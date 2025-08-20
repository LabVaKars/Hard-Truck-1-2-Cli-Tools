import sqlite3
import struct
import logging
import sys
import os
import enum

filename = ''
outdir = ''

reloadTables = False

args = sys.argv

import parsing.read_b3d as rb3d


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("sqlite_utils")
log.setLevel(logging.DEBUG)

b3dBlocks = [
    0,1,2,3,4,5,6,7,8,9,10,
    11,12,13,14,15,16,17,18,19,20,
    21,22,23,24,25,26,27,28,29,30,
    31,33,34,35,36,37,39,40
]

b3dSubBlocks = [
    rb3d.B40.TREE, rb3d.B40.DYNGLOW, rb3d.B40.PEOPLE, rb3d.B40.SPARKLES,
    rb3d.B13.T10, rb3d.B13.T11, rb3d.B13.T16, rb3d.B13.T23,
    rb3d.B13.T24, rb3d.B13.T29, rb3d.B13.T30, rb3d.B13.T31, rb3d.B13.T4095,
    rb3d.B20.T0, rb3d.B20.T3, rb3d.B20.T5, rb3d.B20.T6
]

def readName(file):
    objName = file.read(32)
    if (objName[0] == 0):
        objName = ''
        #objname = "Untitled_0x" + str(hex(pos-36))
    else:
        objName = (objName.decode("cp1251").rstrip('\0'))
    return objName

def tabSphere(name, isInt = False):
    ctype = "INT" if isInt else "FLOAT"
    return """
        {name}_x {ctype},
        {name}_y {ctype},
        {name}_z {ctype},
        {name}_r {ctype}""".format(name=name, ctype=ctype)

def tabPoint(name, isInt = False):
    ctype = "INT" if isInt else "FLOAT"
    return """
        {name}_x {ctype},
        {name}_y {ctype},
        {name}_z {ctype}""".format(name=name, ctype=ctype)

def tabUV(name, isInt = False):
    ctype = "INT" if isInt else "FLOAT"
    return """
        {name}_u {ctype},
        {name}_v {ctype}""".format(name=name, ctype=ctype)

def getBlockColumnBySubType(blockType, subType, noTypes = False):
    blockColumns = ""
    
    if blockType == 20:
        if subType == rb3d.B20.T0:
            blockColumns = """
                unk_f1 FLOAT,
                unk_sh1 INT,
                unk_sh2 INT
            """
        elif subType == rb3d.B20.T3:
            blockColumns = """
                unk_f1 FLOAT,
                unk_sh1 INT,
                unk_sh2 INT,
                unk_sh3 INT
            """
        elif subType == rb3d.B20.T5:
            blockColumns = """
                unk_f1 FLOAT,
                unk_sh1 INT,
                unk_sh2 INT,
                unk_i1 INT
            """
        elif subType == rb3d.B20.T6:
            blockColumns = """
                unk_f1 FLOAT,
                unk_sh1 INT,
                unk_sh2 INT,
                name1 VARCHAR(32),
                name2 VARCHAR(32)
            """

    if blockType == 13:
        if subType == rb3d.B13.T10 \
        or subType == rb3d.B13.T11 \
        or subType == rb3d.B13.T24:
            blockColumns = """
                {},
                {},
                {},
                {},
                {},
                {},
                room_name VARCHAR(32)
            """.format(
                tabPoint("p1"),
                tabPoint("rot1"),
                tabPoint("p2"),
                tabPoint("rot2"),
                tabPoint("p3"),
                tabPoint("rot3")
            )

        elif subType == rb3d.B13.T4095:
            blockColumns = """
                module_name VARCHAR(32)
            """

        elif subType == rb3d.B13.T31:
            blockColumns = """
                {},
                {},
                unk_f1 FLOAT
            """.format(
                tabPoint('p1'),
                tabPoint('p2')
            )

        elif subType == rb3d.B13.T30:
            blockColumns = """
                speed FLOAT,
                {}
            """.format(
                tabPoint('rot')
            )

        elif subType == rb3d.B13.T29:
            blockColumns = """
                {},
                rad FLOAT
            """.format(
                tabPoint('rot')
            )

        elif subType == rb3d.B13.T23:
            blockColumns = """
                {},
                rad FLOAT
            """.format(
                tabPoint('rot')
            )

        elif subType == rb3d.B13.T16:
            blockColumns = """
                water_height FLOAT
            """
    
    if blockType == 40:
        if subType == rb3d.B40.TREE:
            blockColumns = """
            mat_index1 INT,
            mat_index2 INT,
            {},
            {}
            """.format(
                tabSphere("bound_sphere"),
                tabSphere("unk_sphere")
            )

        elif subType == rb3d.B40.DYNGLOW:
            blockColumns = """
            unk_f1 FLOAT,
            unk_f2 FLOAT,
            unk_f3 FLOAT,
            unk_f4 FLOAT,
            unk_f5 FLOAT,
            unk_f6 FLOAT,
            mat_name VARCHAR(32),
            res_index INT,
            unk_f11 FLOAT,
            unk_f12 FLOAT
            """

        elif subType == rb3d.B40.PEOPLE:
            blockColumns = """
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            people_id INT,
            mat_index INT
            """.format(
                tabPoint("p1"),
                tabUV("uv1"),
                tabPoint("p2"),
                tabUV("uv2"),
                tabPoint("p3"),
                tabUV("uv3"),
                tabPoint("p4"),
                tabUV("uv4")
            )

        elif subType == rb3d.B40.SPARKLES:
            blockColumns = """
                {},
                {}
            """.format(
                tabPoint("pos"),
                tabPoint("rot")
            )
            
            
    if noTypes:
        blockColumns = blockColumns.replace(" INT", "")
        blockColumns = blockColumns.replace(" FLOAT", "")
        blockColumns = blockColumns.replace(" VARCHAR(32)", "")

    return blockColumns

def getBlockColumnByType(blockType, noTypes = False):
    blockColumns = ""
    if blockType == 0:
        blockColumns = ""
    elif blockType == 1:
        blockColumns = """
            name1 VARCHAR(32),
            name2 VARCHAR(32)
        """
    elif blockType == 2:
        blockColumns = """
            {},
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere")
        )
    elif blockType == 3:
        blockColumns = """
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 4:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            name2 VARCHAR(32),
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 5:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 6:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            name2 VARCHAR(32),
            vertex_cnt INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 7:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            vertex_cnt INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 8:
        blockColumns = """
            {},
            poly_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType in [9,10,22]:
        blockColumns = """
            {},
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere")
        )
    elif blockType == 11:
        blockColumns = """
            {},
            {},
            {},
            float1 FLOAT,
            float2 FLOAT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("unk_point1"),
            tabPoint("unk_point2")
        )
    elif blockType in [12, 14]:
        blockColumns = """
            {},
            {},
            int1 INT,
            int2 INT,
            unk_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere")
        )
    elif blockType in [13, 15]:
        blockColumns = """
            {},
            int1 INT,
            int2 INT,
            unk_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType in [16, 17]:
        blockColumns = """
            {},
            {},
            {},
            float1 FLOAT,
            float2 FLOAT,
            int1 INT,
            int2 INT,
            poly_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("point1"),
            tabPoint("point2"),
        )
    elif blockType == 18:
        blockColumns = """
            {},
            space_name VARCHAR(32),
            add_name VARCHAR(32)
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 19:
        blockColumns = """
            child_cnt INT
        """
    elif blockType == 20:
        blockColumns = """
            {},
            vertex_cnt INT,
            int1 INT,
            int2 INT,
            unk_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 21:
        blockColumns = """
            {},
            int1 INT,
            int2 INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 23:
        blockColumns = """
            int1 INT,
            surface INT,
            unk_cnt INT,
            poly_cnt INT,
            extra_f1 FLOAT,
            extra_f2 FLOAT,
            extra_f3 FLOAT
        """
    elif blockType == 24:
        blockColumns = """
            {},
            {},
            {},
            {},
            flag INT,
            child_cnt INT
        """.format(
            tabPoint("transf1"),
            tabPoint("transf2"),
            tabPoint("transf3"),
            tabPoint("pos")
        )
    elif blockType == 25:
        blockColumns = """
            unk1 INT,
            unk2 INT,
            unk3 INT,
            name1 VARCHAR(32),
            {},
            {},
            float1 FLOAT,
            float2 FLOAT,
            float3 FLOAT,
            float4 FLOAT,
            float5 FLOAT
        """.format(
            tabPoint("point1"),
            tabPoint("point2")
        )
    elif blockType == 26:
        blockColumns = """
            {},
            {},
            {},
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("point1"),
            tabSphere("point2"),
            tabSphere("point3")
        )
    elif blockType == 27:
        blockColumns = """
            {},
            flag1 INT,
            {},
            material INT
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("unk_point"),
        )
    elif blockType == 28:
        blockColumns = """
            {},
            {},
            vertex_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("sprite_center"),
        )
    elif blockType == 29:
        blockColumns = """
            {},
            unk_cnt INT,
            int2 INT,
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere"),
        )
    elif blockType == 30:
        blockColumns = """
            {},
            room_name VARCHAR(32),
            {},
            {}
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("point1"),
            tabPoint("point2"),
        )
    elif blockType == 31:
        blockColumns = """
            {},
            unk_cnt INT,
            {},
            int1 INT,
            {}
        """.format(
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere"),
            tabPoint("unk_point"),
        )
    elif blockType == 33:
        blockColumns = """
            {},
            use_lights INT,
            light_type INT,
            flag1 INT,
            {},
            {},
            float1 FLOAT,
            float2 FLOAT,
            light_r FLOAT,
            intensity FLOAT,
            float3 FLOAT,
            float4 FLOAT,
            {},
            child_cnt INT
        """.format(
            tabSphere("bound_sphere"),
            tabPoint("unk_sphere1"),
            tabPoint("unk_sphere2"),
            tabPoint("rgb"),
        )
    elif blockType == 34:
        blockColumns = """
            {},
            int1 INT,
            unk_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 35:
        blockColumns = """
            {},
            mtype INT,
            texnum INT,
            poly_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 36:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            name2 VARCHAR(32),
            format INT,
            vertex_cnt INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 37:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            format INT,
            vertex_cnt INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 39:
        blockColumns = """
            {},
            color_r INT,
            float1 FLOAT,
            fog_start FLOAT,
            fog_end FLOAT,
            color_id INT,
            child_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )
    elif blockType == 40:
        blockColumns = """
            {},
            name1 VARCHAR(32),
            name2 VARCHAR(32),
            int1 INT,
            int2 INT,
            unk_cnt INT
        """.format(
            tabSphere("bound_sphere")
        )

    if noTypes:
        blockColumns = blockColumns.replace(" INT", "")
        blockColumns = blockColumns.replace(" FLOAT", "")
        blockColumns = blockColumns.replace(" VARCHAR(32)", "")

    return blockColumns

insertSubTypeColumns = {}
for blockEnum in b3dSubBlocks:
    blockType = int(blockEnum.__class__.__name__[1:])
    subType = blockEnum
    insertSubTypeColumns[blockEnum] = getBlockColumnBySubType(blockType, subType, True)

insertTypeColumns = {}
for blockType in b3dBlocks:
    insertTypeColumns[blockType] = getBlockColumnByType(blockType, True)

def createTableBySubType(con, blockType, subType):
    
    cur = con.cursor()

    sqlStatement = """
        CREATE TABLE IF NOT EXISTS b_{}_{}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER
            {}
        )
    """
    
    blockColumns = getBlockColumnBySubType(blockType, subType)

    if blockType != 0:
        blockColumns = ","+blockColumns
    sqlStatement = sqlStatement.format(blockType, subType.value, blockColumns)

    cur.execute(sqlStatement)


def createTableByType(con, blockType):

    cur = con.cursor()

    sqlStatement = """
        CREATE TABLE IF NOT EXISTS b_{}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            b3dmodule VARCHAR(32),
            b3dname VARCHAR(32),
            parent_id INTEGER,
            parent_type INTEGER
            {}
        )
    """
    blockColumns = getBlockColumnByType(blockType)

    if blockType != 0:
        blockColumns = ","+blockColumns
    sqlStatement = sqlStatement.format(blockType, blockColumns)

    cur.execute(sqlStatement)

def getPlaceholders(cnt):
    if cnt > 0:
        arr = ['?'] * cnt
        return ",".join(arr)
    return ""

def insertBySubType(con, blockType, subType, row):
    
    cur = con.cursor()
    count = (insertSubTypeColumns[subType]).count(",")+1+1
    
    blockColumns = insertSubTypeColumns[subType]
    if blockType != 0:
        blockColumns = ","+blockColumns

    sqlStatement = """
        INSERT INTO b_{}_{}(block_id {})
        VALUES ({})
    """.format(blockType, subType.value, blockColumns, getPlaceholders(count))
    
    if (len(row) < count):
        row.extend([None] * (len(row) - count))
    
    # print(sqlStatement)

    cur.execute(sqlStatement, row)
    id = cur.lastrowid
    # con.commit()
    return id

def insertByType(con, blockType, row):

    # log.debug("inserting {}".format(blockType))

    cur = con.cursor()
    count = (insertTypeColumns[blockType]).count(",")+1+4
    if blockType == 0:
        count-=1
    
    blockColumns = insertTypeColumns[blockType]
    if blockType != 0:
        blockColumns = ","+blockColumns

    sqlStatement = """
        INSERT INTO b_{}(b3dmodule, b3dname, parent_id, parent_type {})
        VALUES ({})
    """.format(blockType, blockColumns, getPlaceholders(count))
    
    if (len(row) < count):
        row.extend([None] * (len(row) - count))

    cur.execute(sqlStatement, row)
    id = cur.lastrowid
    # con.commit()
    return id

def dropDbStruct(con):

    cur = con.cursor()

    for blockType in b3dBlocks:
        sqlStatement = """
            DROP TABLE IF EXISTS b_{}
        """.format(blockType)
        cur.execute(sqlStatement)

    for blockEnum in b3dSubBlocks:
        blockType = int(blockEnum.__class__.__name__[1:])
        subType = blockEnum.value
        sqlStatement = """
            DROP TABLE IF EXISTS b_{}_{}
        """.format(blockType, subType)
        cur.execute(sqlStatement)

    con.commit()

def createDbStruct(con):

    for blockType in b3dBlocks:
        createTableByType(con, blockType)
    
    for blockEnum in b3dSubBlocks:
        blockType = int(blockEnum.__class__.__name__[1:])
        subType = blockEnum
        createTableBySubType(con, blockType, subType)

    con.commit()
