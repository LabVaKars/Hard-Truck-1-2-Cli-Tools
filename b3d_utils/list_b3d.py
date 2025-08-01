import logging
import sys
import os
import struct
import time
import datetime
import enum
import io
import json
# from common import reserve_size_byte, write_size
import parsing.read_b3d as b3dr 
import parsing.skip_b3d as b3ds 
from parsing.read_b3d import ChunkType
from io import BytesIO
from io import SEEK_CUR


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("list_b3d")
log.setLevel(logging.DEBUG)

blocksWithChildren = [2,3,4,5,6,7,9,10,11,19,21,22,24,26,29,33,36,37,39]

def b3dlist(b3dFilename, listType, outFilename):

    rootObjects = {}
    blocks18 = {}

    b3d_stream = None
    with open(b3dFilename, 'rb') as file:
        b3d_stream = BytesIO(file.read())
    # read header
    b3dr.read_file_header(b3d_stream)
    # read materials
    materials_list = [mat["name"] for mat in b3dr.read_materials_list(b3d_stream)["mat_names"]]
    # read start_blocks
    b3dr.begin_blocks = b3d_stream.read(4)
    data_blocks_offset = b3d_stream.tell()
    # read blocks
    
    ex = 0
    level = 0

    objName = ''
    start_pos = data_blocks_offset
    end_pos = 0

    chidren_arrays = []

    nodes = []
    curNode = None
    curObj = curNode
    chidren_arrays.append(nodes)

    while ex != ChunkType.END_CHUNKS:

        ex = b3dr.read_chunk_type(b3d_stream)
        if ex == ChunkType.END_CHUNK:
            level -= 1
            if level+1 < len(chidren_arrays):
                chidren_arrays.pop()
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

                # if curNode is not None:
                #     nodes.append(curNode)
            
            block_name = b3dr.read_name32(b3d_stream)
            block_type, = struct.unpack('<I', b3d_stream.read(4))
            block_data = None

            if level == 0:
                rootObjName = block_name['name']
            
            # Switch based on block_type
            if block_type == 0:
                block_data = b3dr.read_b_0(b3d_stream)
            elif block_type == 1:
                block_data = b3dr.read_b_1(b3d_stream)
            elif block_type == 2:
                block_data = b3dr.read_b_2(b3d_stream)
            elif block_type == 3:
                block_data = b3dr.read_b_3(b3d_stream)
            elif block_type == 4:
                block_data = b3dr.read_b_4(b3d_stream)
            elif block_type == 5:
                block_data = b3dr.read_b_5(b3d_stream)
            elif block_type == 6:
                block_data = b3dr.read_b_6(b3d_stream)
            elif block_type == 7:
                block_data = b3dr.read_b_7(b3d_stream)
            elif block_type == 8:
                block_data = b3dr.read_b_8(b3d_stream)
            elif block_type == 9:
                block_data = b3dr.read_b_9(b3d_stream)
            elif block_type == 10:
                block_data = b3dr.read_b_10(b3d_stream)
            elif block_type == 11:
                block_data = b3dr.read_b_11(b3d_stream)
            elif block_type == 12:
                block_data = b3dr.read_b_12(b3d_stream)
            elif block_type == 13:
                block_data = b3dr.read_b_13(b3d_stream)
            elif block_type == 14:
                block_data = b3dr.read_b_14(b3d_stream)
            elif block_type == 15:
                block_data = b3dr.read_b_15(b3d_stream)
            elif block_type == 16:
                block_data = b3dr.read_b_16(b3d_stream)
            elif block_type == 17:
                block_data = b3dr.read_b_17(b3d_stream)
            elif block_type == 18:
                block_data = b3dr.read_b_18(b3d_stream)
            elif block_type == 19:
                block_data = b3dr.read_b_19(b3d_stream)
            elif block_type == 20:
                block_data = b3dr.read_b_20(b3d_stream)
            elif block_type == 21:
                block_data = b3dr.read_b_21(b3d_stream)
            elif block_type == 22:
                block_data = b3dr.read_b_22(b3d_stream)
            elif block_type == 23:
                block_data = b3dr.read_b_23(b3d_stream)
            elif block_type == 24:
                block_data = b3dr.read_b_24(b3d_stream)
            elif block_type == 25:
                block_data = b3dr.read_b_25(b3d_stream)
            elif block_type == 26:
                block_data = b3dr.read_b_26(b3d_stream)
            elif block_type == 27:
                block_data = b3dr.read_b_27(b3d_stream)
            elif block_type == 28:
                block_data = b3dr.read_b_28(b3d_stream)
            elif block_type == 29:
                block_data = b3dr.read_b_29(b3d_stream)
            elif block_type == 30:
                block_data = b3dr.read_b_30(b3d_stream)
            elif block_type == 31:
                block_data = b3dr.read_b_31(b3d_stream)
            elif block_type == 33:
                block_data = b3dr.read_b_33(b3d_stream)
            elif block_type == 34:
                block_data = b3dr.read_b_34(b3d_stream)
            elif block_type == 35:
                block_data = b3dr.read_b_35(b3d_stream)
            elif block_type == 36:
                block_data = b3dr.read_b_36(b3d_stream)
            elif block_type == 37:
                block_data = b3dr.read_b_37(b3d_stream)
            elif block_type == 39:
                block_data = b3dr.read_b_39(b3d_stream)
            elif block_type == 40:
                block_data = b3dr.read_b_40(b3d_stream)

            curObjName = block_name['name']
            
            
            if block_data.get('child_cnt') is not None and block_data.get('child_cnt') > 0:
                block_data['children'] = []
                chidren_arrays.append(block_data['children'])

            block_data['bname'] = block_name['name']
            block_data['btype'] = block_type
            
            chidren_arrays[level].append(block_data)

            if level == 0:
                objName = curObjName
                blocks18[objName] = []
            
            # fill reference list
            if block_type == 18:
                blocks18[objName].append({
                    "space_name" : block_data['space_name']['name'],
                    "add_name" : block_data['add_name']['name'],
                })

            level += 1

    output = ''
    if listType == 'MATERIALS':
        mat_list = ",\n".join(sorted(materials_list))
        output = mat_list
        # print(materials_list)
    elif listType == 'ROOTS':
        roots = sorted([n['bname'] for n in chidren_arrays[0]])
        roots = ',\n'.join(roots)
        # print(',\n'.join(roots))
        output = roots
    elif listType == 'FULL':
        # print(nodes)
        # nodes = []
        # print(json.dumps(chidren_arrays[0]))
        output = json.dumps(chidren_arrays)
    
    if outFilename is not None:
        with open(outFilename, 'wb') as outFile:
            outFile.write(output.encode('utf-8'))
    else:
        print(output)

    # tt1 = time.mktime(datetime.datetime.now().timetuple()) - tt1
