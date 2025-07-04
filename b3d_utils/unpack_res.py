import sys
import logging
import os

from io import BytesIO
from pathlib import Path

import parsing.read_res as res

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("remove_b3d")
log.setLevel(logging.DEBUG)

def resunpack(resFilepath):
    
    read_from_stream = None
    with open(resFilepath, 'rb') as file:
        read_from_stream = BytesIO(file.read())

    resFilename = os.path.splitext(os.path.basename(resFilepath))[0]

    unpackDir = os.path.join(os.path.dirname(resFilepath), "{}_unpack".format(resFilename))
    print(unpackDir)

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

    if not os.path.exists(unpackDir):
        os.mkdir(unpackDir)

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
                    for data in section['metadata']:
                        outBuffer.write(("{}\n").format(data).encode("UTF-8"))
                elif section_name in ["MATERIALS"]:
                    for data_name, data in section['metadata'].items():
                        outBuffer.write(("{}\n").format(res.get_mat_string(data)).encode("UTF-8"))
                elif section_name in ["SOUNDS"]:
                    for data_name, data in section['metadata'].items():
                        outBuffer.write(("{} {}\n").format(data_name, data).encode("UTF-8"))
                with open(binfile_path, "wb") as out_file:
                    out_file.write(outBuffer.getvalue())
            else:
                for data_name, data in section['metadata'].items():
                    binfile_path = os.path.join(sectionFolder, data_name)
                    binfile_base = os.path.dirname(binfile_path)
                    binfile_base = Path(binfile_base)
                    binfile_base.mkdir(exist_ok=True, parents=True)
                    read_from_stream.seek(data["start"],0)
                    outBuffer = BytesIO(read_from_stream.read(data["size"])) 
                    with open(binfile_path, "wb") as out_file:
                        out_file.write(outBuffer.getvalue())
