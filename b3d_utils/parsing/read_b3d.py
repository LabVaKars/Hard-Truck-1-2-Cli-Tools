import struct
import re
import enum

import parsing.skip_b3d as b3ds 

class ChunkType(enum.Enum):
    END_CHUNK = 0
    END_CHUNKS = 1
    BEGIN_CHUNK = 2
    GROUP_CHUNK = 3
    
def read_chunk_type(_io):
    oc = _io.read(4)
    # print(oc)
    if (oc == (b'\x4D\x01\x00\x00')): # Begin_Chunk(111)
        return ChunkType.BEGIN_CHUNK
    elif oc == (b'\x2B\x02\x00\x00'): # End_Chunk(555)
        return ChunkType.END_CHUNK
    elif oc == (b'\xbc\x01\x00\x00'): # Group_Chunk(444)
        return ChunkType.GROUP_CHUNK
    elif oc == (b'\xde\x00\x00\x00'): # End_Chunks(222)
        return ChunkType.END_CHUNKS
    else:
        print(_io.tell())
        raise Exception()

def read_uv(stream):
    u, v = struct.unpack('<ff', stream.read(8))
    return {'u': u, 'v': v}

def read_point(stream):
    x, y, z = struct.unpack('<fff', stream.read(12))
    return {'x': x, 'y': y, 'z': z}

def read_color(stream):
    r, g, b = struct.unpack('<fff', stream.read(12))
    return {'r': r, 'g': g, 'b': b}

def read_sphere(stream):
    x, y, z, r = struct.unpack('<ffff', stream.read(16))
    return {'x': x, 'y': y, 'z': z, 'r': r}

def read_name32(stream):
    name = stream.read(32).decode('utf-8').rstrip('\x00')
    return {'name': name}

def is_empty_name(name):
    re_is_empty = re.compile(r'.*{}.*'.format('~'))
    return re_is_empty.search(name)

def write_name(stream, name):
    obj_name = ''
    if not is_empty_name(name):
        obj_name = name
    name_len = len(obj_name)
    if name_len <= 32:
        stream.write(obj_name.encode("cp1251"))
    stream.write(bytearray(b'\00'*(32-name_len)))
    return

def read_normal(stream):
    p_normal_switch, = struct.unpack('<I', stream.read(4))
    if p_normal_switch == 0:
        normal1 = read_point(stream)
        return {'p_normal_switch': p_normal_switch, 'normal1': normal1}
    elif p_normal_switch == 1:
        normal_off1, = struct.unpack('<f', stream.read(4))
        return {'p_normal_switch': p_normal_switch, 'normal_off1': normal_off1}
    else:
        raise ValueError(f'Invalid p_normal_switch value: {p_normal_switch}')

def read_simple_vert(stream):
    vert_coord = read_point(stream)
    uv_coord = read_uv(stream)
    return {'vert_coord': vert_coord, 'uv_coord': uv_coord}

def read_vertex_8(stream, p_use_uv, p_use_normal, p_uv_count, p_normal_switch):
    vert_ind, = struct.unpack('<I', stream.read(4))
    result = {'vert_ind': vert_ind}

    if p_use_uv:
        vert_uv = [read_uv(stream) for _ in range(p_uv_count)]
        result['vert_uv'] = vert_uv

    if p_use_normal:
        vert_normal = read_normal_param(stream, p_normal_switch)
        result['vert_normal'] = vert_normal

    return result

def read_normal_param(stream, p_normal_switch):
    if p_normal_switch == 0:
        normal1 = read_point(stream)
        return {'p_normal_switch': p_normal_switch, 'normal1': normal1}
    elif p_normal_switch == 1:
        normal_off1, = struct.unpack('<f', stream.read(4))
        return {'p_normal_switch': p_normal_switch, 'normal_off1': normal_off1}
    else:
        return {'p_normal_switch': p_normal_switch}

def read_polygon_8(stream):
    format_raw, = struct.unpack('<I', stream.read(4))
    unk_f, = struct.unpack('<f', stream.read(4))
    unk_i, = struct.unpack('<I', stream.read(4))
    texnum_pos = stream.tell()
    texnum, = struct.unpack('<I', stream.read(4))
    vert_count, = struct.unpack('<I', stream.read(4))

    format = format_raw ^ 1
    use_uv = (format & 0b10) > 0
    use_normal = ((format & 0b100000) > 0) and ((format & 0b10000) > 0)
    uv_count = ((format & 0xff00) >> 8) + (1 if use_uv else 0)
    normal_switch = -1 if not use_normal else (0 if (format & 1) > 0 else 1)

    verts = [
        read_vertex_8(stream, use_uv, use_normal, uv_count, normal_switch)
        for _ in range(vert_count)
    ]

    return {
        'format_raw': format_raw,
        'unk_f': unk_f,
        'unk_i': unk_i,
        'texnum': texnum,
        'texnum_pos': texnum_pos,
        'vert_count': vert_count,
        'verts': verts,
        'format': format,
        'use_uv': use_uv,
        'use_normal': use_normal,
        'uv_count': uv_count,
        'normal_switch': normal_switch,
    }


def read_vertex_28(stream, p_use_uv, p_uv_count):
    scale_u, scale_v = struct.unpack('<II', stream.read(8))
    result = {
        'scale_u': scale_u,
        'scale_v': scale_v,
    }

    if p_use_uv:
        vert_uv = read_uv(stream)
        vert_uv_extra = [read_uv(stream) for _ in range(p_uv_count - 1)]
        result['vert_uv'] = vert_uv
        result['vert_uv_extra'] = vert_uv_extra

    return result

def read_polygon_28(stream):
    format_raw, = struct.unpack('<I', stream.read(4))
    unk_f, = struct.unpack('<f', stream.read(4))
    unk_i, = struct.unpack('<I', stream.read(4))
    texnum_pos = stream.tell()
    texnum, = struct.unpack('<I', stream.read(4))
    vert_count, = struct.unpack('<I', stream.read(4))

    format = format_raw
    use_uv = (format & 0b10) > 0
    use_normal = ((format & 0b100000) > 0) and ((format & 0b10000) > 0)
    uv_count = ((format & 0xff00) >> 8) + 1
    normal_switch = -1 if not use_normal else (0 if (format & 1) > 0 else 1)

    verts = [
        read_vertex_28(stream, use_uv, uv_count)
        for _ in range(vert_count)
    ]

    return {
        'format_raw': format_raw,
        'unk_f': unk_f,
        'unk_i': unk_i,
        'texnum': texnum,
        'texnum_pos': texnum_pos,
        'vert_count': vert_count,
        'verts': verts,
        'format': format,
        'use_uv': use_uv,
        'use_normal': use_normal,
        'uv_count': uv_count,
        'normal_switch': normal_switch,
    }

def read_complex_vert(stream, p_uv_count, p_normal_switch):
    vert_coord = read_point(stream)
    uv_coord = read_uv(stream)
    uv_coord_extra = [read_uv(stream) for _ in range(p_uv_count)]
    vert_normal = read_normal_param(stream, p_normal_switch)

    return {
        'vert_coord': vert_coord,
        'uv_coord': uv_coord,
        'uv_coord_extra': uv_coord_extra,
        'vert_normal': vert_normal
    }

def read_unk_3fi(stream):
    unk_3f = read_point(stream)  
    unk_i, = struct.unpack('<I', stream.read(4)) 
    return {
        'unk_3f': unk_3f,
        'unk_i': unk_i
    }
    
def read_unk_fi(stream):
    unkf, = struct.unpack('<f', stream.read(4))
    unki, = struct.unpack('<I', stream.read(4))
    return {
        'unkf': unkf,
        'unki': unki
    }

def read_b_0(stream):
    content = list(struct.unpack('<11f', stream.read(44)))
    return {'content': content}

def read_b_1(stream):
    name1 = read_name32(stream)
    name2 = read_name32(stream)
    return {'name1': name1, 'name2': name2}

def read_b_2(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {'bound1': bound1, 'unk1': unk1, 'child_cnt': child_cnt}

def read_b_3(stream):
    bound1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {'bound1': bound1, 'child_cnt': child_cnt}

def read_b_4(stream):
    bound1 = read_sphere(stream)
    name1 = read_name32(stream)
    name2 = read_name32(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {'bound1': bound1, 'name1': name1, 'name2': name2, 'child_cnt': child_cnt}

def read_b_5(stream):
    bound1 = read_sphere(stream)
    name1 = read_name32(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {'bound1': bound1, 'name1': name1, 'child_cnt': child_cnt}

def read_b_6(stream):
    bound1 = read_sphere(stream)
    name1 = read_name32(stream)
    name2 = read_name32(stream)
    vert_count, = struct.unpack('<I', stream.read(4))
    vertices = [read_simple_vert(stream) for _ in range(vert_count)]
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'name1': name1,
        'name2': name2,
        'vert_count': vert_count,
        'vertices': vertices,
        'child_cnt': child_cnt
    }

def read_b_7(stream):
    bound1 = read_sphere(stream)
    group_name = read_name32(stream)
    vert_count, = struct.unpack('<I', stream.read(4))
    vertices = [read_simple_vert(stream) for _ in range(vert_count)]
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'group_name': group_name,
        'vert_count': vert_count,
        'vertices': vertices,
        'child_cnt': child_cnt
    }

def read_b_8(stream):
    bound1 = read_sphere(stream)
    poly_count, = struct.unpack('<I', stream.read(4))
    polygons = [read_polygon_8(stream) for _ in range(poly_count)]
    return {
        'bound1': bound1,
        'poly_count': poly_count,
        'polygons': polygons
    }

def read_b_9(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'child_cnt': child_cnt
    }

def read_b_10(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'child_cnt': child_cnt
    }


def read_b_11(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'child_cnt': child_cnt
    }

def read_b_12(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    unk_i1, unk_i2, unk_count = struct.unpack('<III', stream.read(12))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_13(stream):
    bound1 = read_sphere(stream)
    unk_i1, unk_i2, unk_count = struct.unpack('<III', stream.read(12))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_14(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    unk_i1, unk_i2, unk_count = struct.unpack('<III', stream.read(12))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_15(stream):
    bound1 = read_sphere(stream)
    unk_i1, unk_i2, unk_count = struct.unpack('<III', stream.read(12))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_16(stream):
    bound1 = read_sphere(stream)
    point1 = read_point(stream)
    point2 = read_point(stream)
    unk_f1, unk_f2 = struct.unpack('<ff', stream.read(8))
    unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'point1': point1,
        'point2': point2,
        'unk_f1': unk_f1,
        'unk_f2': unk_f2,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_17(stream):
    bound1 = read_sphere(stream)
    point1 = read_point(stream)
    point2 = read_point(stream)
    unk_f1, unk_f2 = struct.unpack('<ff', stream.read(8))
    unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    return {
        'bound1': bound1,
        'point1': point1,
        'point2': point2,
        'unk_f1': unk_f1,
        'unk_f2': unk_f2,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_18(stream):
    bound1 = read_sphere(stream)
    space_name = read_name32(stream)
    add_name = read_name32(stream)
    return {
        'bound1': bound1,
        'space_name': space_name,
        'add_name': add_name
    }

def read_b_19(stream):
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {'child_cnt': child_cnt}

def read_b_20(stream):
    bound1 = read_sphere(stream)
    coords_count, = struct.unpack('<I', stream.read(4))
    unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    coords = [read_point(stream) for _ in range(coords_count)]
    return {
        'bound1': bound1,
        'coords_count': coords_count,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats,
        'coords': coords
    }

def read_b_21(stream):
    bound1 = read_sphere(stream)
    group_cnt, = struct.unpack('<I', stream.read(4))
    unk_i1, = struct.unpack('<I', stream.read(4))
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'group_cnt': group_cnt,
        'unk_i1': unk_i1,
        'child_cnt': child_cnt
    }

def read_b_22(stream):
    bound1 = read_sphere(stream)
    unk1 = read_sphere(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk1': unk1,
        'child_cnt': child_cnt
    }

def read_b_23(stream):
    unk_i1, = struct.unpack('<I', stream.read(4))
    surface, = struct.unpack('<I', stream.read(4))
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    verts_count, = struct.unpack('<I', stream.read(4))
    verts = [read_vert_23(stream) for _ in range(verts_count)]
    return {
        'unk_i1': unk_i1,
        'surface': surface,
        'unk_count': unk_count,
        'unk_floats': unk_floats,
        'verts_count': verts_count,
        'verts': verts
    }

def read_vert_23(stream):
    vert_count, = struct.unpack('<I', stream.read(4))
    verts = [read_point(stream) for _ in range(vert_count)]
    return {'vert_count': vert_count, 'verts': verts}

def read_b_24(stream):
    coord1 = read_point(stream)
    coord2 = read_point(stream)
    coord3 = read_point(stream)
    pos = read_point(stream)
    flag, = struct.unpack('<I', stream.read(4))
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'coord1': coord1,
        'coord2': coord2,
        'coord3': coord3,
        'pos': pos,
        'flag': flag,
        'child_cnt': child_cnt
    }

def read_b_25(stream):
    unk_i1, = struct.unpack('<f', stream.read(4))
    unk_i2, unk_i3 = struct.unpack('<II', stream.read(8))
    unk_name = read_name32(stream)
    unk_p1 = read_point(stream)
    unk_p2 = read_point(stream)
    unk_f11, unk_f12, unk_f13, unk_f14, unk_f15 = struct.unpack('<fffff', stream.read(20))
    return {
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_i3': unk_i3,
        'unk_name': unk_name,
        'unk_p1': unk_p1,
        'unk_p2': unk_p2,
        'unk_f11': unk_f11,
        'unk_f12': unk_f12,
        'unk_f13': unk_f13,
        'unk_f14': unk_f14,
        'unk_f15': unk_f15
    }

def read_b_26(stream):
    bound1 = read_sphere(stream)
    unk_p1 = read_point(stream)
    unk_p2 = read_point(stream)
    unk_p3 = read_point(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk_p1': unk_p1,
        'unk_p2': unk_p2,
        'unk_p3': unk_p3,
        'child_cnt': child_cnt
    }

def read_b_27(stream):
    bound1 = read_sphere(stream)
    flag, = struct.unpack('<I', stream.read(4))
    unk_p1 = read_point(stream)
    material, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'flag': flag,
        'unk_p1': unk_p1,
        'material': material
    }

def read_b_28(stream):
    bound1 = read_sphere(stream)
    sprite_center = read_point(stream)
    poly_count, = struct.unpack('<I', stream.read(4))
    polygons = [read_polygon_28(stream) for _ in range(poly_count)]
    return {
        'bound1': bound1,
        'sprite_center': sprite_center,
        'poly_count': poly_count,
        'polygons': polygons
    }

def read_b_29(stream):
    bound1 = read_sphere(stream)
    unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    unk_1 = read_sphere(stream)
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_1': unk_1,
        'unk_count': unk_count,
        'unk_floats': unk_floats,
        'child_cnt': child_cnt
    }

def read_b_30(stream):
    bound1 = read_sphere(stream)
    room_name = read_name32(stream)
    point1 = read_point(stream)
    point2 = read_point(stream)
    return {
        'bound1': bound1,
        'room_name': room_name,
        'point1': point1,
        'point2': point2
    }

def read_b_31(stream):
    bound1 = read_sphere(stream)
    unk_count, = struct.unpack('<I', stream.read(4))
    unk1 = read_sphere(stream)
    int2, = struct.unpack('<I', stream.read(4))
    unk_p2 = read_point(stream)
    unk_floats = [read_unk_fi(stream) for _ in range(unk_count)]
    return {
        'bound1': bound1,
        'unk_count': unk_count,
        'unk1': unk1,
        'int2': int2,
        'unk_p2': unk_p2,
        'unk_floats': unk_floats
    }

def read_b_33(stream):
    bound1 = read_sphere(stream)
    use_lights, light_type, flag = struct.unpack('<III', stream.read(12))
    unk_p1 = read_point(stream)
    unk_p2 = read_point(stream)
    unk_f1, unk_f2, light_radius, intensity, unk_f3, unk_f4 = struct.unpack('<ffffff', stream.read(24))
    rgb = read_color(stream)
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'use_lights': use_lights,
        'light_type': light_type,
        'flag': flag,
        'unk_p1': unk_p1,
        'unk_p2': unk_p2,
        'unk_f1': unk_f1,
        'unk_f2': unk_f2,
        'light_radius': light_radius,
        'intensity': intensity,
        'unk_f3': unk_f3,
        'unk_f4': unk_f4,
        'rgb': rgb,
        'child_cnt': child_cnt
    }

def read_b_34(stream):
    bound1 = read_sphere(stream)
    unk_i1, unk_count = struct.unpack('<II', stream.read(8))
    unk_floats = [read_unk_3fi(stream) for _ in range(unk_count)]
    return {
        'bound1': bound1,
        'unk_i1': unk_i1,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_b_35(stream):
    bound1 = read_sphere(stream)
    mtype, = struct.unpack('<I', stream.read(4))
    texnum_pos = stream.tell()
    texnum, = struct.unpack('<I', stream.read(4))
    poly_count, = struct.unpack('<I', stream.read(4))
    polygons = [read_polygon_8(stream) for _ in range(poly_count)]
    return {
        'bound1': bound1,
        'mtype': mtype,
        'texnum_pos': texnum_pos,
        'texnum': texnum,
        'poly_count': poly_count,
        'polygons': polygons
    }

def read_b_36(stream):
    bound1 = read_sphere(stream)
    name1 = read_name32(stream)
    name2 = read_name32(stream)
    format_raw, = struct.unpack('<I', stream.read(4))
    format_ = format_raw & 0xff
    vert_count, = struct.unpack('<I', stream.read(4))
    uv_count = format_raw >> 8
    normal_switch = 0 if (format_ == 1 or format_ == 2) else 1
    vertices = [read_complex_vert(stream, uv_count, normal_switch) for _ in range(vert_count)]
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'name1': name1,
        'name2': name2,
        'format_raw': format_raw,
        'vert_count': vert_count,
        'vertices': vertices,
        'child_cnt': child_cnt
    }

def read_b_37(stream):
    bound1 = read_sphere(stream)
    group_name = read_name32(stream)
    format_raw, = struct.unpack('<I', stream.read(4))
    format_ = format_raw & 0xff 
    vert_count, = struct.unpack('<I', stream.read(4))
    uv_count = format_raw >> 8
    normal_switch = 0 if (format_ == 1 or format_ == 2) else 1
    vertices = [read_complex_vert(stream, uv_count, normal_switch) for _ in range(vert_count)]
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'group_name': group_name,
        'format_raw': format_raw,
        'vert_count': vert_count,
        'vertices': vertices,
        'child_cnt': child_cnt
    }

def read_b_39(stream):
    bound1 = read_sphere(stream)
    color_r, = struct.unpack('<I', stream.read(4))
    unk_f1, unk_f2 = struct.unpack('<ff', stream.read(8))
    fog_start, fog_end = struct.unpack('<ff', stream.read(8))
    color_id, = struct.unpack('<I', stream.read(4))
    child_cnt, = struct.unpack('<I', stream.read(4))
    return {
        'bound1': bound1,
        'color_r': color_r,
        'unk_f1': unk_f1,
        'unk_f2': unk_f2,
        'fog_start': fog_start,
        'fog_end': fog_end,
        'color_id': color_id,
        'child_cnt': child_cnt
    }

def read_b_40(stream):
    bound1 = read_sphere(stream)
    name1 = read_name32(stream)
    name2 = read_name32(stream)
    unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    unk_count, = struct.unpack('<I', stream.read(4))
    unk_floats = [struct.unpack('<f', stream.read(4))[0] for _ in range(unk_count)]
    return {
        'bound1': bound1,
        'name1': name1,
        'name2': name2,
        'unk_i1': unk_i1,
        'unk_i2': unk_i2,
        'unk_count': unk_count,
        'unk_floats': unk_floats
    }

def read_block(stream):
    block_name = read_name32(stream)
    block_type, = struct.unpack('<I', stream.read(4))
    block_data = None
    
    # Switch based on block_type
    if block_type == 0:
        block_data = read_b_0(stream)
    elif block_type == 1:
        block_data = read_b_1(stream)
    elif block_type == 2:
        block_data = read_b_2(stream)
    elif block_type == 3:
        block_data = read_b_3(stream)
    elif block_type == 4:
        block_data = read_b_4(stream)
    elif block_type == 5:
        block_data = read_b_5(stream)
    elif block_type == 6:
        block_data = read_b_6(stream)
    elif block_type == 7:
        block_data = read_b_7(stream)
    elif block_type == 8:
        block_data = read_b_8(stream)
    elif block_type == 9:
        block_data = read_b_9(stream)
    elif block_type == 10:
        block_data = read_b_10(stream)
    elif block_type == 11:
        block_data = read_b_11(stream)
    elif block_type == 12:
        block_data = read_b_12(stream)
    elif block_type == 13:
        block_data = read_b_13(stream)
    elif block_type == 14:
        block_data = read_b_14(stream)
    elif block_type == 15:
        block_data = read_b_15(stream)
    elif block_type == 16:
        block_data = read_b_16(stream)
    elif block_type == 17:
        block_data = read_b_17(stream)
    elif block_type == 18:
        block_data = read_b_18(stream)
    elif block_type == 19:
        block_data = read_b_19(stream)
    elif block_type == 20:
        block_data = read_b_20(stream)
    elif block_type == 21:
        block_data = read_b_21(stream)
    elif block_type == 22:
        block_data = read_b_22(stream)
    elif block_type == 23:
        block_data = read_b_23(stream)
    elif block_type == 24:
        block_data = read_b_24(stream)
    elif block_type == 25:
        block_data = read_b_25(stream)
    elif block_type == 26:
        block_data = read_b_26(stream)
    elif block_type == 27:
        block_data = read_b_27(stream)
    elif block_type == 28:
        block_data = read_b_28(stream)
    elif block_type == 29:
        block_data = read_b_29(stream)
    elif block_type == 30:
        block_data = read_b_30(stream)
    elif block_type == 31:
        block_data = read_b_31(stream)
    elif block_type == 33:
        block_data = read_b_33(stream)
    elif block_type == 34:
        block_data = read_b_34(stream)
    elif block_type == 35:
        block_data = read_b_35(stream)
    elif block_type == 36:
        block_data = read_b_36(stream)
    elif block_type == 37:
        block_data = read_b_37(stream)
    elif block_type == 39:
        block_data = read_b_39(stream)
    elif block_type == 40:
        block_data = read_b_40(stream)
    
    return {
        'block_name': block_name,
        'block_type': block_type,
        'block_data': block_data
    }

def read_file_header(stream):
    magic = struct.unpack('<4B', stream.read(4))
    len_file, ofc_materials, len_materials_section, ofc_nodes, len_nodes = struct.unpack('<5I', stream.read(20))
    return {
        'magic': magic,
        'len_file': len_file,
        'ofc_materials': ofc_materials,
        'len_materials_section': len_materials_section,
        'ofc_nodes': ofc_nodes,
        'len_nodes': len_nodes
    }

def read_materials_list(stream):
    mat_count, = struct.unpack('<I', stream.read(4))
    mat_names = [read_name32(stream) for _ in range(mat_count)]
    return {
        'mat_count': mat_count,
        'mat_names': mat_names
    }

class ChunkType(enum.Enum):
    END_CHUNK = 0
    END_CHUNKS = 1
    BEGIN_CHUNK = 2
    GROUP_CHUNK = 3

def openclose(_io):
    oc = _io.read(4)
    # print(oc)
    if (oc == (b'\x4D\x01\x00\x00')): # Begin_Chunk(111)
        return ChunkType.BEGIN_CHUNK
    elif oc == (b'\x2B\x02\x00\x00'): # End_Chunk(555)
        return ChunkType.END_CHUNK
    elif oc == (b'\xbc\x01\x00\x00'): # Group_Chunk(444)
        return ChunkType.GROUP_CHUNK
    elif oc == (b'\xde\x00\x00\x00'): # End_Chunks(222)
        return ChunkType.END_CHUNKS
    else:
        # log.debug(file.tell())
        raise Exception()
    
def read_roots(stream, nodesOffset):
    
    ex = 0
    level = 0
    
    roots = {}
    references = {}

    objName = ''
    rootObjName = ''
    start_pos = nodesOffset
    end_pos = 0


    def fill_texnum(obj_name, block_data):
        texnum = block_data['texnum']
        texpos = block_data['texnum_pos']
        roots[obj_name]["texnums"].append({
            "val": texnum,
            "pos": texpos - start_pos
        })

    while ex != ChunkType.END_CHUNKS:

        ex = openclose(stream)
        if ex == ChunkType.END_CHUNK:
            level -= 1
            if level == 0:
                end_pos = stream.tell()
                roots[rootObjName]["start"] = start_pos
                roots[rootObjName]["size"] = end_pos - start_pos

        elif ex == ChunkType.END_CHUNKS:
            break
        elif ex == ChunkType.GROUP_CHUNK: #skip
            continue
        elif ex == ChunkType.BEGIN_CHUNK:

            if level == 0:
                start_pos = stream.tell()-4
            
            
            block_name = read_name32(stream)
            block_type, = struct.unpack('<I', stream.read(4))
            block_data = None

            if level == 0:
                rootObjName = block_name['name']
                roots[rootObjName] = {
                    "start": None,
                    "size": None,
                    "texnums": []
                }
            
            # Switch based on block_type
            if block_type == 0:
                block_data = b3ds.skip_b_0(stream)
            elif block_type == 1:
                block_data = b3ds.skip_b_1(stream)
            elif block_type == 2:
                block_data = b3ds.skip_b_2(stream)
            elif block_type == 3:
                block_data = b3ds.skip_b_3(stream)
            elif block_type == 4:
                block_data = b3ds.skip_b_4(stream)
            elif block_type == 5:
                block_data = b3ds.skip_b_5(stream)
            elif block_type == 6:
                block_data = b3ds.skip_b_6(stream)
            elif block_type == 7:
                block_data = b3ds.skip_b_7(stream)
            elif block_type == 8:
                block_data = read_b_8(stream)
            elif block_type == 9:
                block_data = b3ds.skip_b_9(stream)
            elif block_type == 10:
                block_data = b3ds.skip_b_10(stream)
            elif block_type == 11:
                block_data = b3ds.skip_b_11(stream)
            elif block_type == 12:
                block_data = b3ds.skip_b_12(stream)
            elif block_type == 13:
                block_data = b3ds.skip_b_13(stream)
            elif block_type == 14:
                block_data = b3ds.skip_b_14(stream)
            elif block_type == 15:
                block_data = b3ds.skip_b_15(stream)
            elif block_type == 16:
                block_data = b3ds.skip_b_16(stream)
            elif block_type == 17:
                block_data = b3ds.skip_b_17(stream)
            elif block_type == 18:
                block_data = read_b_18(stream)
            elif block_type == 19:
                block_data = b3ds.skip_b_19(stream)
            elif block_type == 20:
                block_data = b3ds.skip_b_20(stream)
            elif block_type == 21:
                block_data = b3ds.skip_b_21(stream)
            elif block_type == 22:
                block_data = b3ds.skip_b_22(stream)
            elif block_type == 23:
                block_data = b3ds.skip_b_23(stream)
            elif block_type == 24:
                block_data = b3ds.skip_b_24(stream)
            elif block_type == 25:
                block_data = b3ds.skip_b_25(stream)
            elif block_type == 26:
                block_data = b3ds.skip_b_26(stream)
            elif block_type == 27:
                block_data = b3ds.skip_b_27(stream)
            elif block_type == 28:
                block_data = read_b_28(stream)
            elif block_type == 29:
                block_data = b3ds.skip_b_29(stream)
            elif block_type == 30:
                block_data = b3ds.skip_b_30(stream)
            elif block_type == 31:
                block_data = b3ds.skip_b_31(stream)
            elif block_type == 33:
                block_data = b3ds.skip_b_33(stream)
            elif block_type == 34:
                block_data = b3ds.skip_b_34(stream)
            elif block_type == 35:
                block_data = read_b_35(stream)
            elif block_type == 36:
                block_data = b3ds.skip_b_36(stream)
            elif block_type == 37:
                block_data = b3ds.skip_b_37(stream)
            elif block_type == 39:
                block_data = b3ds.skip_b_39(stream)
            elif block_type == 40:
                block_data = b3ds.skip_b_40(stream)

            curObjName = block_name['name']

            if level == 0:
                objName = curObjName
                references[objName] = []
            
            # fill reference list
            if block_type == 18:
                references[objName].append({
                    "space_name" : block_data['space_name']['name'],
                    "add_name" : block_data['add_name']['name'],
                })

            # fill texnum list
            if block_type in [8,28,35]:
                if(block_type == 35):
                    fill_texnum(rootObjName, block_data)
                for poly in block_data['polygons']:
                    fill_texnum(rootObjName, poly)

            level += 1

    return {
        "roots": roots,
        "references": references
    }
