from PyQt4 import QtGui,QtCore
import os
from collections import OrderedDict as od
from lxml import etree

#deck_validator = etree.XMLSchema(etree.parse(open('%s/deck.xsd' \
#	%(os.sys.path[0]),'r')))
#layout_validator = etree.XMLSchema(etree.parse(open('%s/layouts.xsd' \
#	%(os.sys.path[0]),'r')))


class TarotDeck:
	def __init__(self, deck_def="defs/coleman-white.xml"):
		f=open(deck_def)
		self.tree=etree.parse(f).getroot()
		self.name=self.tree.attrib['name']
		#self.preview=#some path to the pixmap :B
		#self.cards=#get all suits' cards
	def preview(self):
		return self.tree.find('preview').text
	def name(self):
		return self.tree.attrib['name']
	def cards(self):
		return self.tree.xpath('suit/card')
	def suits(self):
		return self.tree.xpath('suit')

#print TarotDeck().preview()
#print TarotDeck().cards()
#print TarotDeck().suits()

class TarotCard:
	def __init__(self, card_elem):
		self.card_elem=card_elem
	def meanings(self):
		return self.card_elem.xpath('meaning')
	def filename(self):
		return self.card_elem.xpath('file')
	def number(self):
		return self.card_elem.xpath('number')
	def name(self):
		parent=self.card_elem.getparent()
		if parent.attrib.has_key('only_literal'):
			return self.card_elem.attrib['name']
		else:
			return "{name} of {suit}"\
			.format(suit=parent.attrib['name'], \
			name=self.card_elem.attrib['name'])

class TarotLayout:
	"""
	The constructor for this object.
	"""
	def __init__(self,layout_file):
		self.elements=[]
		f=open(layout_file,'r')
		tree=etree.parse(f).getroot()
		self.name=tree.attrib['name']
		self.min_height=float(tree.attrib['height'])
		self.min_width=float(tree.attrib['width'])
		self.purpose=tree.find('purpose').text
		cards=tree.findall('card')
		for i in cards:
			x=float(i.find('x').text)
			y=float(i.find('y').text)
			angle=float(i.find('angle').text)
			purpose=i.find('purpose').text
			self.elements.append([x,y,angle,purpose])

	@property
	def largetDimension(self):
		if self.min_height > self.min_width:
			return self.min_height
		else:
			return self.min_width

class QTarotConfig:
	def __init__(self):
		self.APPNAME="QTarot"
		self.APPVERSION="0.2.0"
		self.AUTHOR="ShadowKyogre"
		self.DESCRIPTION="A simple tarot fortune teller."
		self.YEAR="2012"
		self.PAGE="http://shadowkyogre.github.com/QTarot/"

		self.settings=QtCore.QSettings(QtCore.QSettings.IniFormat,
						QtCore.QSettings.UserScope,
						self.AUTHOR,
						self.APPNAME)

		#path for deck is like: "decks:<deck-name>"
		#so default table is "deck:table.png"
		#path for layouts is like "layouts:<layout-name>.lyt"

		self.__SETDIR="%s/%s" \
		%(str(QtGui.QDesktopServices.storageLocation\
		(QtGui.QDesktopServices.DataLocation)), self.APPNAME)

		app_theme_path="%s/decks" %(os.sys.path[0])
		config_theme_path=("%s/decks" %(self.__SETDIR)).replace('//','')

		app_layout_path="%s/layouts" %(os.sys.path[0])
		config_layout_path=("%s/layouts" %(self.__SETDIR)).replace('//','')

		QtCore.QDir.setSearchPaths("layouts", [config_layout_path,app_layout_path])
		QtCore.QDir.setSearchPaths("decks", [config_theme_path,app_theme_path])
		self.sys_icotheme=QtGui.QIcon.themeName()
		self.reset_settings()

	def load_layouts(self):
		self.layouts=od()
		layouts_path=QtCore.QDir("layouts:/")
		for i in layouts_path.entryList():
			if str(i) in (".",".."):
				continue
			lay=TarotLayout(layouts_path.absolutePath()+"/"+str(i))
			self.layouts[lay.name]=lay

	def load_deck(self):
		self.deck=[]
		QtCore.QDir.setSearchPaths("deck", ["decks:%s" %(self.deck_name)])
		self.default_table=QtGui.QPixmap("deck:table.png")
		for i in QtCore.QDir("deck:/").entryList():
			if str(i) in (".","..","table.png","deck.ini"):
				continue
			px=QtGui.QPixmap("deck:%s"%i)
			self.deck.append(px)

	def reset_settings(self):
		self.settings.beginGroup("Reading")
		self.negativity=self.settings.value("negativity",0.5).toDouble()[0]
		self.default_layout=str(self.settings.value("defaultLayout","Ellipse").toString())
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		self.deck_name=str(self.settings.value("deck","coleman-white").toString())
		self.current_icon_override=str(self.settings.value("stIconTheme", \
																	QtCore.QString("")).toPyObject())
		if self.current_icon_override > "":
			QtGui.QIcon.setThemeName(self.current_icon_override)
		else:
			QtGui.QIcon.setThemeName(self.sys_icotheme)
		self.settings.endGroup()

		self.load_deck()
		self.load_layouts()

	def save_settings(self):
		self.settings.beginGroup("Reading")
		self.settings.setValue("negativity",self.negativity)
		self.settings.setValue("defaultLayout",self.default_layout)
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		self.settings.setValue("deck",self.deck_name)
		self.settings.setValue("stIconTheme",self.current_icon_override)
		self.settings.endGroup()

		self.settings.sync()
