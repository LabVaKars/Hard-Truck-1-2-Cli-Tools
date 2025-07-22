import struct
import re

def skip_uv(stream):
    stream.seek(8, 1)
    # u, v = struct.unpack('<ff', stream.read(8))

def skip_point(stream):
    stream.seek(12, 1)
    # x, y, z = struct.unpack('<fff', stream.read(12))

def skip_color(stream):
    stream.seek(12, 1)
    # r, g, b = struct.unpack('<fff', stream.read(12))

def skip_sphere(stream):
    stream.seek(16, 1)
    # x, y, z, r = struct.unpack('<ffff', stream.read(16))

def skip_name32(stream):
    stream.seek(32, 1)
    # name = stream.read(32).decode('utf-8').rstrip('\x00')

def skip_normal(stream):
    p_normal_switch, = struct.unpack('<I', stream.read(4))
    if p_normal_switch == 0:
        skip_point(stream)
    elif p_normal_switch == 1:
        # struct.unpack('<f', stream.read(4))
        stream.seek(4, 1)
    else:
        raise ValueError(f'Invalid p_normal_switch value: {p_normal_switch}')

def skip_simple_vert(stream):
    skip_point(stream)
    skip_uv(stream)

def skip_poly_vert_8(stream, p_use_uv, p_use_normal, p_uv_count, p_normal_switch):
    # vert_ind, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)
    
    if p_use_uv:
        [skip_uv(stream) for _ in range(p_uv_count)]
        
    if p_use_normal:
        skip_normal_param(stream, p_normal_switch)
        
def skip_normal_param(stream, p_normal_switch):
    if p_normal_switch == 0:
        skip_point(stream)
    elif p_normal_switch == 1:
        # struct.unpack('<f', stream.read(4))
        stream.seek(4, 1)

def skip_polygon_8(stream):
    format_raw, = struct.unpack('<I', stream.read(4))
    # unk_f, = struct.unpack('<f', stream.read(4))
    # unk_i, = struct.unpack('<I', stream.read(4))
    # texnum, = struct.unpack('<I', stream.read(4))
    stream.seek(12, 1)
    vert_count, = struct.unpack('<I', stream.read(4))

    format = format_raw ^ 1
    use_uv = (format & 0b10) > 0
    use_normal = ((format & 0b100000) > 0) and ((format & 0b10000) > 0)
    uv_count = ((format & 0xff00) >> 8) + (1 if use_uv else 0)
    normal_switch = -1 if not use_normal else (0 if (format & 1) > 0 else 1)

    verts = [
        skip_poly_vert_8(stream, use_uv, use_normal, uv_count, normal_switch)
        for _ in range(vert_count)
    ]


def skip_poly_vert_28(stream, p_use_uv, p_uv_count):
    # scale_u, scale_v = struct.unpack('<II', stream.read(8))
    stream.seek(8, 1)
    
    if p_use_uv:
        skip_uv(stream)
        [skip_uv(stream) for _ in range(p_uv_count - 1)]


def skip_polygon_28(stream):
    format_raw, = struct.unpack('<I', stream.read(4))
    # unk_f, = struct.unpack('<f', stream.read(4))
    # unk_i, = struct.unpack('<I', stream.read(4))
    # texnum_pos is position marker, no read
    # texnum, = struct.unpack('<I', stream.read(4))
    stream.seek(12, 1)
    vert_count, = struct.unpack('<I', stream.read(4))

    format = format_raw
    use_uv = (format & 0b10) > 0
    use_normal = ((format & 0b100000) > 0) and ((format & 0b10000) > 0)
    uv_count = ((format & 0xff00) >> 8) + 1
    normal_switch = -1 if not use_normal else (0 if (format & 1) > 0 else 1)

    verts = [
        skip_poly_vert_28(stream, use_uv, uv_count)
        for _ in range(vert_count)
    ]

def skip_complex_vert(stream, p_uv_count, p_normal_switch):
    skip_point(stream)
    skip_uv(stream)
    [skip_uv(stream) for _ in range(p_uv_count)]
    skip_normal_param(stream, p_normal_switch)

    
def skip_unk_3fi(stream):
    skip_point(stream)  
    # struct.unpack('<I', stream.read(4)) 
    stream.seek(4, 1)
    
def skip_unk_fi(stream):
    # unkf, = struct.unpack('<f', stream.read(4))
    # unki, = struct.unpack('<I', stream.read(4))
    stream.seek(8, 1)

def skip_b_0(stream):
    stream.seek(44, 1)
    # content = list(struct.unpack('<11f', stream.read(44)))

def skip_b_1(stream):
    stream.seek(64, 1)
    # name1 = skip_name32(stream)
    # name2 = skip_name32(stream)

def skip_b_2(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_3(stream):
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_4(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_name32(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_5(stream):
    skip_sphere(stream)
    skip_name32(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_6(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_name32(stream)
    vert_count, = struct.unpack('<I', stream.read(4))
    [skip_simple_vert(stream) for _ in range(vert_count)]
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_7(stream):
    skip_sphere(stream)
    skip_name32(stream)
    vert_count, = struct.unpack('<I', stream.read(4))
    vert = [skip_simple_vert(stream) for _ in range(vert_count)]
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_8(stream):
    skip_sphere(stream)
    poly_count, = struct.unpack('<I', stream.read(4))
    poly = [skip_polygon_8(stream) for _ in range(poly_count)]

def skip_b_9(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_10(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)


def skip_b_11(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1)

def skip_b_12(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # unk_i1, unk_i2, 
    stream.seek(8, 1)
    unk_count = struct.unpack('<I', stream.read(4))
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    
def skip_b_13(stream):
    skip_sphere(stream)
    # unk_i1, unk_i2, 
    stream.seek(8, 1)
    unk_count = struct.unpack('<I', stream.read(4))
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    

def skip_b_14(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # unk_i1, unk_i2,
    stream.seek(8, 1) 
    unk_count = struct.unpack('<I', stream.read(4))[0]
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    
def skip_b_15(stream):
    skip_sphere(stream)
    # unk_i1, unk_i2, 
    stream.seek(8, 1) 
    unk_count = struct.unpack('<I', stream.read(4))[0]
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)

def skip_b_16(stream):
    skip_sphere(stream)
    skip_point(stream)
    skip_point(stream)
    # unk_f1, unk_f2
    # unk_i1, unk_i2
    stream.seek(16, 1) 
    unk_count, = struct.unpack('<I', stream.read(4))[0]
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)

def skip_b_17(stream):
    skip_sphere(stream)
    skip_point(stream)
    skip_point(stream)
    # unk_f1, unk_f2
    # unk_i1, unk_i2
    stream.seek(16, 1) 
    unk_count, = struct.unpack('<I', stream.read(4))[0]
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)

def skip_b_18(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_name32(stream)

def skip_b_19(stream):
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 

def skip_b_20(stream):
    skip_sphere(stream)
    coords_count, = struct.unpack('<I', stream.read(4))[0]
    # unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    stream.seek(8, 1) 
    unk_count, = struct.unpack('<I', stream.read(4))[0]
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    [skip_point(stream) for _ in range(coords_count)]
    
def skip_b_21(stream):
    skip_sphere(stream)
    # group_cnt, = struct.unpack('<I', stream.read(4))
    # unk_i1, = struct.unpack('<I', stream.read(4))
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(12, 1) 
    
def skip_b_22(stream):
    skip_sphere(stream)
    skip_sphere(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 

def skip_b_23(stream):
    # unk_i1, = struct.unpack('<I', stream.read(4))
    # surface, = struct.unpack('<I', stream.read(4))
    stream.seek(8, 1) 
    unk_count, = struct.unpack('<I', stream.read(4))
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    verts_count, = struct.unpack('<I', stream.read(4))
    [skip_vert_23(stream) for _ in range(verts_count)]
    

def skip_vert_23(stream):
    vert_count, = struct.unpack('<I', stream.read(4))
    [skip_point(stream) for _ in range(vert_count)]
    
def skip_b_24(stream):
    skip_point(stream)
    skip_point(stream)
    skip_point(stream)
    skip_point(stream)
    # flag, = struct.unpack('<I', stream.read(4))
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(8, 1) 

def skip_b_25(stream):
    # unk_i1, = struct.unpack('<f', stream.read(4))
    # unk_i2, unk_i3 = struct.unpack('<II', stream.read(8))
    stream.seek(12, 1) 
    skip_name32(stream)
    skip_point(stream)
    skip_point(stream)
    # unk_f11, unk_f12, unk_f13, unk_f14, unk_f15 = struct.unpack('<fffff', stream.read(20))
    stream.seek(20, 1) 

def skip_b_26(stream):
    skip_sphere(stream)
    skip_point(stream)
    skip_point(stream)
    skip_point(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 
    
def skip_b_27(stream):
    skip_sphere(stream)
    # flag, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 
    skip_point(stream)
    # material, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 
    
def skip_b_28(stream):
    skip_sphere(stream)
    skip_point(stream)
    poly_count, = struct.unpack('<I', stream.read(4))
    [skip_polygon_28(stream) for _ in range(poly_count)]
    
def skip_b_29(stream):
    skip_sphere(stream)
    # unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    stream.seek(8, 1) 
    skip_sphere(stream)
    unk_count, = struct.unpack('<I', stream.read(4))
    # unk_floats = list(struct.unpack(f'<{unk_count}f', stream.read(4 * unk_count)))
    stream.seek(4 * unk_count, 1)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 

def skip_b_30(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_point(stream)
    skip_point(stream)
    
def skip_b_31(stream):
    skip_sphere(stream)
    unk_count, = struct.unpack('<I', stream.read(4))
    skip_sphere(stream)
    # int2, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 
    skip_point(stream)
    [skip_unk_fi(stream) for _ in range(unk_count)]
    
def skip_b_33(stream):
    skip_sphere(stream)
    # use_lights, light_type, flag = struct.unpack('<III', stream.read(12))
    stream.seek(12, 1) 
    skip_point(stream)
    skip_point(stream)
    # unk_f1, unk_f2, light_radius, intensity, unk_f3, unk_f4 = struct.unpack('<ffffff', stream.read(24))
    stream.seek(24, 1) 
    skip_color(stream)
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 

def skip_b_34(stream):
    skip_sphere(stream)
    # unk_i1, 
    stream.seek(4, 1) 
    unk_count = struct.unpack('<I', stream.read(4))
    [skip_unk_3fi(stream) for _ in range(unk_count)]

def skip_b_35(stream):
    skip_sphere(stream)
    # mtype, = struct.unpack('<I', stream.read(4))
    # texnum, = struct.unpack('<I', stream.read(4))
    stream.seek(8, 1) 
    poly_count, = struct.unpack('<I', stream.read(4))
    [skip_polygon_8(stream) for _ in range(poly_count)]
    
def skip_b_36(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_name32(stream)
    format_raw, = struct.unpack('<I', stream.read(4))
    poly_count, = struct.unpack('<I', stream.read(4))
    uv_count = format_raw >> 8
    normal_switch = 0 if (format_raw == 1 or format_raw == 2) else 1
    [skip_complex_vert(stream, uv_count, normal_switch) for _ in range(poly_count)]
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 
    
def skip_b_37(stream):
    skip_sphere(stream)
    skip_name32(stream)
    format_raw, = struct.unpack('<I', stream.read(4))
    poly_count, = struct.unpack('<I', stream.read(4))
    uv_count = format_raw >> 8
    normal_switch = 0 if (format_raw == 1 or format_raw == 2) else 1
    [skip_complex_vert(stream, uv_count, normal_switch) for _ in range(poly_count)]
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(4, 1) 

def skip_b_39(stream):
    skip_sphere(stream)
    # color_r, = struct.unpack('<I', stream.read(4))
    # unk_f1, unk_f2 = struct.unpack('<ff', stream.read(8))
    # fog_start, fog_end = struct.unpack('<ff', stream.read(8))
    # color_id, = struct.unpack('<I', stream.read(4))
    # child_cnt, = struct.unpack('<I', stream.read(4))
    stream.seek(28, 1) 

def skip_b_40(stream):
    skip_sphere(stream)
    skip_name32(stream)
    skip_name32(stream)
    # unk_i1, unk_i2 = struct.unpack('<II', stream.read(8))
    stream.seek(8, 1) 
    unk_count, = struct.unpack('<I', stream.read(4))
    [struct.unpack('<f', stream.read(4))[0] for _ in range(unk_count)]
    
# def skip_block(stream):
#     block_name = skip_name32(stream)
#     block_type, = struct.unpack('<I', stream.read(4))
#     block_data = None
    
#     # Switch based on block_type
#     if block_type == 0:
#         block_data = skip_b_0(stream)
#     elif block_type == 1:
#         block_data = skip_b_1(stream)
#     elif block_type == 2:
#         block_data = skip_b_2(stream)
#     elif block_type == 3:
#         block_data = skip_b_3(stream)
#     elif block_type == 4:
#         block_data = skip_b_4(stream)
#     elif block_type == 5:
#         block_data = skip_b_5(stream)
#     elif block_type == 6:
#         block_data = skip_b_6(stream)
#     elif block_type == 7:
#         block_data = skip_b_7(stream)
#     elif block_type == 8:
#         block_data = skip_b_8(stream)
#     elif block_type == 9:
#         block_data = skip_b_9(stream)
#     elif block_type == 10:
#         block_data = skip_b_10(stream)
#     elif block_type == 11:
#         block_data = skip_b_11(stream)
#     elif block_type == 12:
#         block_data = skip_b_12(stream)
#     elif block_type == 13:
#         block_data = skip_b_13(stream)
#     elif block_type == 14:
#         block_data = skip_b_14(stream)
#     elif block_type == 15:
#         block_data = skip_b_15(stream)
#     elif block_type == 16:
#         block_data = skip_b_16(stream)
#     elif block_type == 17:
#         block_data = skip_b_17(stream)
#     elif block_type == 18:
#         block_data = skip_b_18(stream)
#     elif block_type == 19:
#         block_data = skip_b_19(stream)
#     elif block_type == 20:
#         block_data = skip_b_20(stream)
#     elif block_type == 21:
#         block_data = skip_b_21(stream)
#     elif block_type == 22:
#         block_data = skip_b_22(stream)
#     elif block_type == 23:
#         block_data = skip_b_23(stream)
#     elif block_type == 24:
#         block_data = skip_b_24(stream)
#     elif block_type == 25:
#         block_data = skip_b_25(stream)
#     elif block_type == 26:
#         block_data = skip_b_26(stream)
#     elif block_type == 27:
#         block_data = skip_b_27(stream)
#     elif block_type == 28:
#         block_data = skip_b_28(stream)
#     elif block_type == 29:
#         block_data = skip_b_29(stream)
#     elif block_type == 30:
#         block_data = skip_b_30(stream)
#     elif block_type == 31:
#         block_data = skip_b_31(stream)
#     elif block_type == 33:
#         block_data = skip_b_33(stream)
#     elif block_type == 34:
#         block_data = skip_b_34(stream)
#     elif block_type == 35:
#         block_data = skip_b_35(stream)
#     elif block_type == 36:
#         block_data = skip_b_36(stream)
#     elif block_type == 37:
#         block_data = skip_b_37(stream)
#     elif block_type == 39:
#         block_data = skip_b_39(stream)
#     elif block_type == 40:
#         block_data = skip_b_40(stream)
    
#     return {
#         'block_name': block_name,
#         'block_type': block_type,
#         'block_data': block_data
#     }

def skip_file_header(stream):
    # magic = struct.unpack('<4B', stream.read(4))
    # len_file, ofc_materials, len_materials_section, ofc_nodes, len_nodes = struct.unpack('<5I', stream.read(20))
    stream.seek(24, 1) 
    
def skip_materials_list(stream):
    mat_count, = struct.unpack('<I', stream.read(4))
    [skip_name32(stream) for _ in range(mat_count)]

