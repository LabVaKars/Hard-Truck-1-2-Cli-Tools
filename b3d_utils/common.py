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