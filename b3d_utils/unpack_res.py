import sys
import logging
import os
import json

from io import BytesIO
from pathlib import Path

import parsing.read_res as res
import common as c
import imghelp as img
from consts import PALETTE_HTML

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("unpack_res")
log.setLevel(logging.DEBUG)

def resunpack(resFilepath, selected_sections, saveTxrMsk = False):
    
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
        "PALETTEFILES": None,
        "SOUNDFILES": None,
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
        if section is not None and section_name in selected_sections:
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
                        outputObj[data_name] = ("{}").format(data)
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
                    if section_name not in ['TEXTUREFILES', 'MASKFILES'] or (saveTxrMsk and section_name in ['TEXTUREFILES', 'MASKFILES']):
                        with open(binfile_path, "wb") as out_file:
                            out_file.write(rawBuffer.getvalue())
                    
                    noExtPath = os.path.join(sectionFolder, os.path.splitext(data_name)[0])
                    if section_name in ['PALETTEFILES']:
                        outfile_path = "{}.txt".format(noExtPath)
                        palette = img.parse_plm(rawBuffer)
                        colors = palette["PALT"]
                        opac = palette["OPAC"]
                        fogs = palette["FOG"]
                        inte = palette["INTE"]
                        op16 = palette["OP16"]
                        fo16 = palette["FO16"]
                        in16 = palette["IN16"]
                        # colors_json = json.dumps(opac, indent=2)
                        # with open(outfile_path, "wb") as out_file:
                        #     out_file.write(colors_json.encode('utf-8'))
                        hex_colors = []

                        html_data = ""
                        html_js = ""
                        if(len(colors)> 0): #PALT
                            hex_colors = ['#{:02X}{:02X}{:02X}'.format(c['r'], c['g'], c['b']) for c in colors]
                            html_data += "let palt_colors = {}\n".format(json.dumps(hex_colors))
                            html_js += "app.appendChild({});\n".format("createHeading('PALT')")
                            html_js += "app.appendChild({});\n".format("createPALTBody(palt_colors)")
                        
                        if(len(opac)> 0): #OPAC
                            opac_colors = [
                                [
                                    [hex_colors[i] for i in pal]
                                    for pal in list(pal_row)
                                ]
                                for pal_row in zip(*opac)
                            ] # flip dimensions using zip

                            html_js += "app.appendChild({});\n".format("createHeading('OPAC')")
                            for ind, pal_row in enumerate(opac_colors):
                                html_data += "let opac_colors{} = {}\n".format(ind, json.dumps(pal_row))
                                pal_cnt = len(pal_row)
                                html_js += "app.appendChild({});\n".format("createOPACBody(opac_colors{}, {})".format(ind, pal_cnt))

                        if(len(fogs)> 0): #FOG
                            fog_colors = [
                                [hex_colors[i] for i in pal]
                                for pal in fogs
                            ]

                            pal_cnt = len(fog_colors)
                            html_js += "app.appendChild({});\n".format("createHeading('FOG')")
                            html_data += "let fog_colors = {}\n".format(json.dumps(fog_colors))
                            html_js += "app.appendChild({});\n".format("createOPACBody(fog_colors, {})".format(pal_cnt))
                        
                        if(len(inte)> 0): #INTE
                            inte_colors = [
                                [hex_colors[i] for i in pal]
                                for pal in inte
                            ]

                            pal_cnt = len(inte_colors)
                            html_js += "app.appendChild({});\n".format("createHeading('INTE')")
                            html_data += "let inte_colors = {}\n".format(json.dumps(inte_colors))
                            html_js += "app.appendChild({});\n".format("createOPACBody(inte_colors, {})".format(pal_cnt))

                        if(len(op16)) > 0: #OP16
                            op16_colors = [
                                [
                                    ['#{:02X}{:02X}{:02X}'.format(c['r'], c['g'], c['b']) for c in pal]
                                    for pal in pal_row
                                ]
                                for pal_row in op16
                            ]

                            size = 1024
                            op16_colors = [
                                [pal[i:i + size] for i in range(0, len(pal), size)] # split into smaller palettes 
                                for pal_row in op16_colors                          # if multiple palettes in one row, they are joined together
                                for pal in pal_row
                            ]
                            
                            pal_cnt = len(op16_colors)
                            html_js += "app.appendChild({});\n".format("createHeading('OP16')")
                            for ind, pal_row in enumerate(op16_colors):
                                html_data += "let op16_colors{} = {}\n".format(ind, json.dumps(pal_row))
                                pal_cnt = len(pal_row)
                                html_js += "app.appendChild({});\n".format("createOPACBody(op16_colors{}, {}, 32)".format(ind, pal_cnt))
                        
                        if(len(fo16)) > 0: #FO16
                            fo16_colors = [
                                ['#{:02X}{:02X}{:02X}'.format(c['r'], c['g'], c['b']) for c in pal]
                                for pal in fo16
                            ]

                            size = 1024
                            fo16_colors = [
                                [pal[i:i + size] for i in range(0, len(pal), size)] # split into smaller palettes 
                                for pal in fo16_colors                              # if multiple palettes in one row, they are joined together
                            ]

                            pal_cnt = len(fo16_colors)
                            html_js += "app.appendChild({});\n".format("createHeading('FO16')")
                            for ind, pal_row in enumerate(fo16_colors):
                                html_data += "let fo16_colors{} = {}\n".format(ind, json.dumps(pal_row))
                                pal_cnt = len(pal_row)
                                html_js += "app.appendChild({});\n".format("createOPACBody(fo16_colors{}, {}, 32)".format(ind, pal_cnt))
                        
                        if(len(in16)) > 0: #IN16
                            in16_colors = [
                                ['#{:02X}{:02X}{:02X}'.format(c['r'], c['g'], c['b']) for c in pal]
                                for pal in in16
                            ]

                            size = 1024
                            in16_colors = [
                                [pal[i:i + size] for i in range(0, len(pal), size)] # split into smaller palettes 
                                for pal in in16_colors                              # if multiple palettes in one row, they are joined together
                            ]

                            pal_cnt = len(in16_colors)
                            html_js += "app.appendChild({});\n".format("createHeading('IN16')")
                            for ind, pal_row in enumerate(in16_colors):
                                html_data += "let in16_colors{} = {}\n".format(ind, json.dumps(pal_row))
                                pal_cnt = len(pal_row)
                                html_js += "app.appendChild({});\n".format("createOPACBody(in16_colors{}, {}, 32)".format(ind, pal_cnt))
                                

                        debug_path = "{}.html".format(noExtPath)
                        debug_html = PALETTE_HTML.replace("{data}", html_data).replace("{js}", html_js)
                        with open(debug_path, "wb") as out_file:
                            out_file.write(debug_html.encode('utf-8'))

                    
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
                        # if 'm15\\' in data_name:
                        #     # pfrm = [63488, 1984, 62, 1] # 5,5,5,1
                        #     # pfrm = [61440, 3840, 240, 15] # 4,4,4,4
                        #     pfrm = [63488, 2016, 31, 0] # 5,6,5,0
                        # else: # m16 and others
                        #     pfrm = [63488, 2016, 31, 0] # 5,6,5,0
                        
                        result = img.msk_to_tga32(rawBuffer)
                        sectionObj[data_name].append(result['magic'])
                        pfrm = result['format']
                        if pfrm is not None:
                            r_unmask = c.unmask_bits(pfrm[0])
                            g_unmask = c.unmask_bits(pfrm[1])
                            b_unmask = c.unmask_bits(pfrm[2])
                            a_unmask = c.unmask_bits(pfrm[3])
                            pfrm_value = 'PFRM{}{}{}{}'.format(b_unmask.ones, g_unmask.ones, r_unmask.ones, a_unmask.ones)
                            sectionObj[data_name].append(pfrm_value)
                        with open(outfile_path, "wb") as out_file:
                            out_file.write((result['data']).getvalue())
                    sectionObj[data_name] = ' '.join(sectionObj[data_name])
                    
                if len(section['metadata'].items()) > 0:
                    outfile_path = os.path.join(sectionFolder, "{}.txt".format(section_name))
                    with open(outfile_path, "wb") as out_file:
                        out_file.write(json.dumps(sectionObj, indent=2).encode('utf-8'))



                        
                    

                        
