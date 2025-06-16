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

# Compiling HardTruck2B3d:
# 1) kaitai-struct-compiler --outdir ./ --no-auto-read --target python ./ksy/hard_truck_2_b3d_parts.ksy
# 2) replace '_pos = self._io.read_bytes(0)' with '_pos = self._io.pos()'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("extract_b3d")
log.setLevel(logging.DEBUG)


def reserve_size_byte(io):
    pos = io.tell()
    io.write(struct.pack("<i",0))
    return pos

def write_size(io, ms, size):
    end_ms = io.tell()
    io.seek(ms, 0)
    io.write(struct.pack("<i", size))
    io.seek(end_ms, 0)

class ChunkType(enum.Enum):
    END_CHUNK = 0
    END_CHUNKS = 1
    BEGIN_CHUNK = 2
    GROUP_CHUNK = 3
    
def openclose(_io):
    oc = _io.read(4)
    # print(oc)
    if (oc == (b'\x4D\x01\x00\x00')): # Begin_Chunk(111)
        return ChunkType.BEGIN_CHUNK
    elif oc == (b'\x2B\x02\x00\x00'): # End_Chunk(555)
        return ChunkType.END_CHUNK
    elif oc == (b'\xbc\x01\x00\x00'): # Group_Chunk(444)
        return ChunkType.GROUP_CHUNK
    elif oc == (b'\xde\x00\x00\x00'): # End_Chunks(222)
        return ChunkType.END_CHUNKS
    else:
        # log.debug(file.tell())
        raise Exception()

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

EMPTY_NAME = '~'


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

    rootObjects = {}
    blocks18 = {}
    rootTexnums = {}
    rootTexnumsPos = {}

    def fill_texnum(obj_name, block_data):
        texnum = block_data['texnum']
        texnum_pos = block_data['texnum_pos']
        rootTexnums[obj_name].add(texnum)
        rootTexnumsPos[obj_name].append(texnum_pos)

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
    b3dr.begin_blocks = b3d_stream.read(4)
    data_blocks_offset = b3d_stream.tell()
    # read blocks
    
    ex = 0
    level = 0

    objName = ''
    rootObjName = ''
    start_pos = data_blocks_offset
    end_pos = 0

    while ex != ChunkType.END_CHUNKS:

        ex = openclose(b3d_stream)
        if ex == ChunkType.END_CHUNK:
            level -= 1
            if level == 0:
                end_pos = b3d_stream.tell()
                rootObjects[objName] = {
                    "start": start_pos,
                    "size": end_pos - start_pos
                }

        elif ex == ChunkType.END_CHUNKS:
            break
        elif ex == ChunkType.GROUP_CHUNK: #skip
            continue
        elif ex == ChunkType.BEGIN_CHUNK:

            if level == 0:
                start_pos = b3d_stream.tell()-4
            
            
            block_name = b3dr.read_name32(b3d_stream)
            block_type, = struct.unpack('<I', b3d_stream.read(4))
            block_data = None

            if level == 0:
                rootTexnums[block_name['name']] = set()
                rootTexnumsPos[block_name['name']] = []
                rootObjName = block_name['name']
                # print(rootObjName)
            
            # Switch based on block_type
            if block_type == 0:
                block_data = b3ds.skip_b_0(b3d_stream)
            elif block_type == 1:
                block_data = b3ds.skip_b_1(b3d_stream)
            elif block_type == 2:
                block_data = b3ds.skip_b_2(b3d_stream)
            elif block_type == 3:
                block_data = b3ds.skip_b_3(b3d_stream)
            elif block_type == 4:
                block_data = b3ds.skip_b_4(b3d_stream)
            elif block_type == 5:
                block_data = b3ds.skip_b_5(b3d_stream)
            elif block_type == 6:
                block_data = b3ds.skip_b_6(b3d_stream)
            elif block_type == 7:
                block_data = b3ds.skip_b_7(b3d_stream)
            elif block_type == 8:
                block_data = b3dr.read_b_8(b3d_stream)
            elif block_type == 9:
                block_data = b3ds.skip_b_9(b3d_stream)
            elif block_type == 10:
                block_data = b3ds.skip_b_10(b3d_stream)
            elif block_type == 11:
                block_data = b3ds.skip_b_11(b3d_stream)
            elif block_type == 12:
                block_data = b3ds.skip_b_12(b3d_stream)
            elif block_type == 13:
                block_data = b3ds.skip_b_13(b3d_stream)
            elif block_type == 14:
                block_data = b3ds.skip_b_14(b3d_stream)
            elif block_type == 15:
                block_data = b3ds.skip_b_15(b3d_stream)
            elif block_type == 16:
                block_data = b3ds.skip_b_16(b3d_stream)
            elif block_type == 17:
                block_data = b3ds.skip_b_17(b3d_stream)
            elif block_type == 18:
                block_data = b3dr.read_b_18(b3d_stream)
            elif block_type == 19:
                block_data = b3ds.skip_b_19(b3d_stream)
            elif block_type == 20:
                block_data = b3ds.skip_b_20(b3d_stream)
            elif block_type == 21:
                block_data = b3ds.skip_b_21(b3d_stream)
            elif block_type == 22:
                block_data = b3ds.skip_b_22(b3d_stream)
            elif block_type == 23:
                block_data = b3ds.skip_b_23(b3d_stream)
            elif block_type == 24:
                block_data = b3ds.skip_b_24(b3d_stream)
            elif block_type == 25:
                block_data = b3ds.skip_b_25(b3d_stream)
            elif block_type == 26:
                block_data = b3ds.skip_b_26(b3d_stream)
            elif block_type == 27:
                block_data = b3ds.skip_b_27(b3d_stream)
            elif block_type == 28:
                block_data = b3dr.read_b_28(b3d_stream)
            elif block_type == 29:
                block_data = b3ds.skip_b_29(b3d_stream)
            elif block_type == 30:
                block_data = b3ds.skip_b_30(b3d_stream)
            elif block_type == 31:
                block_data = b3ds.skip_b_31(b3d_stream)
            elif block_type == 33:
                block_data = b3ds.skip_b_33(b3d_stream)
            elif block_type == 34:
                block_data = b3ds.skip_b_34(b3d_stream)
            elif block_type == 35:
                block_data = b3dr.read_b_35(b3d_stream)
            elif block_type == 36:
                block_data = b3ds.skip_b_36(b3d_stream)
            elif block_type == 37:
                block_data = b3ds.skip_b_37(b3d_stream)
            elif block_type == 39:
                block_data = b3ds.skip_b_39(b3d_stream)
            elif block_type == 40:
                block_data = b3ds.skip_b_40(b3d_stream)

            curObjName = block_name['name']

            if level == 0:
                objName = curObjName
                blocks18[objName] = []
            
            # fill reference list
            if block_type == 18:
                blocks18[objName].append({
                    "space_name" : block_data['space_name']['name'],
                    "add_name" : block_data['add_name']['name'],
                })

            # fill texnum list
            if block_type in [8,28,35]:
                if(block_type == 35):
                    fill_texnum(rootObjName, block_data)
                for poly in block_data['polygons']:
                    fill_texnum(rootObjName, poly)

            level += 1

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

    for extFilename, entry in outFileData.items():
        current_buffer = io.BytesIO(read_from_buffer.getvalue())

        current_texnums = set()
        root_objs = entry["nodes"]
        for obj in root_objs:
            if rootTexnums[obj] is not None and len(rootTexnums[obj]) > 0:
                current_texnums = current_texnums | rootTexnums[obj]

        #replace with new texture indexes in b3d file
        texnum_list = sorted(list(current_texnums))
        used_materials = sorted([idx_to_mat[idx] for idx in texnum_list])
        new_mat_idx_to_idx = {mat_to_idx[mat]:idx for idx, mat in enumerate(used_materials)}


        # replace texnum indexes
        for obj in root_objs:
            if rootTexnumsPos[obj] is not None and len(rootTexnums[obj]) > 0:
                for pos in rootTexnumsPos[obj]:
                    current_buffer.seek(pos, 0)
                    texnum, = struct.unpack("<I", current_buffer.read(4))
                    new_texnum = new_mat_idx_to_idx[texnum] + 1 # Material indexes start counting from 1
                    current_buffer.seek(-4, 1)
                    current_buffer.write(struct.pack("<I", new_texnum))

        outfilename = os.path.join(outpath, '{}.b3d'.format(extFilename))
        write_split_b3d(outfilename, current_buffer, used_materials, rootObjects, spaces, root_objs)

        if(resFilename):

            if(ref_materials):   
                section_records["MATERIALS"] = used_materials

            outresfilename = os.path.join(outpath, '{}.res'.format(extFilename))
            extract_res.resextract(resFilename, outresfilename, selected_sections, section_records)



    tt1 = time.mktime(datetime.datetime.now().timetuple()) - tt1

    log.info('Completed in {} seconds'.format(tt1))

def write_split_b3d(filename, read_from_buffer, materials_list, rootObjects, spaces, objs):
    
    buffer = io.BytesIO()
    buffer.write(b'b3d\x00')
    ms_file_size = reserve_size_byte(buffer)
    ms_materials = reserve_size_byte(buffer)
    ms_materials_size = reserve_size_byte(buffer)
    ms_nodes = reserve_size_byte(buffer)
    ms_nodes_size = reserve_size_byte(buffer)

    cp_materials = int(buffer.tell()/4)

    buffer.write(struct.pack("<i", len(materials_list))) #Material count
    for mat_name in materials_list:
        b3dr.write_name(buffer, mat_name)

    cp_nodes = int(buffer.tell()/4)

    buffer.write(b'\x4D\x01\x00\x00') #BeginChunks
    for space in spaces:
        rootObj = rootObjects[space]
        read_from_buffer.seek(rootObj['start'], 0)
        temp = read_from_buffer.read(rootObj['size'])

        buffer.write(temp)

    for obj in objs:
        rootObj = rootObjects[obj]
        read_from_buffer.seek(rootObj['start'], 0)
        temp = read_from_buffer.read(rootObj['size'])

        buffer.write(temp)

    buffer.write(b'\xde\x00\00\00') #EndChunks
    cp_eof = int(buffer.tell()/4)

    write_size(buffer, ms_file_size, cp_eof)
    write_size(buffer, ms_materials, cp_materials)
    write_size(buffer, ms_materials_size, cp_nodes - cp_materials)
    write_size(buffer, ms_nodes, cp_nodes)
    write_size(buffer, ms_nodes_size, cp_eof - cp_nodes)

    with open(filename, 'wb') as outFile:
        outFile.write(buffer.getvalue())
