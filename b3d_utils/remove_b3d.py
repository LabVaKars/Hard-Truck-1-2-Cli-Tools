import logging
import sys
import os
import fnmatch
import struct
from io import BytesIO

import parsing.read_b3d as b3dr
import common as c

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("remove_b3d")
log.setLevel(logging.DEBUG)

def b3dremove(b3dFilepath, outFilepath, remMaterials, remNodes):
    b3d_read_stream = None
    with open(b3dFilepath, 'rb') as file:
        b3d_read_stream = BytesIO(file.read())

        
    if not outFilepath:
        outFilepath = b3dFilepath

    b3dr.read_file_header(b3d_read_stream)
    materials_list = [mat["name"] for mat in b3dr.read_materials_list(b3d_read_stream)["mat_names"]]
    b3d_read_stream.read(4) # BEGIN_BLOCKS
    data_blocks_off = b3d_read_stream.tell()
    
    parsed_b3d = b3dr.read_roots(b3d_read_stream, data_blocks_off)

    # Read root data
    
    all_roots = parsed_b3d['roots']
    for root_name, root in all_roots.items():
        b3d_read_stream.seek(root["start"],0)
        all_roots[root_name]["data"] = BytesIO(b3d_read_stream.read(root["size"]))

    matching_names = [f 
        for f in all_roots.keys() #all imported names
        if any(fnmatch.fnmatch(f, pattern) 
            for pattern in remNodes) #user defined wildcards or just names
    ]

    all_roots = {key:value for key, value in all_roots.items() if key not in matching_names}
    all_roots_order = sorted(all_roots.keys())

    outBuffer = c.write_output_b3d(all_roots, all_roots_order, materials_list)

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())