import struct
import fnmatch
import os
from pathlib import Path
from io import BytesIO

import parsing.read_b3d as b3dr
import parsing.read_res as res

from consts import SECTIONS

class Graph:

    def __init__(self, graph):
        self.graph = graph

    def DFSUtil(self, val, visited):

        visited[val]["in"] += 1
        for v in self.graph[val]:
            if self.graph.get(v) is not None:
                visited[val]["out"] += 1
                self.DFSUtil(v, visited)

    def DFS(self, start=None):
        V = len(self.graph)  #total vertices

        visited = {}
        for val in self.graph.keys():
            visited[val] = {
                "in": 0,
                "out": 0
            }

        searchIn = []
        if start is not None:
            searchIn.append(start.name)
        else:
            searchIn = self.graph.keys()

        for val in searchIn:
            for v in self.graph[val]:
                if self.graph.get(v) is not None:
                    visited[val]["out"] += 1
                    self.DFSUtil(v, visited)

        return visited

def unmask_template(templ):
    offset = 0
    unmasks = []
    t_a = int(templ[0])
    t_r = int(templ[1])
    t_g = int(templ[2])
    t_b = int(templ[3])
    total_bytes = t_r + t_g + t_b + t_a
    for i in range(4):
        cur_int = int(templ[i])
        lzeros = offset
        bits = cur_int
        rzeros = total_bytes - lzeros - bits
        unmasks.append([lzeros, bits, rzeros])
        offset += cur_int
    return unmasks

class BitMask:
    def __init__(self):
        self.lzeros = 0
        self.ones = 0
        self.rzeros = 0

def unmask_bits(num, bytes_cnt=2):
    bits = [int(digit) for digit in bin(num)[2:]]
    bitmask = BitMask()
    if num == 0:
        return bitmask
    for bit in bits:
        if bit:
            bitmask.ones+=1
        else:
            bitmask.rzeros+=1
        bitmask.lzeros = bytes_cnt*8 - len(bits)
    return bitmask

def getHierarchyRoots(refObjs):

    graph = {}
    for key in refObjs.keys():
        graph[key] = [cn['add_name'] for cn in refObjs[key]]

    zgraph = Graph(graph)
    visited = zgraph.DFS()
    roots = [cn for cn in visited.keys() if (visited[cn]["in"] == 0) and (visited[cn]["out"] > 0)]

    return roots

SECTIONS = ["PALETTEFILES", "SOUNDFILES", "BACKFILES", "MASKFILES", "TEXTUREFILES", "COLORS", "MATERIALS", "SOUNDS"]

def get_res_params(
    sections, 
    inc_soundfiles, ref_soundfiles, 
    inc_backfiles,
    inc_maskfiles, ref_maskfiles, 
    inc_texturefiles, ref_texturefiles, 
    inc_materials,
    inc_sounds
):
    current_sections = None
    if(sections):
        current_sections = sections
    else:
        current_sections = SECTIONS

    section_records = {
        "SOUNDFILES": "REF" if ref_soundfiles else inc_soundfiles,
        "BACKFILES": inc_backfiles,
        "MASKFILES": "REF" if ref_maskfiles else inc_maskfiles,
        "TEXTUREFILES": "REF" if ref_texturefiles else inc_texturefiles,
        "MATERIALS": inc_materials,
        "SOUNDS": inc_sounds,
        "PALETTEFILES": None
    }

    return {
        "current_sections": current_sections,
        "section_records": section_records
    }


def write_cstring(stream, txt):
    if txt[-1] != "\00":
        txt += "\00"
    stream.write(txt.encode("utf8"))

    
def reserve_size_byte(io):
    pos = io.tell()
    io.write(struct.pack("<i",0))
    return pos

def write_size(io, ms, size):
    end_ms = io.tell()
    io.seek(ms, 0)
    io.write(struct.pack("<i", size))
    io.seek(end_ms, 0)

    
def write_output_b3d(all_roots, all_roots_order, material_list):
    outBuffer = BytesIO()
    
    outBuffer.write(b'b3d\x00')
    ms_file_size = reserve_size_byte(outBuffer)
    ms_materials = reserve_size_byte(outBuffer)
    ms_materials_size = reserve_size_byte(outBuffer)
    ms_nodes = reserve_size_byte(outBuffer)
    ms_nodes_size = reserve_size_byte(outBuffer)

    cp_materials = int(outBuffer.tell()/4)

    outBuffer.write(struct.pack("<i", len(material_list))) #Material count
    for mat_name in material_list:
        b3dr.write_name(outBuffer, mat_name)
        
    cp_nodes = int(outBuffer.tell()/4)
    
    outBuffer.write(b'\x4D\x01\x00\x00') #BeginChunks
    
    for root_name in all_roots_order:
        root = all_roots[root_name]
        temp = root["data"].getvalue()
        outBuffer.write(temp)

    outBuffer.write(b'\xde\x00\00\00') #EndChunks

    cp_eof = int(outBuffer.tell()/4)

    write_size(outBuffer, ms_file_size, cp_eof)
    write_size(outBuffer, ms_materials, cp_materials)
    write_size(outBuffer, ms_materials_size, cp_nodes - cp_materials)
    write_size(outBuffer, ms_nodes, cp_nodes)
    write_size(outBuffer, ms_nodes_size, cp_eof - cp_nodes)

    return outBuffer

def create_missing_folders(filepath):
    binfile_base = os.path.dirname(filepath)
    if not os.path.exists(binfile_base):
        binfile_base = Path(binfile_base)
        binfile_base.mkdir(exist_ok=True, parents=True)

def write_debug_tga(sectionFolder, filepath, debug_data):
    no_ext = os.path.splitext(filepath)[0]
    debugFolder = os.path.join(sectionFolder, "debug")
    
    if not os.path.exists(debugFolder):
        os.makedirs(debugFolder)
    filename = os.path.join(debugFolder, "{}.tga".format(no_ext))
    
    create_missing_folders(filename)
    with open(filename, 'wb') as file:
        file.write(debug_data.getvalue())

def write_matching_records(read_from_stream, selected_sections, section_records, toReverse):
    section = None
    outBuffer = BytesIO()
    if len(selected_sections) == 0:
        selected_sections = SECTIONS

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
        section = res.read_section(read_from_stream)
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

    out_records = {
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
            matched_sounds = {mat_name:sounds[mat_name] for mat_name in matching_records["SOUNDS"]}
        sf_indexes = [int(ind)-1 for ind in matched_sounds.values()]
        
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
            
        matching_materials = {mat_name:materials[mat_name] for mat_name in matching_records["MATERIALS"]}


    if section_records['TEXTUREFILES'] == 'REF':
        tex_indexes = set((int(res.get_tex(mat))-1 for mat in matching_materials.values() if res.get_tex(mat)>-1)) \
                    | set((int(res.get_ttx(mat))-1 for mat in matching_materials.values() if res.get_ttx(mat)>-1)) \
                    | set((int(res.get_itx(mat))-1 for mat in matching_materials.values() if res.get_itx(mat)>-1))
        tex_names = tex_section['metadata_order']
        used_names = [tex_names[i] for i in tex_indexes]
        matching_records['TEXTUREFILES'] = used_names
    elif section_records['TEXTUREFILES'] is None:
        matching_records['TEXTUREFILES'] = tex_section['metadata_order']
    

    if section_records['MASKFILES'] == 'REF':
        msk_indexes = set((int(res.get_msk(mat))-1 for mat in matching_materials.values() if res.get_msk(mat)>-1))
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
                # print(section['metadata_order'])
                if len(section['metadata_order']) > 0:
                    if toReverse:
                        out_records[section['name']] = [r for r in section['metadata_order'] if r not in matching_records[section['name']]]
                    else:
                        out_records[section['name']] = matching_records[section['name']]

                    if(out_records[section['name']]): 
                    
                        matching_names = out_records[section['name']]
                        for record_name in matching_names:
                            metadata = section['metadata'].get(record_name)
                            read_from_stream.seek(metadata['start'], 0)
                            sectionDataBuffer.write(read_from_stream.read(metadata['size']))

                        write_cstring(sectionBuffer, '{} {}'.format(section['name'], len(matching_names)))
                        sectionBuffer.write(sectionDataBuffer.getvalue())
                    else:
                        write_cstring(sectionBuffer, '{} {}'.format(section['name'], 0))
                else:
                    write_cstring(sectionBuffer, '{} {}'.format(section['name'], 0))


            
            elif section['name'] in ["MATERIALS"]:
                if toReverse:
                    out_records['TEXTUREFILES'] = [r for r in sections['TEXTUREFILES']['metadata_order'] if r not in matching_records['TEXTUREFILES']]
                else:
                    out_records['TEXTUREFILES'] = matching_records['TEXTUREFILES']
                
                if toReverse:
                    out_records['MASKFILES'] = [r for r in sections['MASKFILES']['metadata_order'] if r not in matching_records['MASKFILES']]
                else:
                    out_records['MASKFILES'] = matching_records['MASKFILES']
                
                if toReverse:
                    out_records['MATERIALS'] = [r for r in section['metadata_order'] if r not in matching_records['MATERIALS']]
                    matching_materials = {mat_name:materials[mat_name] for mat_name in out_records["MATERIALS"]}
                    #Additional check to remove materials that lost Texturefile or Maskfile reference
                    idx_to_tex = {i:f for i, f in enumerate(tex_section['metadata_order'])}
                    idx_to_msk = {i:f for i, f in enumerate(msk_section['metadata_order'])}
                    matching_materials = {mat_name:mat_obj for mat_name, mat_obj in matching_materials.items() \
                        if (res.get_tex(mat_obj) > -1 and idx_to_tex[res.get_tex(mat_obj)] in out_records['TEXTUREFILES'] \
                        or res.get_ttx(mat_obj) > -1 and idx_to_tex[res.get_ttx(mat_obj)] in out_records['TEXTUREFILES'] \
                        or res.get_itx(mat_obj) > -1 and idx_to_tex[res.get_itx(mat_obj)] in out_records['TEXTUREFILES'] \
                        or res.get_msk(mat_obj) > -1 and idx_to_msk[res.get_msk(mat_obj)] in out_records['MASKFILES'])} 
                    #TODO: maybe add check for missing parent material
                else:
                    out_records['MATERIALS'] = matching_records['MATERIALS']
                
                ignore_tex = out_records['TEXTUREFILES'] is None
                ignore_msk = out_records['MASKFILES'] is None

                og_mat_indexes = {f:i for i, f in enumerate(mat_section['metadata_order'])}
                new_mat_indexes = {f:(i+1) for i, f in enumerate(out_records['MATERIALS'])}
                mat_index_mapping = {og_mat_indexes[k]: new_mat_indexes[k] for k in og_mat_indexes if k in new_mat_indexes}            
                
                # print(og_mat_indexes)
                # print(new_mat_indexes)
                # print(mat_index_mapping)

                if(not ignore_tex):
                    og_tex_indexes = {f:i for i, f in enumerate(tex_section['metadata_order'])}
                    new_tex_indexes = {f:(i+1) for i, f in enumerate(out_records['TEXTUREFILES'])}
                    tex_index_mapping = {og_tex_indexes[k]: new_tex_indexes[k] for k in og_tex_indexes if k in new_tex_indexes}            
                    print(og_tex_indexes)
                    print(new_tex_indexes)
                    print(tex_index_mapping)
                    
                if(not ignore_msk):
                    og_msk_indexes = {f:i for i, f in enumerate(msk_section['metadata_order'])}
                    new_msk_indexes = {f:(i+1) for i, f in enumerate(out_records['MASKFILES'])}
                    msk_index_mapping = {og_msk_indexes[k]: new_msk_indexes[k] for k in og_msk_indexes if k in new_msk_indexes}

                for mat_name, mat in matching_materials.items():
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
                    
                    write_cstring(sectionDataBuffer, newParamsStr)
            
                write_cstring(sectionBuffer, '{} {}'.format('MATERIALS', len(matching_materials)))
                sectionBuffer.write(sectionDataBuffer.getvalue())

                if(out_records['TEXTUREFILES'] is None):
                    write_cstring(sectionBuffer, '{} {}'.format('TEXTUREFILES', 0))

                if(out_records['MASKFILES'] is None):
                    write_cstring(sectionBuffer, '{} {}'.format('MASKFILES', 0))

                
            elif section['name'] in ["SOUNDS"]:
                if toReverse:
                    out_records['SOUNDS'] = [r for r in section['metadata_order'] if r not in matching_records['SOUNDS']]
                    matching_sounds = {snd_name:sounds[snd_name] for snd_name in out_records["SOUNDS"]}
                    #Additional check to remove sounds that lost Soundfiles reference
                    matching_sounds = {snd_name:snd_num for snd_name, snd_num in matching_sounds.items() \
                                        if (snd_name in out_records['SOUNDFILES'])} 
                else:
                    out_records['SOUNDS'] = matching_records['SOUNDS']
                
                if(out_records[section['name']]): 

                    og_sf_indexes = {f:i for i, f in enumerate(sf_section['metadata_order'])}
                    new_sf_indexes = {f:(i+1) for i, f in enumerate(out_records['SOUNDFILES'])}
                    sf_index_mapping = {og_sf_indexes[k]: new_sf_indexes[k] for k in og_sf_indexes if k in new_sf_indexes}

                    for sound_idx in matching_sounds.values():
                        newSoundsStr = '{} {}'.format(record_name, sf_index_mapping[sound_idx-1]+1)
                        write_cstring(sectionDataBuffer, newSoundsStr)
                    
                    write_cstring(sectionBuffer, '{} {}'.format('SOUNDS', len(matching_sounds)))
                    sectionBuffer.write(sectionDataBuffer.getvalue())
                else:
                    write_cstring(sectionBuffer, '{} {}'.format('SOUNDS', 0))


            else:
                #extract whole section
                sectionBuffer = BytesIO()
                write_cstring(sectionBuffer, '{} {}'.format(section['name'], section['cnt']))
                read_from_stream.seek(section['start'], 0)
                sectionBuffer.write(read_from_stream.read(section['size']))

            outBuffer.write(sectionBuffer.getvalue())
        
        else:     
            write_cstring(outBuffer, '{} {}'.format(section_name, 0))
    
    return outBuffer