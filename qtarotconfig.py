from PyQt4 import QtGui,QtCore
import os
from collections import OrderedDict as od
from lxml import etree, objectify

deck_validator = etree.XMLSchema(etree.parse(open('%s/deck.xsd' \
	%(os.sys.path[0]),'r')))
layout_validator = etree.XMLSchema(etree.parse(open('%s/layouts.xsd' \
	%(os.sys.path[0]),'r')))

class TarotDeck(objectify.ObjectifiedElement):
	def cards(self):
		return self.xpath('suit/card')
	def conforms(self, skin):
		skin_dir=QtCore.QDir("skins:{skin}".format(**locals()))

		skin_contents=set( str(i) for i in skin_dir.entryList() \
						if str(i) not in (".","..","table.png","deck.ini"))
		required_files=set( c.file.text for c in self.cards() )
		#or required_files-skin_contents
		return required_files.issubset(skin_contents)

class TarotCard(objectify.ObjectifiedElement):
	def fullname(self):
		parent=self.getparent()
		if parent.attrib.has_key('only_literal'):
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

def setup_parser():
	global parser
	lookup = etree.ElementNamespaceClassLookup(objectify.ObjectifyElementClassLookup())
	parser = etree.XMLParser(remove_blank_text=True)
	parser.set_element_class_lookup(lookup)

	namespace = lookup.get_namespace('')
	namespace['deck']=TarotDeck
	namespace['card']=TarotCard
	namespace['layout']=TarotLayout

class QTarotConfig:
	APPNAME="QTarot"
	APPVERSION="0.3.0"
	AUTHOR="ShadowKyogre"
	DESCRIPTION="A simple tarot fortune teller."
	YEAR="2012"
	PAGE="http://shadowkyogre.github.com/QTarot/"
	def __init__(self):
		self.settings=QtCore.QSettings(QtCore.QSettings.IniFormat,
						QtCore.QSettings.UserScope,
						self.AUTHOR,
						self.APPNAME)

		#path for deck skins is like: "skins:<deck-name>"
		#so default table is "skins:{skin}/table.png"
		#deck defs are like "decks:{deck}.xml"
		#path for layouts is like "layouts:<layout-name>.lyt"

		self.userconfdir=str(QtGui.QDesktopServices.storageLocation\
		(QtGui.QDesktopServices.DataLocation)).replace('//','/')

		app_theme_path=os.path.join(os.sys.path[0],"decks")
		config_theme_path=os.path.join(self.userconfdir,"decks")

		app_layout_path=os.path.join(os.sys.path[0],"layouts")
		config_layout_path=os.path.join(self.userconfdir,"layouts")

		app_defs_path=os.path.join(os.sys.path[0],"deck_defs")
		config_defs_path=os.path.join(self.userconfdir,"deck_defs")

		QtCore.QDir.setSearchPaths("layouts", [config_layout_path,app_layout_path])
		QtCore.QDir.setSearchPaths("skins", [config_theme_path,app_theme_path])
		QtCore.QDir.setSearchPaths("deckdefs", [config_defs_path,app_defs_path])

		setup_parser()
		self.sys_icotheme=QtGui.QIcon.themeName()
		self.reset_settings()

	def load_layouts(self):
		self.layouts=od()
		layouts_path=QtCore.QDir("layouts:/")
		for i in layouts_path.entryList():
			if str(i) in (".",".."):
				continue
			path=str(layouts_path.absoluteFilePath(i))
			lay=objectify.parse(path,parser=parser)
			try:
				layout_validator.validate(lay)
				lay=lay.getroot()
				self.layouts[lay.attrib['name']]=lay
			except etree.DocumentInvalid, e:
				print e.message

	def setup_skin(self):
		QtCore.QDir.setSearchPaths("skin", ["skins:%s" %(self.deck_skin)])

	def load_deck_defs(self):
		self.deck_defs=od()
		deck_defs_path=QtCore.QDir("deckdefs:/")
		for i in deck_defs_path.entryList():
			if str(i) in (".",".."):
				continue
			path=str(deck_defs_path.absoluteFilePath(i))
			deck_def=objectify.parse(path,parser=parser)
			try:
				deck_validator.validate(deck_def)
				deck_def=deck_def.getroot()
				self.deck_defs[deck_def.attrib['name']]={}
				self.deck_defs[deck_def.attrib['name']]['definition']=deck_def
				self.deck_defs[deck_def.attrib['name']]['skins']=[]
			except etree.DocumentInvalid, e:
				print e.message

	def load_skins(self):
		deck_skins_path=QtCore.QDir("skins:/")
		for i in deck_skins_path.entryList():
			if str(i) in (".",".."):
				continue
			if deck_skins_path.exists("skins:/{i}/deck.ini".format(i=i)):
				skin_info=QtCore.QSettings("skins:/{i}/deck.ini".format(i=i), \
							QtCore.QSettings.IniFormat)
				skin_info.beginGroup("Deck Skin")
				for_deck=str(skin_info.value("definition","").toString())
				if for_deck:
					if self.deck_defs.has_key(for_deck):
						if self.deck_defs[for_deck]['definition'].conforms(i):
							self.deck_defs[for_deck]['skins'].append(str(i))
							#copy metadata
						else:
							print ("Deck definition {for_deck}"
							" is not compatible with {i}"
							", skipping {i}...").format(**locals())
					else:
						print ("Deck definition {for_deck} is not installed"
						", skipping {i}...").format(**locals())
				else:
					print ("Cannot confirm which deck definitions"
					" {i} is compatible with, skipping...").format(i=i)
				skin_info.endGroup()
			else:
				print ("Cannot confirm which deck definitions"
				" {i} is compatible with, skipping...").format(i=i)

	def reset_settings(self):
		self.settings.beginGroup("Reading")
		self.deck_def=str(self.settings.value("deck","Rider Waite").toString())
		self.negativity=self.settings.value("negativity",0.5).toDouble()[0]
		self.default_layout=str(self.settings.value("defaultLayout","Ellipse").toString())
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		#deck_name is now deck_skin
		self.deck_skin=str(self.settings.value("skin","coleman-white").toString())
		self.current_icon_override=str(self.settings.value("stIconTheme", \
					QtCore.QString("")).toPyObject())
		if self.current_icon_override > "":
			QtGui.QIcon.setThemeName(self.current_icon_override)
		else:
			QtGui.QIcon.setThemeName(self.sys_icotheme)
		self.settings.endGroup()

		self.load_deck_defs()
		self.load_layouts()
		self.load_skins()
		self.setup_skin()

	def save_settings(self):
		self.settings.beginGroup("Reading")
		self.settings.setValue("deck",self.deck_def)
		self.settings.setValue("negativity",self.negativity)
		self.settings.setValue("defaultLayout",self.default_layout)
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		self.settings.setValue("skin",self.deck_skin)
		self.settings.setValue("stIconTheme",self.current_icon_override)
		self.settings.endGroup()

		self.settings.sync()
