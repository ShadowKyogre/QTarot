from lxml import etree, objectify
from os import path
from PyQt4 import QtCore

from . import VALIDATORS

dvald = open(path.join(VALIDATORS,'deck.xsd'))
deck_validator = etree.XMLSchema(etree.parse(dvald))
dvald.close()
del dvald

lvald = open(path.join(VALIDATORS,'layouts.xsd'))
layout_validator = etree.XMLSchema(etree.parse(lvald))
lvald.close()
del lvald

class TarotDeck(objectify.ObjectifiedElement):
	def cards(self):
		return self.xpath('suit/card')
	def conforms(self, skin):
		skin_dir=QtCore.QDir("skins:{skin}".format(**locals()))

		skin_contents=set(str(i) for i in skin_dir.entryList() \
						if str(i) not in (".","..","table.png","deck.ini"))
		required_files=set( c.file.text for c in self.cards() )
		#or required_files-skin_contents
		return required_files.issubset(skin_contents)

class TarotCard(objectify.ObjectifiedElement):
	def fullname(self):
		parent=self.getparent()
		if 'nosuitname' in parent.attrib and parent.attrib['nosuitname'] in ('1','true'):
			return self.attrib['name']
		else:
			return "{name} of {suit}"\
			.format(suit=parent.attrib['name'], \
			name=self.attrib['name'])

class TarotLayout(objectify.ObjectifiedElement):
	def largetDimension(self):
		height=float(self.attrib['height'])
		width=float(self.attrib['width'])
		return height if height > width else width

lookup = etree.ElementNamespaceClassLookup(objectify.ObjectifyElementClassLookup())
parser = etree.XMLParser(remove_blank_text=True)
parser.set_element_class_lookup(lookup)

namespace = lookup.get_namespace('')
namespace['deck']=TarotDeck
namespace['card']=TarotCard
namespace['layout']=TarotLayout
