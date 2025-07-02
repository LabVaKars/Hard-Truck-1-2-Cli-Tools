import logging
import sys
import os
import struct
import time
import datetime
import enum
import io
# from common import reserve_size_byte, write_size
import parsing.read_b3d as b3dr 
import parsing.skip_b3d as b3ds 
from io import BytesIO
from io import SEEK_CUR

import extract_res
import common as c

# Compiling HardTruck2B3d:
# 1) kaitai-struct-compiler --outdir ./ --no-auto-read --target python ./ksy/hard_truck_2_b3d_parts.ksy
# 2) replace '_pos = self._io.read_bytes(0)' with '_pos = self._io.pos()'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("extract_b3d")
log.setLevel(logging.DEBUG)




class Graph:

    def __init__(self, graph):
        self.graph = graph

    def DFSUtil(self, val, visited):

        visited[val]["in"] += 1
        for v in self.graph[val]:
            if self.graph.get(v) is not None:
                visited[val]["out"] += 1
                self.DFSUtil(v, visited)

    def DFS(self, start=None):
        V = len(self.graph)  #total vertices

        visited = {}
        for val in self.graph.keys():
            visited[val] = {
                "in": 0,
                "out": 0
            }

        searchIn = []
        if start is not None:
            searchIn.append(start.name)
        else:
            searchIn = self.graph.keys()

        for val in searchIn:
            for v in self.graph[val]:
                if self.graph.get(v) is not None:
                    visited[val]["out"] += 1
                    self.DFSUtil(v, visited)

        return visited

def getHierarchyRoots(refObjs):

    graph = {}
    for key in refObjs.keys():
        graph[key] = [cn['add_name'] for cn in refObjs[key]]

    zgraph = Graph(graph)
    visited = zgraph.DFS()
    roots = [cn for cn in visited.keys() if (visited[cn]["in"] == 0) and (visited[cn]["out"] > 0)]

    return roots

def get_name(obj):
    return obj.rstrip('\00')

EMPTY_NAME = ''


def b3dextract(b3dFilename, resFilename, outpath, indlNodes, toSplit, toUseNodeRefs, ref_materials, selected_sections, section_records):

    basename, ext = os.path.splitext(b3dFilename)
    outname = None
    if not toSplit:
        if not outpath:
            outpath_full = '{}_extract.{}'.format(basename, ext[1:])
            outname =  os.path.basename(os.path.splitext(outpath_full)[0])
            outpath = os.path.dirname(outpath_full)
        else:
            outname = os.path.basename(os.path.splitext(outpath)[0])
            outpath = os.path.dirname(outpath)

    else:
        if not outpath:
            outpath = os.path.dirname(b3dFilename)
    
    nodesFromCli = False
    if indlNodes and len(indlNodes) > 0:
        nodesFromCli = True

    #read roots from text file
    blocksToExtract = []

    tt1 = time.mktime(datetime.datetime.now().timetuple())
    #Initial Kaitai Struct parsing
    log.info('initial parsing b3d start')
    b3d_stream = None
    with open(b3dFilename, 'rb') as file:
        b3d_stream = BytesIO(file.read())
    # read header
    b3dr.read_file_header(b3d_stream)
    # read materials
    materials_list = b3dr.read_materials_list(b3d_stream)
    # read start_blocks
    begin_blocks = b3d_stream.read(4)
    data_blocks_offset = b3d_stream.tell()
    # read blocks
    
    parsed_b3d = b3dr.read_roots(b3d_stream, data_blocks_offset)

    all_roots = parsed_b3d['roots']
    blocks18 = parsed_b3d['references']

    # read end_blocks
    # b3d.end_blocks = KaitaiStream.resolve_enum(HardTruck2B3d.Identifiers, b3d._io.read_u4le())
    log.info('initial parsing b3d end')

    if nodesFromCli:
        blocksToExtract = indlNodes
    else:
        blocksToExtract = getHierarchyRoots(blocks18)

    # log.info(blocksToExtract)

    mat_to_idx = {mat['name']:idx for idx, mat in enumerate(materials_list['mat_names'])}
    idx_to_mat = {idx:mat['name'] for idx, mat in enumerate(materials_list['mat_names'])}

    read_from_buffer = None
    with open(b3dFilename, 'rb') as file:
        read_from_buffer = io.BytesIO(file.read())

    outFileData = {}

    # search for referenced blocks
    if (toUseNodeRefs):
        for extBlock in blocksToExtract:

            g_spaces = set()
            g_root_objs = set()
            g_root_objs.add(extBlock)
            curLevel = [extBlock]
            # curLevel.append(extBlock)
            root_objs = set()
            while len(curLevel) > 0:
                for add in curLevel:
                    for block in blocks18[add]:
                        g_spaces.add(block['space_name'])
                        g_root_objs.add(block['add_name'])
                        root_objs.add(block['add_name'])
                curLevel = list(root_objs)
                root_objs = set()

            spaces = [cn for cn in list(g_spaces) if cn != EMPTY_NAME]

            root_objs = list(g_root_objs)

            spaces.sort()
            root_objs.sort(reverse=True)
        
            outFileData[extBlock] = {
                "nodes": root_objs,
                "spaces": spaces
            }
        
    else:
        spaces = []
        for extBlock in blocksToExtract:
            outFileData[extBlock] = {
                "nodes": [extBlock],
                "spaces": []
            }

    current_buffer = io.BytesIO(read_from_buffer.getvalue())

    #Replacing texnum in separate buffer
    if(not toSplit):
        root_objs = set()
        for extFilename, entry in outFileData.items():
            root_objs.update(entry["nodes"])
        root_objs = list(root_objs)
        outFileData = {}
        outFileData[outname] = {
            "nodes": root_objs,
            "spaces": []
        }
        
    for root_name, root in all_roots.items():
        current_buffer.seek(root["start"],0)
        all_roots[root_name]["data"] = BytesIO(current_buffer.read(root["size"]))

    for extFilename, entry in outFileData.items():
        current_buffer = io.BytesIO(read_from_buffer.getvalue())

        current_texnums = set()
        root_objs = entry["nodes"]
        spaces = entry["spaces"]
        for obj in root_objs:
            if all_roots[obj] is not None and len(all_roots[obj]["texnums"]) > 0:
                texnums = [tx["val"] for tx in all_roots[obj]["texnums"]]
                current_texnums.update(texnums)

        #replace with new texture indexes in b3d file
        texnum_list = sorted(list(current_texnums))
        used_materials = sorted([idx_to_mat[idx] for idx in texnum_list])
        new_mat_idx_to_idx = {mat_to_idx[mat]:idx for idx, mat in enumerate(used_materials)}

        # replace texnum indexes
        for obj in root_objs:
            for texnum_obj in all_roots[obj]["texnums"]:
                pos = texnum_obj["pos"]
                texnum = texnum_obj["val"]
                new_texnum = new_mat_idx_to_idx[texnum] + 1 # Material indexes start counting from 1
                current_buffer.seek(pos, 0)
                current_buffer.write(struct.pack("<I", new_texnum))

        outfilename = os.path.join(outpath, '{}.b3d'.format(extFilename))
        
        all_roots_order = sorted(spaces) + sorted(root_objs)

        outBuffer = c.write_output_b3d(all_roots, all_roots_order, used_materials)

        with open(outfilename, 'wb') as outFile:
            outFile.write(outBuffer.getvalue())

        if(resFilename):

            if(ref_materials):   
                section_records["MATERIALS"] = used_materials

            outresfilename = os.path.join(outpath, '{}.res'.format(extFilename))
            extract_res.resextract(resFilename, outresfilename, selected_sections, section_records)



    tt1 = time.mktime(datetime.datetime.now().timetuple()) - tt1

    log.info('Completed in {} seconds'.format(tt1))