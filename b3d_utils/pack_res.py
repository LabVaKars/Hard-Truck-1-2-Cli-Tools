import sys
import logging
import os
import json
import struct

from io import BytesIO
from pathlib import Path

import parsing.read_res as res
import imghelp as img
import common as c

from consts import SECTIONS

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("pack_res")
log.setLevel(logging.DEBUG)



def respack(resDirpath, outFilepath, tgaDebug):
    # read_from_stream = None
    # with open(resFilepath, 'rb') as file:
    #     read_from_stream = BytesIO(file.read())

    # resFilename = os.path.splitext(os.path.basename(resFilepath))[0]

    sections = {
        "PALETTEFILES": None,
        "SOUNDFILES": None,
        "BACKFILES": None,
        "MASKFILES": None,
        "TEXTUREFILES": None,
        "COLORS": None,
        "MATERIALS": None,
        "SOUNDS": None
    }
     
    out_sections = {
        "TEXTUREFILES": None,
        "MASKFILES": None,
        "BACKFILES": None,
        "SOUNDFILES": None,
        "SOUNDS": None,
        "MATERIALS": None,
        "PALETTEFILES": None,
        "COLORS": None
    }

    outBuffer = BytesIO()    

    for section_name, section in sections.items():
        sectionFolder = os.path.join(resDirpath, section_name)
        if os.path.exists(sectionFolder):
            sectionMetadata = os.path.join(sectionFolder, '{}.txt'.format(section_name))
            if os.path.exists(sectionMetadata):
                section_meta = None
                with open(sectionMetadata, 'rb') as file:
                    section_meta = json.loads(file.read().decode('utf-8'))
                cur_section = out_sections[section_name]
                if section_name in ["SOUNDFILES", "PALETTEFILES"]:
                    cur_section = {}
                    for entry_key, entry_value in section_meta.items():
                        entryBuffer = BytesIO()
                        filename = os.path.join(sectionFolder, entry_key)
                        with open(filename, 'rb') as file:
                            entryBuffer = BytesIO(file.read())
                            cur_section[entry_key] = entryBuffer
                    
                    c.write_cstring(outBuffer, "{} {}".format(section_name, len(cur_section.keys())))
                    for entry_key, entry_value in cur_section.items():
                        c.write_cstring(outBuffer, entry_key)
                        val = entry_value.getvalue()
                        val_size = len(val)
                        outBuffer.write(struct.pack('<I', val_size))
                        outBuffer.write(val)
                
                elif section_name in ["COLORS"]:
                    c.write_cstring(outBuffer, "{} {}".format(section_name, len(section_meta)))
                    for color in section_meta: #array
                        c.write_cstring(outBuffer, color)
                
                elif section_name in ["MATERIALS", "SOUNDS"]:
                    c.write_cstring(outBuffer, "{} {}".format(section_name, len(section_meta)))
                    for key, value in section_meta.items(): #array
                        c.write_cstring(outBuffer, "{} {}".format(key, value))
                        
                elif section_name in ["MASKFILES"]:
                    cur_section = {}
                    cur_section_params = {}
                    for entry_key, entry_value in section_meta.items():
                        entryBuffer = BytesIO()
                        log.info(entry_key)
                        noExtPath = os.path.splitext(entry_key)[0]
                        filename = os.path.join(sectionFolder, "{}.tga".format(noExtPath))
                        with open(filename, 'rb') as file:
                            entryBuffer = BytesIO(file.read())
                        
                        msk_params = parse_msk_params(entry_value)

                        result = img.tga32_to_msk(entryBuffer, msk_params, tgaDebug)

                        if result['debug_data'] is not None:
                            c.write_debug_tga(sectionFolder, noExtPath, result['debug_data'])

                        cur_section[entry_key] = result["data"]
                        cur_section_params[entry_key] = msk_params
                    
                    c.write_cstring(outBuffer, "{} {}".format(section_name, len(cur_section.keys())))
                    for entry_key, entry_value in cur_section.items():
                        params = cur_section_params[entry_key]
                        if len(params['other']) > 0:
                            params_str = " ".join(params['other'])
                            c.write_cstring(outBuffer, "{} {}".format(entry_key, params_str))
                        else:
                            c.write_cstring(outBuffer, entry_key)
                        val = entry_value.getvalue()
                        val_size = len(val)
                        outBuffer.write(struct.pack('<I', val_size))
                        outBuffer.write(val)
                
                elif section_name in ["TEXTUREFILES"]:
                    cur_section = {}
                    cur_section_params = {}
                    for entry_key, entry_value in section_meta.items():
                        entryBuffer = BytesIO()
                        noExtPath = os.path.splitext(entry_key)[0]
                        filename = os.path.join(sectionFolder, "{}.tga".format(noExtPath))
                        with open(filename, 'rb') as file:
                            entryBuffer = BytesIO(file.read())
                        
                        tex_params = parse_tex_params(entry_value)

                        result = img.convert_tga32_to_txr(entryBuffer, tex_params, tgaDebug)
                        
                        if result['debug_data'] is not None:
                            c.write_debug_tga(sectionFolder, noExtPath, result['debug_data'])
                        
                        cur_section[entry_key] = result["data"]
                        cur_section_params[entry_key] = tex_params
                    
                    c.write_cstring(outBuffer, "{} {}".format(section_name, len(cur_section.keys())))
                    for entry_key, entry_value in cur_section.items():
                        params = cur_section_params[entry_key]
                        if len(params['other']) > 0:
                            params_str = " ".join(params['other'])
                            c.write_cstring(outBuffer, "{} {}".format(entry_key, params_str))
                        else:
                            c.write_cstring(outBuffer, entry_key)
                        val = entry_value.getvalue()
                        val_size = len(val)
                        outBuffer.write(struct.pack('<I', val_size))
                        outBuffer.write(val)


                else:
                    c.write_cstring(outBuffer, "{} {}".format(section_name, 0))
            
            else:
                c.write_cstring(outBuffer, "{} {}".format(section_name, 0))

        else:
            c.write_cstring(outBuffer, "{} {}".format(section_name, 0))
            

    
    with open(outFilepath, 'wb') as file:
        file.write(outBuffer.getvalue())


def parse_msk_params(paramStr):
    result = {
        'pfrm': None,
        'has_pfrm': False,
        'magic': None,
        'other': []
    }
    paramArr = paramStr.split(' ')
    for param in paramArr:
        if param[0:4] == 'PFRM':
            result['pfrm'] = param[4:8]
        
        elif param[0:4] in ['MSK8', 'MS16', 'MASK', 'MSKR']:
            result['magic'] = param[0:4]
        
        else:
            result['other'].append(param)
    
    if result['pfrm'] is not None:
        result['has_pfrm'] = True
    else:
        result['pfrm'] = '0565'

    return result

def parse_tex_params(paramStr):
    result = {
        'img_type': 'TIMG',
        'has_lvmp': False,
        'pfrm': None,
        'has_pfrm': False,
        'other': []
    }
    paramArr = paramStr.split(' ')
    for param in paramArr:
        if param[0:4] == 'PFRM':
            result['pfrm'] = param[4:8]
        
        elif param[0:4] == 'LVMP':
            result['has_lvmp'] = True

        elif param[0:4] == 'CMAP':
            result['img_type'] = 'CMAP'
                
        else:
            result['other'].append(param)
    
    if result['pfrm'] is not None:
        result['has_pfrm'] = True
    else:
        result['pfrm'] = '0565'

    return result
