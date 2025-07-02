import struct
from io import BytesIO

import parsing.read_b3d as b3dr

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

SECTIONS = ["PALETTEFILES", "SOUNDFILES", "BACKFILES", "MASKFILES", "TEXTUREFILES", "COLORS", "MATERIALS", "SOUNDS"]

def get_res_params(
    sections, 
    inc_soundfiles, ref_soundfiles, 
    inc_backfiles,
    inc_maskfiles, ref_maskfiles, 
    inc_texturefiles, ref_texturefiles, 
    inc_materials,
    inc_sounds
):
    current_sections = None
    if(sections):
        current_sections = sections
    else:
        current_sections = SECTIONS

    section_records = {
        "SOUNDFILES": "REF" if ref_soundfiles else inc_soundfiles,
        "BACKFILES": inc_backfiles,
        "MASKFILES": "REF" if ref_maskfiles else inc_maskfiles,
        "TEXTUREFILES": "REF" if ref_texturefiles else inc_texturefiles,
        "MATERIALS": inc_materials,
        "SOUNDS": inc_sounds,
        "PALETTEFILES": None
    }

    return {
        "current_sections": current_sections,
        "section_records": section_records
    }


def write_cstring(stream, txt):
    if txt[-1] != "\00":
        txt += "\00"
    stream.write(txt.encode("utf8"))

    
def reserve_size_byte(io):
    pos = io.tell()
    io.write(struct.pack("<i",0))
    return pos

def write_size(io, ms, size):
    end_ms = io.tell()
    io.seek(ms, 0)
    io.write(struct.pack("<i", size))
    io.seek(end_ms, 0)

    
def write_output_b3d(all_roots, all_roots_order, material_list):
    outBuffer = BytesIO()
    
    outBuffer.write(b'b3d\x00')
    ms_file_size = reserve_size_byte(outBuffer)
    ms_materials = reserve_size_byte(outBuffer)
    ms_materials_size = reserve_size_byte(outBuffer)
    ms_nodes = reserve_size_byte(outBuffer)
    ms_nodes_size = reserve_size_byte(outBuffer)

    cp_materials = int(outBuffer.tell()/4)

    outBuffer.write(struct.pack("<i", len(material_list))) #Material count
    for mat_name in material_list:
        b3dr.write_name(outBuffer, mat_name)
        
    cp_nodes = int(outBuffer.tell()/4)
    
    outBuffer.write(b'\x4D\x01\x00\x00') #BeginChunks
    
    for root_name in all_roots_order:
        root = all_roots[root_name]
        temp = root["data"].getvalue()
        outBuffer.write(temp)

    outBuffer.write(b'\xde\x00\00\00') #EndChunks

    cp_eof = int(outBuffer.tell()/4)

    write_size(outBuffer, ms_file_size, cp_eof)
    write_size(outBuffer, ms_materials, cp_materials)
    write_size(outBuffer, ms_materials_size, cp_nodes - cp_materials)
    write_size(outBuffer, ms_nodes, cp_nodes)
    write_size(outBuffer, ms_nodes_size, cp_eof - cp_nodes)

    return outBuffer