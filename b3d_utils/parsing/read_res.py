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
        matArr = matString.split(' ')
        matName = matArr[0]
        matParams = matArr[1:]
        curMat = parse_material_params(matParams)
        curMat["raw_string"] = matString
        materials[matName] = curMat
    
    return materials

def parse_material_params(matParams):
    i = 0
    result = {}
    while i < len(matParams):
        paramName = matParams[i].replace('"', '')
        if len(paramName) > 0:
            if paramName in ["tex", "ttx", "itx", "col", "att", "msk", "power", "coord"]:
                result[paramName] = int(matParams[i+1])
                i+=1
            elif paramName in ["reflect", "specular", "transp", "rot"]:
                result[paramName] = float(matParams[i+1])
                i+=1
            elif paramName in ["noz", "nof", "notile", "notileu", "notilev", \
                            "alphamirr", "bumpcoord", "usecol", "wave"]:
                result[paramName] = True
            elif paramName in ["RotPoint", "move"]:
                result[paramName] = [float(matParams[i+1]), float(matParams[i+2])]
                i+=2
        elif paramName[0:3] == "env":
            envid = paramName[3:]
            if len(envid) > 0:
                result["envid"] = int(envid)
            else:
                result["env"] = [float(matParams[i+1]), float(matParams[i+2])]
                i+=2
        i+=1
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
