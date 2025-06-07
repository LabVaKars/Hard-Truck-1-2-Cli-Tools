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

