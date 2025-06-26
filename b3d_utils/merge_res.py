import logging
import sys
import os
import fnmatch
from io import BytesIO

import parsing.read_res as res
import common as c

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("merge_res")
log.setLevel(logging.DEBUG)


def resmerge(resFromFilepath, resToFilepath, outFilepath, toReplace):
    
    res_from_parse_stream = None
    res_from_read_stream = None
    with open(resFromFilepath, 'rb') as file:
        res_from_parse_stream = BytesIO(file.read())
        res_from_read_stream = BytesIO(res_from_parse_stream.getvalue())

        
    res_into_parse_stream = None
    res_into_read_stream = None
    with open(resToFilepath, 'rb') as file:
        res_into_parse_stream = BytesIO(file.read())
        res_into_read_stream = BytesIO(res_into_parse_stream.getvalue())
        
    if not outFilepath:
        # basename, ext = os.path.splitext(resFromFilepath)
        # outFilepath = '{}_extract.{}'.format(basename, ext[1:])
        outFilepath = resToFilepath


    section = None
    outBuffer = BytesIO()

    from_sections = {
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "BACKFILES": None,
        "SOUNDFILES": None,
        "SOUNDS": None,
        "MATERIALS": None,
        "PALETTEFILES": None
    }

    into_sections = {
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "BACKFILES": None,
        "SOUNDFILES": None,
        "SOUNDS": None,
        "MATERIALS": None,
        "PALETTEFILES": None
    }

    sections = {
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "BACKFILES": None,
        "SOUNDFILES": None,
        "SOUNDS": None,
        "MATERIALS": None,
        "PALETTEFILES": None
    }

    #Reading all sections...
    while(True):
        section = res.read_section(res_from_parse_stream)
        if(not section):
            break
        
        from_sections[section['name']] = section

        
    while(True):
        section = res.read_section(res_into_parse_stream)
        if(not section):
            break
        
        into_sections[section['name']] = section

    # section aliases
    mat_from_section = from_sections["MATERIALS"]
    sounds_from_section = from_sections["SOUNDS"]
    mat_into_section = into_sections["MATERIALS"]
    sounds_into_section = into_sections["SOUNDS"]

    into_msk_cnt = into_sections['MASKFILES']['cnt'] if into_sections['MASKFILES'] is not None else 0
    into_tex_cnt = into_sections['TEXTUREFILES']['cnt'] if into_sections['TEXTUREFILES'] is not None else 0
    into_sf_cnt = into_sections['SOUNDFILES']['cnt'] if into_sections['SOUNDFILES'] is not None else 0


    # stream definitions
    mat_from_stream = BytesIO()
    from_materials = {}
    if(mat_from_section is not None):
        res_from_read_stream.seek(mat_from_section['start'], 0)
        mat_from_stream.seek(0,0)
        mat_from_stream.write(res_from_read_stream.read(mat_from_section['size']))
        
        # Parsing 'from' materials
        mat_from_stream.seek(0,0)
        from_materials = res.parse_materials(mat_from_stream, mat_from_section['cnt'])
        
    mat_into_stream = BytesIO()
    into_materials = {}
    if(mat_into_section is not None):
        res_into_read_stream.seek(mat_into_section['start'], 0)
        mat_into_stream.seek(0,0)
        mat_into_stream.write(res_into_read_stream.read(mat_into_section['size']))
        
        # Parsing 'into' materials
        mat_into_stream.seek(0,0)
        into_materials = res.parse_materials(mat_into_stream, mat_into_section['cnt'])
    
    sounds_from_stream = BytesIO()
    from_sounds = {}
    if(sounds_from_section is not None):
        res_from_read_stream.seek(sounds_from_section['start'], 0)
        sounds_from_stream.seek(0,0)
        sounds_from_stream.write(res_from_read_stream.read(sounds_from_section['size']))
        
        # Parsing 'from' sounds
        sounds_from_stream.seek(0,0)
        from_sounds = res.parse_sounds(sounds_from_stream, sounds_from_section['cnt'])
    
    sounds_into_stream = BytesIO()
    into_sounds = {}
    if(sounds_into_section is not None):
        res_into_read_stream.seek(sounds_into_section['start'], 0)
        sounds_into_stream.seek(0,0)
        sounds_into_stream.write(res_into_read_stream.read(sounds_into_section['size']))
        
        # Parsing 'into' sounds
        sounds_into_stream.seek(0,0)
        into_sounds = res.parse_sounds(sounds_into_stream, sounds_into_section['cnt'])
    
    

    from_og_tex_indexes = {f:i for i, f in enumerate(from_sections['TEXTUREFILES']['metadata_order'])}
    og_tex_indexes = {f:i for i, f in enumerate(into_sections['TEXTUREFILES']['metadata_order'])}
    if toReplace:
        for entry_name, value in from_og_tex_indexes.items():
            og_tex_indexes[entry_name] = value + into_tex_cnt
    else:
        for entry_name, value in from_og_tex_indexes.items():
            if og_tex_indexes[entry_name] is not None:
                og_tex_indexes[entry_name] = value + into_tex_cnt


    from_og_msk_indexes = {f:i for i, f in enumerate(from_sections['MASKFILES']['metadata_order'])}
    og_msk_indexes = {f:i for i, f in enumerate(into_sections['MASKFILES']['metadata_order'])}
    if toReplace:
        for entry_name, value in from_og_msk_indexes.items():
            og_msk_indexes[entry_name] = value + into_msk_cnt
    else:
        for entry_name, value in from_og_msk_indexes.items():
            if og_msk_indexes[entry_name] is not None:
                og_msk_indexes[entry_name] = value + into_msk_cnt


    from_og_sf_indexes = {f:i for i, f in enumerate(from_sections['SOUNDFILES']['metadata_order'])}
    og_sf_indexes = {f:i for i, f in enumerate(into_sections['SOUNDFILES']['metadata_order'])}
    if toReplace:
        for entry_name, value in from_og_sf_indexes.items():
            og_sf_indexes[entry_name] = value + into_sf_cnt
    else:
        for entry_name, value in from_og_sf_indexes.items():
            if og_sf_indexes[entry_name] is not None:
                og_sf_indexes[entry_name] = value + into_sf_cnt



    # Change 'from' section material indexes not to collapse with original
    # by starting counting from last 'into' section index
    for mat_name, material in from_materials.items():
        matParams = material['raw_string'].split('  ')
        if len(matParams) > 0:
            matParams[0] = ' '.join(matParams[0].split(' ')[1:]) # cut name
        else:
            matParams = [' '.join(material['raw_string'].split(' ')[1:])] # cut name



        newMatParams = []
        i = 0
        while i < len(matParams):
            paramStr = matParams[i].replace('"', '')
            paramArr = paramStr.split(' ')
            paramName = paramArr[0]
            if paramName in ['tex', 'ttx', 'itx', 'msk']:
                paramValue = int(paramArr[1])
            if (paramName in ["tex", "ttx", "itx"]):
                paramValue = paramValue + into_tex_cnt

                newMatParams.append("{} {}".format(paramName, paramValue))
            elif (paramName in ["msk"]):
                paramValue = paramValue + into_msk_cnt
                newMatParams.append("{} {}".format(paramName, paramValue))
            else: # leave as is
                newMatParams.append(matParams[i])
            i+=1
        
        newMatParam = '{} {}'.format(mat_name, '  '.join(newMatParams))

        from_materials[mat_name] = res.parse_material_params(newMatParam)

        from_materials[mat_name]['raw_string'] = newMatParam



    # Merging materials into one array
    all_materials = {}

    for mat_name, material in into_materials.items():
        all_materials[mat_name] = material
    
    if toReplace:
        for mat_name, material in from_materials.items():
            all_materials[mat_name] = material
    else:
        for mat_name, material in from_materials.items():
            if all_materials.get(mat_name) is not None:
                all_materials[mat_name] = material

        
    # Change 'from' section sound indexes not to collapse with original
    # by starting counting from last 'into' section index

    
    for sound_name, sound_idx in from_sounds.values():
        from_sounds[sound_name] = sound_idx+into_sf_cnt


    # Merging sounds into one array
    all_sounds = {}

    for sound_name, sound in into_sounds.items():
        all_sounds[sound_name] = sound
    
    if toReplace:
        for sound_name, sound in from_sounds.items():
            all_sounds[sound_name] = sound
    else:
        for sound_name, sound in from_sounds.items():
            if all_sounds.get(sound_name) is not None:
                all_sounds[sound_name] = sound


    not_indexed_sections = ["PALETTEFILES", "TEXTUREFILES", "MASKFILES", "BACKFILES", "SOUNDFILES"]

    # Join sections from 'into' and 'from' files. If toReplace is set, prioritize entries from 'from' file
    for section_name in not_indexed_sections:
        from_section = from_sections[section_name]
        into_section = into_sections[section_name]
        
        sections[section_name] = {
            "data" : {},
            "data_order": []
        }
        section = sections[section_name]['data']
        section_order = sections[section_name]['data_order']

        # merge binary data from 'into' file metadata
        if into_section:
            for entry_name, metadata in into_section['metadata'].items():
                res_into_parse_stream.seek(metadata['start'], 0)
                section[entry_name] = res_into_parse_stream.read(metadata['size'])
            
            section_order = section_order + into_section['metadata_order']
        
        # merge binary data from 'from' file metadata
        if from_section:
            if toReplace:
                # replace old entries
                for entry_name, metadata in from_section['metadata'].items():
                    res_from_read_stream.seek(metadata['start'], 0)
                    section[entry_name] = res_from_read_stream.read(metadata['size'])
            else:
                # add only new entries
                for entry_name, metadata in from_section['metadata'].items():
                    if (section.get(entry_name) is not None):
                        res_from_read_stream.seek(metadata['start'], 0)
                        section[entry_name] = res_from_read_stream.read(metadata['size'])
        
            section_order = section_order + from_section['metadata_order']
        
        # merge section data order
        sections[section_name]['data_order'] = list(set(section_order))
        
    # preparing MATERIALS section
    # changing material indexes based on current TEXTUREFILES and MASKFILES section entry order
    # print(sections['TEXTUREFILES'])
    new_tex_indexes = {f:(i+1) for i, f in enumerate(sections['TEXTUREFILES']['data_order'])}
    tex_index_mapping = {og_tex_indexes[k]: new_tex_indexes[k] for k in og_tex_indexes if k in new_tex_indexes}  

    # print(tex_index_mapping)

    new_msk_indexes = {f:(i+1) for i, f in enumerate(sections['MASKFILES']['data_order'])}
    msk_index_mapping = {og_msk_indexes[k]: new_msk_indexes[k] for k in og_msk_indexes if k in new_msk_indexes}

    for mat_name, material in all_materials.items():
        matParams = material['raw_string'].split('  ')
        if len(matParams) > 0:
            matParams[0] = ' '.join(matParams[0].split(' ')[1:]) # cut name
        else:
            matParams = [' '.join(material['raw_string'].split(' ')[1:])] # cut name

        newMatParams = []
        i = 0
        while i < len(matParams):
            paramStr = matParams[i].replace('"', '')
            paramArr = paramStr.split(' ')
            paramName = paramArr[0]
            if paramName in ['tex', 'ttx', 'itx', 'msk']:
                paramValue = int(paramArr[1])-1
            if (paramName in ["tex", "ttx", "itx"]):
                paramValue = tex_index_mapping[paramValue]
                newMatParams.append("{} {}".format(paramName, paramValue))
            elif (paramName in ["msk"]):
                paramValue = msk_index_mapping[paramValue]
                newMatParams.append("{} {}".format(paramName, paramValue))
            else: # leave as is
                newMatParams.append(matParams[i])
            i+=1
        
        newMatParam = '{} {}'.format(mat_name, '  '.join(newMatParams))
            
        all_materials[mat_name] = res.parse_material_params(newMatParam)

        all_materials[mat_name]['raw_string'] = newMatParam

    # preparing SOUNDS section
    # changing material indexes based on current SOUNDFILES section entry order

    new_sf_indexes = {f:(i+1) for i, f in enumerate(sections['SOUNDFILES']['data_order'])}
    sf_index_mapping = {og_sf_indexes[k]: new_sf_indexes[k] for k in og_sf_indexes if k in new_sf_indexes} 

    for sound_name, sound_idx in all_sounds.items():
        all_sounds[sound_name] = sf_index_mapping[sound_idx-1]+1

    # Finally, writing all sections to output:
    for section_name in not_indexed_sections:
        section = sections[section_name]
        
        entry_cnt = len(section['data'].keys())
        if entry_cnt > 0:
            c.write_cstring(outBuffer, "{} {}".format(section_name, entry_cnt))
            for entry_name in section['data_order']:
                outBuffer.write(section['data'][entry_name])
        else:
            c.write_cstring(outBuffer, "{} {}".format(section_name, 0))
    
    # and separately MATERIALS and SOUNDS
    materials_cnt = len(all_materials.keys())
    if materials_cnt > 0:
        all_materials_order = sorted(all_materials.keys())
        c.write_cstring(outBuffer, "{} {}".format("MATERIALS", materials_cnt))
        for entry_name in all_materials_order:
            c.write_cstring(outBuffer, all_materials[entry_name]["raw_string"])
    else:
       c.write_cstring(outBuffer, "{} {}".format("MATERIALS", 0))

    sounds_cnt = len(all_sounds.keys())
    if sounds_cnt > 0:
        all_sounds_order = sorted(all_sounds.keys())
        c.write_cstring(outBuffer, "{} {}".format("SOUNDS", sounds_cnt))
        for entry_name in all_sounds_order:
            c.write_cstring(outBuffer, "{} {}".format(entry_name, all_sounds[entry_name]))
    else:
       c.write_cstring(outBuffer, "{} {}".format("SOUNDS", 0))

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())
    

