import logging
import sys
import os
import fnmatch
import struct
from io import BytesIO

import parsing.read_b3d as b3dr
import common as c

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("merge_b3d")
log.setLevel(logging.DEBUG)


def b3dmerge(b3dFromFilepath, b3dToFilepath, outFilepath, toReplace):

    b3d_from_read_stream = None
    with open(b3dFromFilepath, 'rb') as file:
        b3d_from_read_stream = BytesIO(file.read())

    b3d_into_read_stream = None
    with open(b3dToFilepath, 'rb') as file:
        b3d_into_read_stream = BytesIO(file.read())
        
    if not outFilepath:
        outFilepath = b3dToFilepath

    b3dr.read_file_header(b3d_from_read_stream)
    materials_list_from = [mat["name"] for mat in b3dr.read_materials_list(b3d_from_read_stream)["mat_names"]]
    b3d_from_read_stream.read(4) # BEGIN_BLOCKS
    data_blocks_off_from = b3d_from_read_stream.tell()
    
    parsed_from_b3d = b3dr.read_roots(b3d_from_read_stream, data_blocks_off_from)

    b3dr.read_file_header(b3d_into_read_stream)
    materials_list_into = [mat["name"] for mat in b3dr.read_materials_list(b3d_into_read_stream)["mat_names"]]
    b3d_into_read_stream.read(4) # BEGIN_BLOCKS
    data_blocks_off_into = b3d_into_read_stream.tell()
    
    parsed_into_b3d = b3dr.read_roots(b3d_into_read_stream, data_blocks_off_into)

    # Read root data
    
    roots_from = parsed_from_b3d['roots']
    for root_name, root in roots_from.items():
        b3d_from_read_stream.seek(root["start"],0)
        roots_from[root_name]["data"] = BytesIO(b3d_from_read_stream.read(root["size"]))

    roots_into = parsed_into_b3d['roots']
    for root_name, root in roots_into.items():
        b3d_into_read_stream.seek(root["start"],0)
        roots_into[root_name]["data"] = BytesIO(b3d_into_read_stream.read(root["size"]))

    all_materials_order = sorted(list(set(materials_list_into + materials_list_from)))
    
    from_og_mat_indexes = {f:i for i, f in enumerate(materials_list_from)}
    into_og_mat_indexes = {f:i for i, f in enumerate(materials_list_into)}
            
    # Merging materials into one array
    new_mat_indexes = {f:(i+1) for i, f in enumerate(all_materials_order)}
    from_mat_index_mapping = {from_og_mat_indexes[k]: new_mat_indexes[k] for k in from_og_mat_indexes if k in new_mat_indexes}
    into_mat_index_mapping = {into_og_mat_indexes[k]: new_mat_indexes[k] for k in into_og_mat_indexes if k in new_mat_indexes}

    all_roots = {}
    all_roots_order = []

    for root_name, root in roots_into.items():
        all_roots[root_name] = root
        all_roots[root_name]['is_from'] = False
    
    if toReplace:
        for root_name, root in roots_from.items():
            all_roots[root_name] = root
            all_roots[root_name]['is_from'] = True
    else:
        for root_name, root in roots_from.items():
            if all_roots.get(root_name) is not None:
                all_roots[root_name] = root
                all_roots[root_name]['is_from'] = True

    all_roots_order = sorted(all_roots.keys())

    for root_name, root in all_roots.items():
        for i, tx in enumerate(root["texnums"]):
            if root["is_from"]:
                tx['val'] = from_mat_index_mapping[tx['val']-1]
            else:
                tx['val'] = into_mat_index_mapping[tx['val']-1]
            root["data"].seek(tx["pos"], 0)
            root["data"].write(struct.pack("<I", tx["val"]))

    outBuffer = BytesIO()
    
    outBuffer.write(b'b3d\x00')
    ms_file_size = c.reserve_size_byte(outBuffer)
    ms_materials = c.reserve_size_byte(outBuffer)
    ms_materials_size = c.reserve_size_byte(outBuffer)
    ms_nodes = c.reserve_size_byte(outBuffer)
    ms_nodes_size = c.reserve_size_byte(outBuffer)

    cp_materials = int(outBuffer.tell()/4)

    outBuffer.write(struct.pack("<i", len(all_materials_order))) #Material count
    for mat_name in all_materials_order:
        b3dr.write_name(outBuffer, mat_name)
        
    cp_nodes = int(outBuffer.tell()/4)
    
    outBuffer.write(b'\x4D\x01\x00\x00') #BeginChunks
    
    for root_name in all_roots_order:
        root = all_roots[root_name]
        temp = root["data"].getvalue()
        outBuffer.write(temp)

    outBuffer.write(b'\xde\x00\00\00') #EndChunks

    cp_eof = int(outBuffer.tell()/4)

    c.write_size(outBuffer, ms_file_size, cp_eof)
    c.write_size(outBuffer, ms_materials, cp_materials)
    c.write_size(outBuffer, ms_materials_size, cp_nodes - cp_materials)
    c.write_size(outBuffer, ms_nodes, cp_nodes)
    c.write_size(outBuffer, ms_nodes_size, cp_eof - cp_nodes)

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())
