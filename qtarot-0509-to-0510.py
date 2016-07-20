#!/usr/bin/env python3

from lxml import etree
from html2text import HTML2Text

import os

from argparse import ArgumentParser

ALL_MEANINGS = etree.XPath('//meaning/normal|//meaning/reversed')
CONVERTER = HTML2Text()

def convert_to_new_format(xmlobj):
    for meaning_node in ALL_MEANINGS(xmlobj):
        if meaning_node.text is not None:
            html_text = meaning_node.text
            meaning_node.text = CONVERTER.handle(html_text)

aparser = ArgumentParser()
aparser.add_argument("--output-dir", default=".")
aparser.add_argument("input_files", nargs='+')

args = aparser.parse_args()

for fname in args.input_files:
    xmlobj = etree.parse(fname)
    convert_to_new_format(xmlobj)

    dest_fname = os.path.join(args.output_dir, os.path.basename(fname))

    with open(dest_fname, 'w', encoding='utf-8') as destf:
        destf.write(etree.tounicode(xmlobj, pretty_print=True))
