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

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("sqlite_utils")
log.setLevel(logging.DEBUG)

b3dBlocks = [
    1,2,3,4,5,6,7,8,9,10,
    11,12,13,14,15,16,17,18,19,20,
    21,22,23,24,25,26,27,28,29,30,
    31,33,34,35,36,37,39,40
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

def getBlockColumnByType(blockType, noTypes = False):
    blockColumns = ""
    if blockType == 1:
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
            tabSphere("bound_sphere"),
            tabSphere("unk_sphere")
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
            poly_cnt INT
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

insertColumns = {}
for blockType in b3dBlocks:
    insertColumns[blockType] = getBlockColumnByType(blockType, True)

def createTableByType(con, blockType):

    cur = con.cursor()

    sqlStatement = """
        CREATE TABLE IF NOT EXISTS b_{}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            b3dmodule VARCHAR(32),
            b3dname VARCHAR(32),
            {}
        )
    """
    blockColumns = getBlockColumnByType(blockType)

    cur.execute(sqlStatement.format(blockType, blockColumns))

def getPlaceholders(cnt):
    if cnt > 0:
        arr = ['?'] * cnt
        return ",".join(arr)
    return ""

def insertByType(con, blockType, row):

    # log.debug("inserting {}".format(blockType))

    cur = con.cursor()

    count = (insertColumns[blockType]).count(",")+1+2

    sqlStatement = """
        INSERT INTO b_{}(b3dmodule, b3dname, {})
        VALUES ({})
    """.format(blockType, insertColumns[blockType], getPlaceholders(count))

    cur.execute(sqlStatement, row)
    con.commit()

def dropDbStruct(con):

    cur = con.cursor()

    for blockType in b3dBlocks:
        cur.execute("""
            DROP TABLE IF EXISTS b_{}
        """.format(blockType))

    con.commit()

def createDbStruct(con):

    for blockType in b3dBlocks:
        createTableByType(con, blockType)

    con.commit()
