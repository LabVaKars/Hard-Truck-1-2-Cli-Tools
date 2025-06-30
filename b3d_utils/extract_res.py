import logging
import sys
import os
import fnmatch
from io import BytesIO

import parsing.read_res as res
import common as c

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("extract_res")
log.setLevel(logging.DEBUG)



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

    # then processing
    processing_order = ["PALETTEFILES", "TEXTUREFILES", "MASKFILES", "BACKFILES", "MATERIALS", "SOUNDFILES", "SOUNDS"]

    matching_records = {
        "PALETTEFILES": None,
        "BACKFILES": None,
        "MATERIALS": None,
        "SOUNDS": None,
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "SOUNDFILES": None
    }

    # filter mathing records based on wildcards
    for section_name in processing_order:
        section = sections.get(section_name)

        if(section is not None and section['name'] in selected_sections):
            #extract separate records
            if(section_records[section['name']]): 
                cnt = 0
                #checking for wildcards
                matching_names = [f 
                    for f in section['metadata'].keys() #all imported names
                    if any(fnmatch.fnmatch(f, pattern) 
                        for pattern in section_records[section['name']]) #user defined wildcards or just names
                ]

                if section['name'] in ["MATERIALS", "SOUNDS", "TEXTUREFILES", "MASKFILES", "SOUNDFILES"]:
                    matching_records[section['name']] = matching_names #for replacing indexes in MATERIALS and SOUNDS


    #Parsing only referenced in res file resources 
    if section_records['SOUNDFILES'] == 'REF': #extract only objects referenced in this res-file
        sounds_stream.seek(0,0)
        sounds = res.parse_sounds(sounds_stream, sounds_section['cnt'])
        if (matching_records["SOUNDS"] is not None and len(matching_records["SOUNDS"]) > 0): 
            sounds = {mat_name:sounds[mat_name] for mat_name in matching_records["SOUNDS"]}
        sf_indexes = [int(ind)-1 for ind in sounds.values()]
        
        sf_names = sf_section['metadata_order']
        used_names = [sf_names[i] for i in sf_indexes]
        matching_records['SOUNDFILES'] = used_names
    elif section_records['SOUNDFILES'] is None:
        matching_records['SOUNDFILES'] = sf_section['metadata_order']

    mat_stream.seek(0,0)
    materials = res.parse_materials(mat_stream, mat_section['cnt'])
    if (matching_records["MATERIALS"] is not None and len(matching_records["MATERIALS"]) > 0):
        new_matching_records = set(matching_records["MATERIALS"])
        par_references = {}
        mat_order = mat_section['metadata_order']
        for mat_name, mat in materials.items():
            par_idx = res.get_par(mat)
            if par_idx > -1:
                # print(mat_name)
                if par_references.get(mat_name) is None:
                    par_references[mat_name] = []
                par_references[mat_name].append(mat_order[par_idx-1])
        
        stack = list(matching_records["MATERIALS"])
        
        while stack:
            mat_name = stack.pop()
            if par_references.get(mat_name) is not None:
                stack = stack + par_references[mat_name]
                new_matching_records |= set(par_references[mat_name])
            
        matching_records["MATERIALS"] = sorted(list(new_matching_records))
            
        materials = {mat_name:materials[mat_name] for mat_name in matching_records["MATERIALS"]}


    if section_records['TEXTUREFILES'] == 'REF':
        tex_indexes = set((int(res.get_tex(mat))-1 for mat in materials.values() if res.get_tex(mat)>-1)) \
                    | set((int(res.get_ttx(mat))-1 for mat in materials.values() if res.get_ttx(mat)>-1)) \
                    | set((int(res.get_itx(mat))-1 for mat in materials.values() if res.get_itx(mat)>-1))
        tex_names = tex_section['metadata_order']
        used_names = [tex_names[i] for i in tex_indexes]
        matching_records['TEXTUREFILES'] = used_names
    elif section_records['TEXTUREFILES'] is None:
        matching_records['TEXTUREFILES'] = tex_section['metadata_order']
    

    if section_records['MASKFILES'] == 'REF':
        msk_indexes = set((int(res.get_msk(mat))-1 for mat in materials.values() if res.get_msk(mat)>-1))
        msk_names = msk_section['metadata_order']
        used_names = [msk_names[i] for i in msk_indexes]
        matching_records['MASKFILES'] = used_names
    elif section_records['MASKFILES'] is None:
        matching_records['MASKFILES'] = msk_section['metadata_order']

    # Processing sections data
    for section_name in processing_order:
        section = sections.get(section_name)

        if(section is not None and section['name'] in selected_sections):
            # log.debug('{}: {}'.format(section['name'], section['cnt']))
            sectionBuffer = BytesIO()
            sectionDataBuffer = BytesIO()
            
            #extract separate records

            if section['name'] not in ["SOUNDS", "MATERIALS"]: #sections with replaceable indexes are processed lower
                if(matching_records[section['name']]): 
                    cnt = 0
                    matching_names = matching_records[section['name']]
                    for record_name in matching_names:
                        cnt+=1
                        metadata = section['metadata'].get(record_name)
                        read_from_stream.seek(metadata['start'], 0)
                        sectionDataBuffer.write(read_from_stream.read(metadata['size']))

                    c.write_cstring(sectionBuffer, '{} {}'.format(section['name'], cnt))
                    sectionBuffer.write(sectionDataBuffer.getvalue())
                else:
                    c.write_cstring(sectionBuffer, '{} {}'.format(section['name'], 0))

            
            elif section['name'] in ["MATERIALS"] \
            and (matching_records['TEXTUREFILES'] is not None \
            or matching_records['MASKFILES'] is not None):
                ignore_tex = matching_records['TEXTUREFILES'] is None
                ignore_msk = matching_records['MASKFILES'] is None

                og_mat_indexes = {f:i for i, f in enumerate(mat_section['metadata_order'])}
                new_mat_indexes = {f:(i+1) for i, f in enumerate(matching_records['MATERIALS'])}
                mat_index_mapping = {og_mat_indexes[k]: new_mat_indexes[k] for k in og_mat_indexes if k in new_mat_indexes}            

                if(not ignore_tex):
                    og_tex_indexes = {f:i for i, f in enumerate(tex_section['metadata_order'])}
                    new_tex_indexes = {f:(i+1) for i, f in enumerate(matching_records['TEXTUREFILES'])}
                    tex_index_mapping = {og_tex_indexes[k]: new_tex_indexes[k] for k in og_tex_indexes if k in new_tex_indexes}            
                    
                if(not ignore_msk):
                    og_msk_indexes = {f:i for i, f in enumerate(msk_section['metadata_order'])}
                    new_msk_indexes = {f:(i+1) for i, f in enumerate(matching_records['MASKFILES'])}
                    msk_index_mapping = {og_msk_indexes[k]: new_msk_indexes[k] for k in og_msk_indexes if k in new_msk_indexes}

                for mat_name, mat in materials.items():
                    cnt+=1
                    # mat = materials[mat_name]

                    par = res.get_par(mat)
                    if par > -1:
                        res.set_par(mat, mat_index_mapping[par-1])
                    if not ignore_tex:
                        tex = res.get_tex(mat)
                        ttx = res.get_ttx(mat)
                        itx = res.get_itx(mat)
                        if tex > -1:
                            res.set_tex(mat, tex_index_mapping[tex-1])
                        if ttx > -1:
                            res.set_ttx(mat, tex_index_mapping[ttx-1])
                        if itx > -1:
                            res.set_itx(mat, tex_index_mapping[itx-1])
                    if not ignore_msk:
                        msk = res.get_msk(mat)
                        if msk > -1:
                            res.set_msk(mat, msk_index_mapping[msk-1])

                    newParamsStr = "{} {}".format(mat_name, res.get_mat_string(mat))
                    
                    c.write_cstring(sectionDataBuffer, newParamsStr)
            
                c.write_cstring(sectionBuffer, '{} {}'.format('MATERIALS', len(materials)))
                sectionBuffer.write(sectionDataBuffer.getvalue())

                if(matching_records['TEXTUREFILES'] is None):
                    c.write_cstring(sectionBuffer, '{} {}'.format('TEXTUREFILES', 0))

                if(matching_records['MASKFILES'] is None):
                    c.write_cstring(sectionBuffer, '{} {}'.format('MASKFILES', 0))

                
            elif section['name'] in ["SOUNDS"] \
            and (matching_records['SOUNDFILES'] is not None):
                sounds_stream.seek(0,0)
                new_sounds = res.parse_sounds(sounds_stream, sounds_section['cnt'])

                og_sf_indexes = {f:i for i, f in enumerate(sf_section['metadata_order'])}
                new_sf_indexes = {f:(i+1) for i, f in enumerate(matching_records['SOUNDFILES'])}
                sf_index_mapping = {og_sf_indexes[k]: new_sf_indexes[k] for k in og_sf_indexes if k in new_sf_indexes}

                for sound_idx in new_sounds.values():
                    cnt+=1
                    newSoundsStr = '{} {}'.format(record_name, sf_index_mapping[sound_idx-1]+1)
                    c.write_cstring(sectionDataBuffer, newSoundsStr)
                
                c.write_cstring(sectionBuffer, '{} {}'.format('SOUNDS', cnt))
                sectionBuffer.write(sectionDataBuffer.getvalue())


            else:
                #extract whole section
                sectionBuffer = BytesIO()
                c.write_cstring(sectionBuffer, '{} {}'.format(section['name'], section['cnt']))
                read_from_stream.seek(section['start'], 0)
                sectionBuffer.write(read_from_stream.read(section['size']))

            outBuffer.write(sectionBuffer.getvalue())
        
        else:     
            c.write_cstring(outBuffer, '{} {}'.format(section_name, 0))

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())