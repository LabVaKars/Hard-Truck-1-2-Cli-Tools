import sys
import logging
import os
import json

from io import BytesIO
from pathlib import Path

import parsing.read_res as res
import common as c
import imghelp as img

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("unpack_res")
log.setLevel(logging.DEBUG)

def resunpack(resFilepath, saveTxrMsk = False):
    
    read_from_stream = None
    with open(resFilepath, 'rb') as file:
        read_from_stream = BytesIO(file.read())

    resFilename = os.path.splitext(os.path.basename(resFilepath))[0]

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

    unpackDir = os.path.join(os.path.dirname(resFilepath), "{}_unpack".format(resFilename))
    if not os.path.exists(unpackDir):
        os.mkdir(unpackDir)

    # Unpack raw resources
    for section_name, section in sections.items():
        if section is not None:
            sectionFolder = os.path.join(unpackDir, section_name)
            if section_name in ["COLORS", "MATERIALS", "SOUNDS"]: # save only .txt
                binfile_path = os.path.join(sectionFolder, "{}.txt".format(section_name))
                binfile_base = os.path.dirname(binfile_path)
                binfile_base = Path(binfile_base)
                binfile_base.mkdir(exist_ok=True, parents=True)
                outBuffer = BytesIO()
                if section_name in ["COLORS"]:
                    outputArr = []
                    for data in section['metadata']:
                        outputArr.append(("{}").format(data))
                    outBuffer.write(json.dumps(outputArr, indent=2).encode("UTF-8"))
                elif section_name in ["MATERIALS"]:
                    outputObj = {}
                    for data_name, data in section['metadata'].items():
                        outputObj[data_name] = ("{}").format(res.get_mat_string(data))
                    outBuffer.write(json.dumps(outputObj, indent=2).encode("UTF-8"))
                elif section_name in ["SOUNDS"]:
                    outputObj = {}
                    for data_name, data in section['metadata'].items():
                        outputObj[data_name] = ("{} {}").format(data_name, data)
                    outBuffer.write(json.dumps(outputObj, indent=2).encode("UTF-8"))
                with open(binfile_path, "wb") as out_file:
                    out_file.write(outBuffer.getvalue())
            else:
                sectionObj = {}
                for data_name, data in section['metadata'].items():
                    binfile_path = os.path.join(sectionFolder, data_name)
                    binfile_base = os.path.dirname(binfile_path)
                    binfile_base = Path(binfile_base)
                    binfile_base.mkdir(exist_ok=True, parents=True)
                    read_from_stream.seek(data["start"],0)
                    outBuffer = BytesIO(read_from_stream.read(data["size"])) 
                    outBuffer.seek(0,0) 
                    name = res.read_cstring(outBuffer) # skip filename
                    sectionObj[data_name] = name.split(' ')[1:]
                    outBuffer.seek(4,1) #skip SectionSize
                    rawBuffer = BytesIO(outBuffer.read())
                    if saveTxrMsk:
                        with open(binfile_path, "wb") as out_file:
                            out_file.write(rawBuffer.getvalue())
                    
                    noExtPath = os.path.join(sectionFolder, os.path.splitext(data_name)[0])
                    if section_name in ['PALETTEFILES']:
                        outfile_path = "{}.txt".format(noExtPath)

                        colors = img.parse_plm(rawBuffer)
                        hex_colors = ['#{:02X}{:02X}{:02X}'.format(c['r'], c['g'], c['b']) for c in colors]
                        with open(outfile_path, "wb") as out_file:
                            out_file.write(json.dumps(hex_colors, indent=2).encode('utf-8'))
                    
                    elif section_name in ['TEXTUREFILES', 'BACKFILES']:
                        transp_color = [0, 0, 0]

                        outfile_path = "{}.tga".format(noExtPath)
                        result = img.convert_txr_to_tga32(rawBuffer, transp_color)

                        # save PFRM value
                        pfrm = result['format']
                        if pfrm is not None:
                            r_unmask = c.unmask_bits(pfrm[0])
                            g_unmask = c.unmask_bits(pfrm[1])
                            b_unmask = c.unmask_bits(pfrm[2])
                            a_unmask = c.unmask_bits(pfrm[3])
                            pfrm_value = 'PFRM{}{}{}{}'.format(b_unmask.ones, g_unmask.ones, r_unmask.ones, a_unmask.ones)
                            sectionObj[data_name].append(pfrm_value)

                        with open(outfile_path, "wb") as out_file:
                            outBuffer = result['data']
                            outBuffer.seek(0,0)
                            out_file.write(outBuffer.getvalue()) #BytesIO
                        if result['has_mipmap']:
                            sectionObj[data_name].append('LVMP')
                            for mipmap_data in result['mipmaps']:
                                mipmap_path = "{}_{}_{}.tga".format(noExtPath, mipmap_data['w'], mipmap_data['h'])
                                with open(mipmap_path, "wb") as out_file:
                                    out_file.write((result['data']).getvalue())
                        
                    elif section_name in ['MASKFILES']:
                        outfile_path = "{}.tga".format(noExtPath)
                        result = img.msk_to_tga32(rawBuffer)
                        sectionObj[data_name].append(result['magic'])
                        with open(outfile_path, "wb") as out_file:
                            out_file.write((result['data']).getvalue())
                    sectionObj[data_name] = ' '.join(sectionObj[data_name])
                    
                if len(section['metadata'].items()) > 0:
                    outfile_path = os.path.join(sectionFolder, "{}.txt".format(section_name))
                    with open(outfile_path, "wb") as out_file:
                        out_file.write(json.dumps(sectionObj, indent=2).encode('utf-8'))



                        
                    

                        
