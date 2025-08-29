import logging
import struct
import os
import sys
import sqlite3

import parsing.read_way as wayr 
import parsing.read_b3d as b3dr 
import sqlite_utils as sqlu 
from parsing.read_b3d import ChunkType
from io import BytesIO
from io import SEEK_CUR


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("sqlite_way")
log.setLevel(logging.DEBUG)

def openclose(file, path):
    if file.tell() == os.path.getsize(path):
        log.debug ('EOF')
        return 1
    else:
        return 2

def waysqlite(wayFilename, dbFilename, dropDB = False):

    rootObjects = {}
    
    wayBasename = os.path.basename(wayFilename)[:-4] #cut extension
    
    con = sqlite3.connect(dbFilename)

    b3d_stream = None
    with open(wayFilename, 'rb') as file:
        b3d_stream = BytesIO(file.read())

    if dropDB:
        sqlu.dropDbStruct(con)
    sqlu.createDbStruct(con)

    wayr.read_header(b3d_stream)

    # read blocks
    objName = ''
    eof = os.path.getsize(wayFilename)

    room_name = None
    while b3d_stream.tell() != eof:

        block = wayr.read_block(b3d_stream)

        if block["room_name"] is not None:
            room_name = block["room_name"]
            continue

        block_type = block["block_type"]
        block_data = block["block_data"]
            
        row = [room_name]
        
            # Switch based on block_type
        if block_type == "RSEG":
            row.append(block_data["attr1"])
            row.append(block_data["attr2"])
            row.append(block_data["attr3"])
            row.append(block_data["width1"])
            row.append(block_data["width2"])
            row.append(block_data["unk_name"])
            row.append(block_data["point_cnt"])
        elif block_type == "RNOD":
            row.append(block_data["name"])
            row.append(1 if block_data["oriented"] else 0)
            row.extend(block_data['pos'])
            row.append(block_data["flag"])
        
        new_id = sqlu.insertWayByType(con, block_type, row)
        
    con.commit()
    con.close()
