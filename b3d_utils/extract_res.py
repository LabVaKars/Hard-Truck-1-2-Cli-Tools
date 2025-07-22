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
    
    read_from_stream = None
    with open(resFilepath, 'rb') as file:
        read_from_stream = BytesIO(file.read())
    
    if not outFilepath:
        basename, ext = os.path.splitext(resFilepath)
        outFilepath = '{}_extract.{}'.format(basename, ext[1:])

    outBuffer = c.write_matching_records(read_from_stream, selected_sections, section_records, False)

    with open(outFilepath, 'wb') as outFile:
        outFile.write(outBuffer.getvalue())