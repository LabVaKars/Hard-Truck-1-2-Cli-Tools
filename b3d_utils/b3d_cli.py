import logging
import sys
import argparse
import os

import extract_b3d
import list_b3d
import extract_res
import list_res

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("b3d_cli")
log.setLevel(logging.DEBUG)

def parse_items(value):
    # If prefixed with '@', treat it as a filename
    items = []
    if value.startswith('@'):
        filepath = value[1:]
        if not os.path.isfile(filepath):
            raise argparse.ArgumentTypeError(f"File not found: {filepath}")
        with open(filepath, 'r') as f:
            items = f.readline().strip().split(',')
    else:
        items = value.strip().split(',')
    return items

sections = ["PALETTEFILES", "SOUNDFILES", "BACKFILES", "MASKFILES", "TEXTUREFILES", "COLORS", "MATERIALS", "SOUNDS"]

parser = argparse.ArgumentParser(description="Say hello")

format_subparser = parser.add_subparsers(dest="format", help="Format with which cli is currently working", required=True)

#res utils
res_parser = format_subparser.add_parser("res", help="Commands to work with .res files")
subparser = res_parser.add_subparsers(dest="command", help="Commands to work with .res files")

# extract - parses res. Exports selected res sections and/or selected records in separate .res file. 
extract_parser = subparser.add_parser("extract", help="Extracts selected res sections and/or selected records in separate .res file")
extract_parser.add_argument('--i', help="Path to res file", required=True)
extract_parser.add_argument('--incl', help="List of sections to include. All included by default", nargs="+", choices=sections)
extract_parser.add_argument('--excl', help="List of sections to exclude. All included by default", nargs="+", choices=sections)
extract_parser.add_argument('--o', help="Path to output file. {name}_extract.res by default")

# namelist_subparser = extract_parser.add_subparsers(dest="include_lists", help="Lists of names to include in extract")
# namelist_parser = namelist_subparser.add_parser("using", help="Extract selected resources into separate files. All arguments accepts list of names divided by comma. Also accepts comma-separated string or path to file with comma-separated string. File path should start with @. For example: @test.txt")

extract_parser.add_argument('--inc-soundfiles', type = parse_items, help="Soundfile full name in res. Example: snd\\alarm.wav")
extract_parser.add_argument('--ref-soundfiles', action='store_true', help="Extract only soundfiles referenced within this resource file. --inc-soundfiles is ignored if this flag is set")
extract_parser.add_argument('--inc-backfiles', type = parse_items, help="Backfile full name in res. Example: txr\\sky.txr")
extract_parser.add_argument('--inc-maskfiles', type = parse_items, help="Maskfile full name in res. Example: txr\\rain.txr")
extract_parser.add_argument('--ref-maskfiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-maskfiles is ignored if this flag is set")
extract_parser.add_argument('--inc-texturefiles', type = parse_items, help="Texturefile full name in res. Example: txr\\tree.txr")
extract_parser.add_argument('--ref-texturefiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-texturefiles is ignored if this flag is set")
extract_parser.add_argument('--inc-materials', type = parse_items, help="Material name in res")
extract_parser.add_argument('--inc-sounds', type = parse_items, help="Sound name in res")

#list - parses res. List all resources
list_parser = subparser.add_parser("list", help="List res file")
list_parser.add_argument('--i', help="Path to res file", required=True)

#b3d utils
b3d_parser = format_subparser.add_parser("b3d", help="Commands to work with .b3d files")
subparser = b3d_parser.add_subparsers(dest="command", help="Commands to work with b3d. files")

# extract - parses b3d. Find root elements in structure(by finding nodes, that aren't referenced(18)) or uses root name file instead(--roots) 
extract_parser = subparser.add_parser("extract", help="Extract selected b3d nodes with all references into separate files")
extract_parser.add_argument('--i', help="Path to b3d file", required=True)
extract_parser.add_argument('--nodes', type = parse_items, help="List of node names divided by comma. Accepts comma-separated string or path to file with comma-separated string. File path should start with @. For example: @test.txt")
# extract_parser.add_argument('--split', action='store_true', help="Default. Export each node to separate file with node name. If not set export all nodes to single file")
# extract_parser.add_argument('--ref', action='store_true', help="Default. Export with all references. If not set ignore node references")
# extract_parser.add_argument('--ref-materials', action='store_true', help="Save only materials used in this .b3d")
extract_parser.add_argument('--o', help="Path to output folder/file. Default is b3d file folder.")
extract_parser.add_argument('--res', help="Path to res file. Default name same as for b3d file")

#list - parses b3d. List all nodes
list_parser = subparser.add_parser("list", help="List b3d file")
list_parser.add_argument('--i', help="Path to b3d file", required=True)

#remove
remove_parser = subparser.add_parser("remove", help="Remove selected b3d nodes with all references from b3d file")
remove_parser.add_argument('--i', help="Path to b3d file", required=True)

# merge

args = parser.parse_args()
if args.format == 'b3d':
    if args.command == 'extract':
        extract_b3d.b3dextract(args.i, args.res, args.o, args.roots)

    elif args.command == 'list':
        list_b3d.b3dlist(args.i)
        
    elif args.command == 'remove':
        pass

elif args.format == 'res':
    
    if args.command == 'extract':
        current_sections = None
        if(args.excl):
            current_sections = list(set(sections) - set(args.excl))
        elif(args.incl):
            current_sections = args.incl

        section_records = {
            "SOUNDFILES": "REF" if args.ref_soundfiles else args.inc_soundfiles,
            "BACKFILES": args.inc_backfiles,
            "MASKFILES": "REF" if args.ref_maskfiles else args.inc_maskfiles,
            "TEXTUREFILES": "REF" if args.ref_texturefiles else args.inc_texturefiles,
            "MATERIALS": args.inc_materials,
            "SOUNDS": args.inc_sounds,
            "PALETTEFILES": None
        }
        extract_res.resextract(args.i, args.o, current_sections, section_records)

    elif args.command == 'list':

        list_res.reslist(args.i)

    elif args.command == 'remove':
        pass