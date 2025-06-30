import struct


def read_cstring(stream):
    chars = []
    while True:
        c = stream.read(1)
        if c == b'\x00' or c == b'':
            break
        chars.append(c)
    return b''.join(chars).decode('utf-8')

def read_file_entry(stream):
    item_value = read_cstring(stream)
    len_data, = struct.unpack('<I', stream.read(4))
    data = stream.read(len_data)
    return {
        'item_value': item_value,
        'len_data': len_data,
        'data': data
    }

def read_file_entry_metadata(stream):
    full_name = read_cstring(stream)
    only_name = full_name.split(' ')[0]
    len_data, = struct.unpack('<I', stream.read(4))
    stream.seek(len_data, 1)
    return {
        'name': only_name,
        'len_data': len_data
    }

def parse_sounds(stream, num_items):
    sounds = {}
    for i in range(num_items):
        soundString = read_cstring(stream)
        soundArr = soundString.split(' ')
        soundName = soundArr[0]
        soundIndex = soundArr[1]
        # print("{} {}".format(soundName, soundIndex))
        sounds[soundName] = int(soundIndex)
    return sounds

def parse_materials(stream, num_items):
    materials = {}
    for j in range(num_items):
        matString = read_cstring(stream)
        matArr = matString.split(' ', 1)
        matName = matArr[0]
        matParams = matArr[1]
        curMat = parse_mat_string(matParams)
        materials[matName] = curMat
    
    return materials

def get_tex(matObj):
    idx = matObj["tex_idx"]
    if idx > -1:
        return matObj['params'][idx]
    else:
        return -1

def set_tex(matObj, value):
    idx = matObj["tex_idx"]
    if idx > -1:
        matObj['params'][idx] = value

def get_ttx(matObj):
    idx = matObj["ttx_idx"]
    if idx > -1:
        return matObj['params'][idx]
    else:
        return -1

def set_ttx(matObj, value):
    idx = matObj["ttx_idx"]
    if idx > -1:
        matObj['params'][idx] = value

def get_itx(matObj):
    idx = matObj["itx_idx"]
    if idx > -1:
        return matObj['params'][idx]
    else:
        return -1

def set_itx(matObj, value):
    idx = matObj["itx_idx"]
    if idx > -1:
        matObj['params'][idx] = value

def get_msk(matObj):
    idx = matObj["msk_idx"]
    if idx > -1:
        return matObj['params'][idx]
    else:
        return -1

def set_msk(matObj, value):
    idx = matObj["msk_idx"]
    if idx > -1:
        matObj['params'][idx] = value

def get_mat_string(matObj):
    tex_idx = matObj["tex_idx"]
    ttx_idx = matObj["ttx_idx"]
    itx_idx = matObj["itx_idx"]
    msk_idx = matObj["msk_idx"]

    params = list(matObj["params"]) #copy

    if(tex_idx > -1):
        params[tex_idx] = "{} {}".format("tex", params[tex_idx])
    if(ttx_idx > -1):
        params[ttx_idx] = "{} {}".format("tex", params[ttx_idx])
    if(itx_idx > -1):
        params[itx_idx] = "{} {}".format("tex", params[itx_idx])
    if(msk_idx > -1):
        params[msk_idx] = "{} {}".format("tex", params[msk_idx])

    return " ".join(params)
        


def parse_mat_string(matString):
    i = 0
    result = {
        "tex_idx": -1,
        "ttx_idx": -1,
        "itx_idx": -1,
        "msk_idx": -1,
        "params": []
    }

    matParams = [mat for mat in matString.split(' ') if mat.strip() != ""] #array without whitespaces

    i = 0
    p = 0
    other_params_buf = []
    while i < len(matParams):
        paramName = matParams[i].replace('"', '')
        if len(paramName) > 0:
            if paramName in ["tex", "ttx", "itx", "msk"]:
                if len(other_params_buf) > 0:
                    result["params"].append(" ".join(other_params_buf))
                    other_params_buf = []
                    p+=1

                result["{}_idx".format(paramName)] = p
                result["params"].append(int(matParams[i+1]))
                i+=1
                p+=1
            else:
                other_params_buf.append(matParams[i])
        i+=1

    if len(other_params_buf) > 0:
        result["params"].append(" ".join(other_params_buf))
    
    return result


def read_section(stream):
    section = read_cstring(stream)
    if(len(section) > 0):
        section_split = section.split(" ")
        section_name = section_split[0]
        num_items = int(section_split[1])
        data = {}
        start_pos = stream.tell()
        if section_name == u"MASKFILES":
            data = read_file_metadata(stream, num_items)
        elif section_name == u"SOUNDS":
            data = read_string_metadata(stream, num_items)
        elif section_name == u"TEXTUREFILES":
            data = read_file_metadata(stream, num_items)
        elif section_name == u"SOUNDFILES":
            data = read_file_metadata(stream, num_items)
        elif section_name == u"COLORS":
            data = read_string(stream, num_items)
        elif section_name == u"MATERIALS":
            data = read_string_metadata(stream, num_items)
        elif section_name == u"BACKFILES":
            data = read_file_metadata(stream, num_items)
        elif section_name == u"PALETTEFILES":
            data = read_file_metadata(stream, num_items)
        else:
            return False
        size = stream.tell() - start_pos
        return {
            'name': section_name,
            'start': start_pos,
            'size': size,
            'cnt': num_items,
            'metadata_order': data['data_order'],
            'metadata': data['data']
        }


def read_file_metadata(stream, num_items): #for most of *FILES
    data = {}
    # start_pos = None
    # end_pos = None
    data_order = []
    for i in range(num_items):
        start_pos = stream.tell()
        metadata_entry = read_file_entry_metadata(stream)
        end_pos = stream.tell()
        
        data_order.append(metadata_entry['name'])
        data[metadata_entry['name']] = {
            "start" : start_pos,
            "size" : end_pos - start_pos
        }

    return {
        "data_order": data_order,
        "data": data
    }


def read_string_metadata(stream, num_items): #for SOUNDS and MATERIALS
    data = {}
    data_order = []
    for i in range(num_items):
        start_pos = stream.tell()
        metadata_entry = read_cstring(stream)
        record_name = metadata_entry.split(' ')[0]
        end_pos = stream.tell()
        
        data[record_name] = {
            "start" : start_pos,
            "size" : end_pos - start_pos
        }
    
    return {
        "data_order": [],
        "data": data
    }

def read_string(stream, num_items): #for COLORS as they aren't named     
    data = []
    for i in range(num_items):
        metadata_entry = read_cstring(stream)
        data.append(metadata_entry)
    
    return {
        "data_order": [],
        "data": data
    }
