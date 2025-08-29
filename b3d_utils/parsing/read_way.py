import struct

def read_block_type(file):
    return file.read(4).decode("cp1251").rstrip('\0')

def read_name(file, text_len):
    # text_len = 0
    str_len = 0
    fill_len = 0
    if text_len % 4:
        fill_len = ((text_len >> 2) + 1) * 4 - text_len

    string = file.read(text_len).decode("cp1251").rstrip('\0')
    if fill_len > 0:
        file.seek(fill_len, 1)
    return string


def read_header(stream):
    reading_header = True
    module_name = None
    while True:
        subtype = read_block_type(stream)

        if subtype == "WTWR":
            subtype_size = struct.unpack("<i",stream.read(4))[0]

        elif subtype == "MNAM":
            subtype_size = struct.unpack("<i",stream.read(4))[0]
            module_name = read_name(stream, subtype_size)

        elif subtype == "GDAT":
            subtype_size = struct.unpack("<i",stream.read(4))[0]
        else:
            stream.seek(-4, 1)
            break

    return {
        "module_name": module_name
    }

def read_room(stream):
    grom_size = struct.unpack("<i",stream.read(4))[0]
    subtype = read_block_type(stream)
    room_name = None
    if subtype == "RNAM":
        name_len = struct.unpack("<i",stream.read(4))[0]
        room_name = read_name(stream, name_len)
    
    return room_name

def read_RSEG(stream):
    rseg_size = struct.unpack("<i",stream.read(4))[0]
    rseg_size_cur = rseg_size

    points = []
    attr1 = None
    attr2 = None
    attr3 = None
    wdth1 = None
    wdth2 = None
    unk_name = ''
    len_points = 0

    while rseg_size_cur > 0:
        subtype = read_block_type(stream)
        subtype_size = struct.unpack("<i",stream.read(4))[0]

        if subtype == "ATTR":
            attr1 = struct.unpack("<i",stream.read(4))[0]
            attr2 = struct.unpack("<d",stream.read(8))[0]
            attr3 = struct.unpack("<i",stream.read(4))[0]

            rseg_size_cur -= (subtype_size+8) #subtype+subtype_size

        elif subtype == "WDTH":
            wdth1 = struct.unpack("<d",stream.read(8))[0]
            wdth2 = struct.unpack("<d",stream.read(8))[0]

            rseg_size_cur -= (subtype_size+8) #subtype+subtype_size

        elif subtype == "VDAT":
            len_points = struct.unpack("<i",stream.read(4))[0]
            for i in range (len_points):
                points.append(struct.unpack("ddd",stream.read(24)))

            rseg_size_cur -= (subtype_size+8) #subtype+subtype_size

        elif subtype == "RTEN":
            unk_name = read_name(stream, subtype_size)

            subtype_size = ((subtype_size >> 2) + 1) * 4

            rseg_size_cur -= (subtype_size+8) #subtype+subtype_size

    return {
        "attr1": attr1,
        "attr2": attr2,
        "attr3": attr3,
        "width1": wdth1,
        "width2": wdth2,
        "unk_name": unk_name,
        "point_cnt": len_points
    }

def read_RNOD(stream):
    rnod_size = struct.unpack("<i",stream.read(4))[0]
    rnod_size_cur = rnod_size

    obj_name = ''
    object_matrix = None
    pos = None
    flag = None

    cur_pos = (0.0,0.0,0.0)

    while rnod_size_cur > 0:
        subtype = read_block_type(stream)
        subtype_size = struct.unpack("<i",stream.read(4))[0]
        if subtype == "NNAM":
            obj_name = read_name(stream, subtype_size)

            real_size = ((subtype_size >> 2) + 1) * 4
            rnod_size_cur -= (real_size+8) #subtype+subtype_size
        elif subtype == "POSN":
            pos = struct.unpack("ddd",stream.read(24))

            rnod_size_cur -= (subtype_size+8) #subtype+subtype_size
        elif subtype == "ORTN":
            object_matrix = []
            for i in range(4):
                object_matrix.append(struct.unpack("<ddd",stream.read(24)))

            rnod_size_cur -= (subtype_size+8) #subtype+subtype_size
        elif subtype == "FLAG":
            flag = struct.unpack("<i",stream.read(4))[0]

            rnod_size_cur -= (subtype_size+8) #subtype+subtype_size
    
    oriented = True
    if pos is not None:
        oriented = False
    
    if pos is not None:
        cur_pos = pos
    elif object_matrix is not None:
        cur_pos = object_matrix[3]

    
    return {
        "name": obj_name,
        "oriented": oriented,
        "pos": cur_pos,
        "flag": flag
    }

def read_block(stream):
    block_type = read_block_type(stream)
    room_name = None
    block_data = None

    if block_type == 'GROM':
        room_name = read_room(stream)
    if block_type == 'RSEG':
        block_data = read_RSEG(stream)
    elif block_type == 'RNOD':
        block_data = read_RNOD(stream)

    return {
        'room_name': room_name,
        'block_type': block_type,
        'block_data': block_data
    }


