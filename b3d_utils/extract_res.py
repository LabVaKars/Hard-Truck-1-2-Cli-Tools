import logging
import sys
import os
import fnmatch
from io import BytesIO

import parsing.read_res as res

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("extract_res")
log.setLevel(logging.DEBUG)

def write_cstring(stream, txt):
    if txt[-1] != "\00":
        txt += "\00"
    stream.write(txt.encode("utf8"))


def resextract(resFilepath, outFilepath, selected_sections, section_records):
    
    parse_stream = None
    read_from_stream = None
    with open(resFilepath, 'rb') as file:
        parse_stream = BytesIO(file.read())
        read_from_stream = BytesIO(parse_stream.getvalue())

    if not outFilepath:
        basename, ext = os.path.splitext(resFilepath)
        outFilepath = '{}_extract.{}'.format(basename, ext[1:])
    
    section = None
    outBuffer = BytesIO()
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
        section = res.read_section(parse_stream)
        if(not section):
            break
        
        sections[section['name']] = section

    sounds_section = sections["SOUNDS"]
    sf_section = sections["SOUNDFILES"]
    mat_section = sections["MATERIALS"]
    tex_section = sections["TEXTUREFILES"]
    msk_section = sections["MASKFILES"]

    sounds_stream = BytesIO()
    if(sounds_section is not None):
        read_from_stream.seek(sounds_section['start'], 0)
        sounds_stream.seek(0,0)
        sounds_stream.write(read_from_stream.read(sounds_section['size']))

    mat_stream = BytesIO()
    if(mat_section is not None):
        read_from_stream.seek(mat_section['start'], 0)
        mat_stream.seek(0,0)
        mat_stream.write(read_from_stream.read(mat_section['size']))

    #Parsing only referenced in res file resources 
    if section_records['SOUNDFILES'] == 'REF': #extract only objects referenced in this res-file
        sounds_stream.seek(0,0)
        sounds = res.parse_sounds(sounds_stream, sounds_section['cnt'])
        sf_indexes = [int(ind)-1 for ind in sounds.values()]
        
        sf_names = sf_section['metadata_order']
        used_names = [sf_names[i] for i in sf_indexes]
        section_records['SOUNDFILES'] = used_names


    if section_records['TEXTUREFILES'] == 'REF':
        mat_stream.seek(0,0)
        materials = res.parse_materials(mat_stream, mat_section['cnt'])
        tex_indexes = set((int(mat.get('tex'))-1 for mat in materials.values() if mat.get("tex") is not None)) \
                    | set((int(mat.get('ttx'))-1 for mat in materials.values() if mat.get("ttx") is not None)) \
                    | set((int(mat.get('itx'))-1 for mat in materials.values() if mat.get("itx") is not None))
        tex_names = tex_section['metadata_order']
        used_names = [tex_names[i] for i in tex_indexes]
        section_records['TEXTUREFILES'] = used_names
    

    if section_records['MASKFILES'] == 'REF':
        mat_stream.seek(0,0)
        materials = res.parse_materials(mat_stream, mat_section['cnt'])
        msk_indexes = set((int(mat.get("msk"))-1 for mat in materials.values() if mat.get("msk")))
        msk_names = msk_section['metadata_order']
        used_names = [msk_names[i] for i in msk_indexes]
        section_records['MASKFILES'] = used_names
        
    # then processing
    processing_order = ["PALETTEFILES", "TEXTUREFILES", "MASKFILES", "BACKFILES", "MATERIALS", "SOUNDFILES", "SOUNDS"]

    matching_records = {
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "SOUNDFILES": None
    }

    for section_name in processing_order:
        section = sections.get(section_name)

        if(section is not None and section['name'] in selected_sections):
            log.debug('{}: {}'.format(section['name'], section['cnt']))
            sectionBuffer = BytesIO()
            sectionDataBuffer = BytesIO()
            
            #extract separate records
            if(section_records[section['name']]): 
                cnt = 0
                #checking for wildcards
                matching_names = [f 
                    for f in section['metadata'].keys() #all imported names
                    if any(fnmatch.fnmatch(f, pattern) 
                        for pattern in section_records[section['name']]) #user defined wildcards or just names
                ]

                if section['name'] in ["TEXTUREFILES", "MASKFILES", "SOUNDFILES"]:
                    matching_records[section['name']] = matching_names #for replacing indexes in MATERIALS and SOUNDS

                for record_name in matching_names:
                    cnt+=1
                    metadata = section['metadata'].get(record_name)
                    read_from_stream.seek(metadata['start'], 0)
                    sectionDataBuffer.write(read_from_stream.read(metadata['size']))
                
                write_cstring(sectionBuffer, '{} {}'.format(section['name'], cnt))
                sectionBuffer.write(sectionDataBuffer.getvalue())
            
            elif section['name'] in ["MATERIALS"] \
            and (section_records['TEXTUREFILES'] is not None \
            or section_records['MASKFILES'] is not None):
                ignore_tex = section_records['TEXTUREFILES'] is None
                ignore_msk = section_records['MASKFILES'] is None

                mat_stream.seek(0,0)
                new_materials = res.parse_materials(mat_stream, mat_section['cnt'])
                
                if(not ignore_tex):
                    og_tex_indexes = {f:i for i, f in enumerate(tex_section['metadata_order'])}
                    new_tex_indexes = {f:(i+1) for i, f in enumerate(matching_records['TEXTUREFILES'])}
                    tex_index_mapping = {og_tex_indexes[k]: new_tex_indexes[k] for k in og_tex_indexes if k in new_tex_indexes}            
                    
                if(not ignore_msk):
                    og_msk_indexes = {f:i for i, f in enumerate(msk_section['metadata_order'])}
                    new_msk_indexes = {f:(i+1) for i, f in enumerate(matching_records['MASKFILES'])}
                    msk_index_mapping = {og_msk_indexes[k]: new_msk_indexes[k] for k in og_msk_indexes if k in new_msk_indexes}

                for mat_name in new_materials:
                    cnt+=1
                    mat = new_materials[mat_name]
                    matParams = mat['raw_string'].split('  ')
                    if len(matParams) > 0:
                        matParams[0] = ' '.join(matParams[0].split(' ')[1:]) # cut name
                    else:
                        matParams = [' '.join(mat['raw_string'].split(' ')[1:])] # cut name

                    newMatParams = []
                    i = 0
                    while i < len(matParams):
                        paramStr = matParams[i].replace('"', '')
                        paramArr = paramStr.split(' ')
                        paramName = paramArr[0]
                        if paramName in ['tex', 'ttx', 'itx', 'msk']:
                            paramValue = int(paramArr[1])-1
                        if (paramName in ["tex", "ttx", "itx"] and not ignore_tex):
                            paramValue = tex_index_mapping[paramValue]
                            newMatParams.append("{} {}".format(paramName, paramValue))
                        elif (paramName in ["msk"] and not ignore_msk):
                            paramValue = msk_index_mapping[paramValue]
                            newMatParams.append("{} {}".format(paramName, paramValue))
                        else: # leave as is
                            newMatParams.append(matParams[i])
                        i+=1
                    
                    newParamsStr = '{} {}'.format(mat_name, '  '.join(newMatParams))
                    
                    write_cstring(sectionDataBuffer, newParamsStr)
            
                write_cstring(sectionBuffer, '{} {}'.format('MATERIALS', len(new_materials)))
                sectionBuffer.write(sectionDataBuffer.getvalue())
                
            elif section['name'] in ["SOUNDS"] \
            and (section_records['SOUNDFILES'] is not None):
                sounds_stream.seek(0,0)
                new_sounds = res.parse_sounds(sounds_stream, sounds_section['cnt'])

                og_sf_indexes = {f:i for i, f in enumerate(sf_section['metadata_order'])}
                new_sf_indexes = {f:(i+1) for i, f in enumerate(matching_records['SOUNDFILES'])}
                sf_index_mapping = {og_sf_indexes[k]: new_sf_indexes[k] for k in og_sf_indexes if k in new_sf_indexes}

                for sound_idx in new_sounds.values():
                    cnt+=1
                    newSoundsStr = '{} {}'.format(record_name, sf_index_mapping[sound_idx-1]+1)
                    write_cstring(sectionDataBuffer, newSoundsStr)
                
                write_cstring(sectionBuffer, '{} {}'.format('SOUNDS', cnt))
                sectionBuffer.write(sectionDataBuffer.getvalue())


            else:
                #extract whole section
                sectionBuffer = BytesIO()
                write_cstring(sectionBuffer, '{} {}'.format(section['name'], section['cnt']))
                read_from_stream.seek(section['start'], 0)
                sectionBuffer.write(read_from_stream.read(section['size']))

            outBuffer.write(sectionBuffer.getvalue())
        
        else:     
            write_cstring(outBuffer, '{} {}'.format(section_name, 0))

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())