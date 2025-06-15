import logging
import sys
import os
from io import BytesIO

import parsing.read_res as res 

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("list_res")
log.setLevel(logging.DEBUG)


def reslist(resFilename):
    
    res_stream = None
    with open(resFilename, 'rb') as file:
        res_stream = BytesIO(file.read())

    section = None
    while(True):
        section = res.read_section(res_stream)
        if(not section):
            break
        print('{}: {}'.format(section['name'], section['size']))
        if section['name'] != 'COLORS':
            for key in section['metadata'].keys(): #dict
                print('  {}'.format(key))
