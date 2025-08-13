import logging
import struct
import os
import sys
import sqlite3

import parsing.read_b3d as b3dr 
import parsing.skip_b3d as b3ds 
import sqlite_utils as sqlu 
from parsing.read_b3d import ChunkType
from io import BytesIO
from io import SEEK_CUR


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("sqlite_b3d")
log.setLevel(logging.DEBUG)

blocksWithChildren = [2,3,4,5,6,7,9,10,11,19,21,22,24,26,29,33,36,37,39]

def b3dsqlite(b3dFilename, dbFilename, dropDB = False):

    rootObjects = {}
    
    b3dBasename = os.path.basename(b3dFilename)[:-4] #cut extension

    con = sqlite3.connect(dbFilename)

    b3d_stream = None
    with open(b3dFilename, 'rb') as file:
        b3d_stream = BytesIO(file.read())
    # read header
    b3dr.read_file_header(b3d_stream)
    # read materials
    materials_list = [mat["name"] for mat in b3dr.read_materials_list(b3d_stream)["mat_names"]]
    # read start_blocks
    b3dr.begin_blocks = b3d_stream.read(4)
    # read blocks
    
    ex = 0
    level = 0


    if dropDB:
        sqlu.dropDbStruct(con)
    sqlu.createDbStruct(con)
    objName = ''

    nodes = []
    curNode = None
    curObj = curNode

    while ex != ChunkType.END_CHUNKS:

        ex = b3dr.read_chunk_type(b3d_stream)
        if ex == ChunkType.END_CHUNK:
            level -= 1
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
            
            row = [b3dBasename, block_name['name']]

            # Switch based on block_type
            if block_type == 0:
                block_data = b3dr.read_b_0(b3d_stream)
            elif block_type == 1:
                block_data = b3dr.read_b_1(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.extend(b3dr.read_as_array(block_data['name2']))
                sqlu.insertByType(con, block_type, row)
            elif block_type == 2:
                block_data = b3dr.read_b_2(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 3:
                block_data = b3dr.read_b_3(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 4:
                block_data = b3dr.read_b_4(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.extend(b3dr.read_as_array(block_data['name2']))
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 5:
                block_data = b3dr.read_b_5(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 6:
                block_data = b3dr.read_b_6(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.extend(b3dr.read_as_array(block_data['name2']))
                row.append(block_data['vert_count'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 7:
                block_data = b3dr.read_b_7(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['group_name']))
                row.append(block_data['vert_count'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 8:
                block_data = b3dr.read_b_8(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['poly_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 9:
                block_data = b3dr.read_b_9(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 10:
                block_data = b3dr.read_b_10(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 11:
                block_data = b3dr.read_b_11(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['point1'])) 
                row.extend(b3dr.read_as_array(block_data['point2'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 12:
                block_data = b3dr.read_b_12(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 13:
                block_data = b3dr.read_b_13(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 14:
                block_data = b3dr.read_b_14(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 15:
                block_data = b3dr.read_b_15(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 16:
                block_data = b3dr.read_b_16(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['point1'])) 
                row.extend(b3dr.read_as_array(block_data['point2'])) 
                row.append(block_data['unk_f1'])
                row.append(block_data['unk_f2'])
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 17:
                block_data = b3dr.read_b_17(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['point1'])) 
                row.extend(b3dr.read_as_array(block_data['point2'])) 
                row.append(block_data['unk_f1'])
                row.append(block_data['unk_f2'])
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 18:
                block_data = b3dr.read_b_18(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['space_name']))
                row.extend(b3dr.read_as_array(block_data['add_name']))
                sqlu.insertByType(con, block_type, row)
            elif block_type == 19:
                block_data = b3dr.read_b_19(b3d_stream)
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 20:
                block_data = b3dr.read_b_20(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['coords_count'])
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 21:
                block_data = b3dr.read_b_21(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['group_cnt'])
                row.append(block_data['unk_i1'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 22:
                block_data = b3dr.read_b_22(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 23:
                block_data = b3dr.read_b_23(b3d_stream)
                row.append(block_data['unk_i1'])
                row.append(block_data['surface'])
                row.append(block_data['unk_count'])
                row.append(block_data['verts_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 24:
                block_data = b3dr.read_b_24(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['coord1'])) 
                row.extend(b3dr.read_as_array(block_data['coord2'])) 
                row.extend(b3dr.read_as_array(block_data['coord3'])) 
                row.extend(b3dr.read_as_array(block_data['pos'])) 
                row.append(block_data['flag'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 25:
                block_data = b3dr.read_b_25(b3d_stream)
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_i3'])
                row.extend(b3dr.read_as_array(block_data['unk_name']))
                row.extend(b3dr.read_as_array(block_data['point1'])) 
                row.extend(b3dr.read_as_array(block_data['point2'])) 
                row.append(block_data['unkfl1'])
                row.append(block_data['unkfl2'])
                row.append(block_data['unkfl3'])
                row.append(block_data['unkfl4'])
                row.append(block_data['unkfl5'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 26:
                block_data = b3dr.read_b_26(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['unk_p1'])) 
                row.extend(b3dr.read_as_array(block_data['unk_p2'])) 
                row.extend(b3dr.read_as_array(block_data['unk_p3'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 27:
                block_data = b3dr.read_b_27(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['flag'])
                row.extend(b3dr.read_as_array(block_data['unk_p1'])) 
                row.append(block_data['material'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 28:
                block_data = b3dr.read_b_28(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['sprite_center'])) 
                row.append(block_data['poly_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 29:
                block_data = b3dr.read_b_29(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['unk_count'])
                row.append(block_data['unk_i1'])
                row.extend(b3dr.read_as_array(block_data['unk_1'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 30:
                block_data = b3dr.read_b_30(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['room_name']))
                row.extend(b3dr.read_as_array(block_data['point1'])) 
                row.extend(b3dr.read_as_array(block_data['point2'])) 
                sqlu.insertByType(con, block_type, row)
            elif block_type == 31:
                block_data = b3dr.read_b_31(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['unk_count'])
                row.extend(b3dr.read_as_array(block_data['unk1'])) 
                row.append(block_data['int2'])
                row.extend(b3dr.read_as_array(block_data['unk_p2'])) 
                sqlu.insertByType(con, block_type, row)
            elif block_type == 33:
                block_data = b3dr.read_b_33(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['use_lights'])
                row.append(block_data['light_type'])
                row.append(block_data['flag'])
                row.extend(b3dr.read_as_array(block_data['unk_p1'])) 
                row.extend(b3dr.read_as_array(block_data['unk_p2'])) 
                row.append(block_data['unk_f1'])
                row.append(block_data['unk_f2'])
                row.append(block_data['light_radius'])
                row.append(block_data['intensity'])
                row.append(block_data['unk_f3'])
                row.append(block_data['unk_f4'])
                row.extend(b3dr.read_as_array(block_data['rgb'])) 
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 34:
                block_data = b3dr.read_b_34(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 35:
                block_data = b3dr.read_b_35(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['mtype'])
                row.append(block_data['texnum'])
                row.append(block_data['poly_count'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 36:
                block_data = b3dr.read_b_36(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.extend(b3dr.read_as_array(block_data['name2']))
                row.append(block_data['format_raw'])
                row.append(block_data['vert_count'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 37:
                block_data = b3dr.read_b_37(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['group_name']))
                row.append(block_data['format_raw'])
                row.append(block_data['vert_count'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 39:
                block_data = b3dr.read_b_39(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.append(block_data['color_r'])
                row.append(block_data['unk_f1'])
                row.append(block_data['fog_start'])
                row.append(block_data['fog_end'])
                row.append(block_data['color_id'])
                row.append(block_data['child_cnt'])
                sqlu.insertByType(con, block_type, row)
            elif block_type == 40:
                block_data = b3dr.read_b_40(b3d_stream)
                row.extend(b3dr.read_as_array(block_data['bound1'])) 
                row.extend(b3dr.read_as_array(block_data['name1']))
                row.extend(b3dr.read_as_array(block_data['name2']))
                row.append(block_data['unk_i1'])
                row.append(block_data['unk_i2'])
                row.append(block_data['unk_count'])
                sqlu.insertByType(con, block_type, row)
