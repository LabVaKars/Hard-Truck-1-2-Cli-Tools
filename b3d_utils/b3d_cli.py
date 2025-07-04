import logging
import sys
import argparse
import os

import remove_b3d
import merge_b3d
import extract_b3d
import list_b3d

import remove_res
import merge_res
import extract_res
import list_res

import common

from consts import SECTIONS

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



parser = argparse.ArgumentParser(description="Say hello")

format_subparser = parser.add_subparsers(dest="format", help="Format with which cli is currently working", required=True)

#res utils
res_parser = format_subparser.add_parser("res", help="Commands to work with .res files")
subparser = res_parser.add_subparsers(dest="command", help="Commands to work with .res files")

# extract - parses res. Exports selected res sections and/or selected records in separate .res file. 
extract_parser = subparser.add_parser("extract", help="Extracts selected res sections and/or selected records in separate .res file")
extract_parser.add_argument('--i', help="Path to res file", required=True)
extract_parser.add_argument('--sections', help="List of sections to include. All included by default", nargs="+", choices=SECTIONS)
extract_parser.add_argument('--o', help="Path to output file. {name}_extract.res by default")

#   Res settings
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
list_parser.add_argument('--o', help="Path to output file. If not set - prints to terminal")

#merge - merges two res-files into single one
merge_parser = subparser.add_parser("merge", help="Merge selected res sections and/or selected records into .res file")
merge_parser.add_argument('--i-from', help="Path to res file to merge from", required=True)
merge_parser.add_argument('--i-to', help="Path to res file to merge into", required=True)
merge_parser.add_argument('--replace', action='store_true', help="If is set replaces resources with same names. Ignores otherwise")
merge_parser.add_argument('--o', help="Path to res file to save merge result. If not set merges into original file")

#remove
remove_parser = subparser.add_parser("remove", help="Remove selected resources res file")
remove_parser.add_argument('--i', help="Path to res file", required=True)
remove_parser.add_argument('--o', help="Path to res file to save result. If not set save into original file")

#   Res settings

remove_parser.add_argument('--rem-soundfiles', type = parse_items, help="Soundfile full name in res. Example: snd\\alarm.wav")
remove_parser.add_argument('--ref-soundfiles', action='store_true', help="Extract only soundfiles referenced within this resource file. --inc-soundfiles is ignored if this flag is set")
remove_parser.add_argument('--rem-backfiles', type = parse_items, help="Backfile full name in res. Example: txr\\sky.txr")
remove_parser.add_argument('--rem-maskfiles', type = parse_items, help="Maskfile full name in res. Example: txr\\rain.txr")
remove_parser.add_argument('--ref-maskfiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-maskfiles is ignored if this flag is set")
remove_parser.add_argument('--rem-texturefiles', type = parse_items, help="Texturefile full name in res. Example: txr\\tree.txr")
remove_parser.add_argument('--ref-texturefiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-texturefiles is ignored if this flag is set")
remove_parser.add_argument('--rem-materials', type = parse_items, help="Material name in res")
remove_parser.add_argument('--rem-sounds', type = parse_items, help="Sound name in res")



#b3d utils
b3d_parser = format_subparser.add_parser("b3d", help="Commands to work with .b3d files")
subparser = b3d_parser.add_subparsers(dest="command", help="Commands to work with b3d. files")

# extract - parses b3d. Find root elements in structure(by finding nodes, that aren't referenced(18)) or uses root name file instead(--roots) 
extract_parser = subparser.add_parser("extract", help="Extract selected b3d nodes with all references into separate files")
extract_parser.add_argument('--i', help="Path to b3d file", required=True)
extract_parser.add_argument('--inc-nodes', type = parse_items, help="List of node names divided by comma. Accepts comma-separated string or path to file with comma-separated string. File path should start with @. For example: @test.txt")
extract_parser.add_argument('--node-refs', action='store_true', help="Export with all references. If not set ignore node references")
extract_parser.add_argument('--split', action='store_true', help="Export each node to separate file with node name. If not set export all nodes to single file")
extract_parser.add_argument('--o', help="Path to output folder/file. Default is b3d file folder.")
extract_parser.add_argument('--res', help="Path to res file. If is set, exports associated res file(s) with defined parameters.")
extract_parser.add_argument('--ref-materials', action='store_true', help="Save only materials used in this .b3d")

#   Settings for connected res file
extract_parser.add_argument('--sections', help="List of res sections to include. All included by default", nargs="+", choices=SECTIONS)
extract_parser.add_argument('--inc-soundfiles', type = parse_items, help="Soundfile full name in res. Example: snd\\alarm.wav")
extract_parser.add_argument('--ref-soundfiles', action='store_true', help="Extract only soundfiles referenced within this resource file. --inc-soundfiles is ignored if this flag is set")
extract_parser.add_argument('--inc-backfiles', type = parse_items, help="Backfile full name in res. Example: txr\\sky.txr")
extract_parser.add_argument('--inc-maskfiles', type = parse_items, help="Maskfile full name in res. Example: txr\\rain.txr")
extract_parser.add_argument('--ref-maskfiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-maskfiles is ignored if this flag is set")
extract_parser.add_argument('--inc-texturefiles', type = parse_items, help="Texturefile full name in res. Example: txr\\tree.txr")
extract_parser.add_argument('--ref-texturefiles', action='store_true', help="Extract only texturefiles referenced within this resource file. --inc-texturefiles is ignored if this flag is set")
extract_parser.add_argument('--inc-materials', type = parse_items, help="Material name in res")
extract_parser.add_argument('--inc-sounds', type = parse_items, help="Sound name in res")

#list - parses b3d. List all nodes
list_parser = subparser.add_parser("list", help="List b3d file")
list_parser.add_argument('--i', help="Path to b3d file", required=True)
list_parser.add_argument('--t', help="What type of information to list. Availabe options: MATERIALS, ROOTS, FULL", choices=['MATERIALS','ROOTS','FULL'], required=True)
list_parser.add_argument('--o', help="Path to output file. If not set - prints to terminal")

#remove
remove_parser = subparser.add_parser("remove", help="Remove selected b3d nodes with all references from b3d file")
remove_parser.add_argument('--i', help="Path to b3d file", required=True)
remove_parser.add_argument('--rem-nodes', type = parse_items, help="List of node names divided by comma. Accepts comma-separated string or path to file with comma-separated string. File path should start with @. For example: @test.txt")
remove_parser.add_argument('--rem-materials', type = parse_items, help="Material name in res")
remove_parser.add_argument('--o', help="Path to b3d file to save result. If not set save into original file")

# merge
merge_parser = subparser.add_parser("merge", help="List b3d file")
merge_parser.add_argument('--i-from', help="Path to b3d file to merge from", required=True)
merge_parser.add_argument('--i-to', help="Path to b3d file to merge into", required=True)
merge_parser.add_argument('--replace', action='store_true', help="If is set replaces nodes with same names. Ignores otherwise")
merge_parser.add_argument('--o', help="Path to b3d file to save merge result. If not set merges into original file")


args = parser.parse_args()
print(args)
if args.format == 'b3d':
    if args.command == 'extract':

        res_params = common.get_res_params(
            args.sections, 
            args.inc_soundfiles, args.ref_soundfiles,
            args.inc_backfiles, 
            args.inc_maskfiles, args.ref_maskfiles,
            args.inc_texturefiles, args.ref_texturefiles,
            args.inc_materials,
            args.inc_sounds
        )

        extract_b3d.b3dextract(args.i, args.res, args.o, args.inc_nodes, args.split, args.node_refs, args.ref_materials, res_params["current_sections"], res_params["section_records"])

    elif args.command == 'list':
        list_b3d.b3dlist(args.i, args.t, args.o)
        
    elif args.command == 'merge':
        merge_b3d.b3dmerge(args.i_from, args.i_to, args.o, args.replace)

    elif args.command == 'remove':
        remove_b3d.b3dremove(args.i, args.o, args.rem_materials, args.rem_nodes)

elif args.format == 'res':
    
    if args.command == 'extract':

        res_params = common.get_res_params(
            args.sections, 
            args.inc_soundfiles, args.ref_soundfiles,
            args.inc_backfiles, 
            args.inc_maskfiles, args.ref_maskfiles,
            args.inc_texturefiles, args.ref_texturefiles,
            args.inc_materials,
            args.inc_sounds
        )

        extract_res.resextract(args.i, args.o, res_params["current_sections"], res_params["section_records"])

    elif args.command == 'list':

        list_res.reslist(args.i, args.o)
    
    elif args.command == 'merge':

        merge_res.resmerge(args.i_from, args.i_to, args.o, args.replace)
    
    elif args.command == 'remove':
        
        res_params = common.get_res_params(
            [], 
            args.rem_soundfiles, args.ref_soundfiles,
            args.rem_backfiles, 
            args.rem_maskfiles, args.ref_maskfiles,
            args.rem_texturefiles, args.ref_texturefiles,
            args.rem_materials,
            args.rem_sounds
        )

        remove_res.resremove(args.i, args.o, res_params["section_records"])
