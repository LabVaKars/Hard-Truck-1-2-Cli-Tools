import logging
import sys
import argparse

import extract_b3d
import list_b3d

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("b3d_cli")
log.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description="Say hello")
# split - parses b3d. Find root elements in structure(by finding nodes, that has no references(18) to itself) or uses root name file instead(--roots)
# 
subparser = parser.add_subparsers(dest="command", help="Action performed on b3d file", required=True)
split_parser = subparser.add_parser("split", help="Extract selected b3d roots into separate files")

split_parser.add_argument('--b3d', help="Path to b3d file", required=True)
split_parser.add_argument('--res', help="Path to res file. Default name same as for b3d file")
split_parser.add_argument('--roots', help="Path to file with b3d roots")

list_parser = subparser.add_parser("list", help="List b3d file")
list_parser.add_argument('--b3d', help="Path to b3d file", required=True)

# merge


args = parser.parse_args()

if args.command == 'split':
    extract_b3d.b3dsplit(args.b3d, args.res, args.roots)

if args.command == 'list':
    list_b3d.b3dlist(args.b3d)

