import struct



def read_cstring(stream):
    try:
        chrs = []
        i = 0
        chrs.append(stream.read(1).decode("utf-8"))
        while ord(chrs[i]) != 0:
            chrs.append(stream.read(1).decode("utf-8"))
            i += 1
        return "".join(chrs[:-1])
    except TypeError as e:
        # log.warning("Error in read_cstring. Nothing to read")
        return ""


def read_null_terminated_ascii(stream):
    chars = []
    while True:
        c = stream.read(1)
        if c == b'\x00' or c == b'':
            break
        chars.append(c)
    return b''.join(chars).decode('ascii')

def read_file_entry(stream):
    item_value = read_null_terminated_ascii(stream)
    len_data, = struct.unpack('<I', stream.read(4))
    data = stream.read(len_data)
    return {
        'item_value': item_value,
        'len_data': len_data,
        'data': data
    }



def read_res_sections(stream):
    sections = []
    k = 0
    while 1:
        category = read_cstring(stream)
        if(len(category) > 0):
            res_split = category.split(" ")
            cat_id = res_split[0]
            cnt = int(res_split[1])

            sections.append({})

            sections[k]["name"] = cat_id
            sections[k]["cnt"] = cnt
            sections[k]["data"] = []

            # log.info("Reading category {}".format(cat_id))
            # log.info("Element count in category is {}.".format(cnt))
            if cnt > 0:
                # log.info("Start processing...")
                res_data = []
                if cat_id in ["COLORS", "MATERIALS", "SOUNDS"]: # save only .txt
                    for i in range(cnt):
                        data = {}
                        data['row'] = read_cstring(stream)
                        res_data.append(data)

                else: #PALETTEFILES, SOUNDFILES, BACKFILES, MASKFILES, TEXTUREFILES
                    for i in range(cnt):

                        data = {}
                        data['row'] = read_cstring(stream)
                        data['size'] = struct.unpack("<i",stream.read(4))[0]
                        data['bytes'] = stream.read(data['size'])
                        res_data.append(data)

                sections[k]['data'] = res_data

            else:
                pass
                # log.info("Skip category")
            k += 1
        else:
            break
    return sections