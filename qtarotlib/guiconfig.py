from PyQt4 import QtGui,QtCore
import os
from lxml.etree import DocumentInvalid
from collections import OrderedDict as od

from .xmlobjects import objectify, layout_validator, deck_validator, parser
from . import APPVERSION, AUTHOR, APPNAME, DECKS, DECK_DEFS, LAYOUTS, HTMLTPL

class QTarotConfig:
	def __init__(self):
		self.settings=QtCore.QSettings(QtCore.QSettings.IniFormat,
						QtCore.QSettings.UserScope,
						AUTHOR,
						APPNAME)

		#path for deck skins is like: "skins:<deck-name>"
		#so default table is "skins:{skin}/table.png"
		#deck defs are like "decks:{deck}.xml"
		#path for layouts is like "layouts:<layout-name>.lyt"

		self.userconfdir=QtGui.QDesktopServices.storageLocation\
		(QtGui.QDesktopServices.DataLocation).replace('//','/')

		app_theme_path=DECKS
		config_theme_path=os.path.join(self.userconfdir,"decks")

		app_layout_path=LAYOUTS
		config_layout_path=os.path.join(self.userconfdir,"layouts")

		app_defs_path=DECK_DEFS
		config_defs_path=os.path.join(self.userconfdir,"deck_defs")

		app_htmltpl_path=HTMLTPL
		config_htmltpl_path=os.path.join(self.userconfdir,"htmltpl")

		QtCore.QDir.setSearchPaths("layouts", [config_layout_path,app_layout_path])
		QtCore.QDir.setSearchPaths("skins", [config_theme_path,app_theme_path])
		QtCore.QDir.setSearchPaths("deckdefs", [config_defs_path,app_defs_path])
		QtCore.QDir.setSearchPaths("htmltpl", [config_htmltpl_path,app_htmltpl_path])

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
				layout_validator.assertValid(lay)
				lay=lay.getroot()
				self.layouts[lay.attrib['name']]=lay
			except DocumentInvalid as e:
				print('File',lay,'is invalid for these reason(s):',e,file=os.sys.stderr)

	def setup_skin(self,skin):
		QtCore.QDir.setSearchPaths("skin", ["skins:%s" %(skin)])

	def load_deck_defs(self):
		self.deck_defs=od()
		deck_defs_path=QtCore.QDir("deckdefs:/")
		for i in deck_defs_path.entryList():
			if i in (".",".."):
				continue
			path=deck_defs_path.absoluteFilePath(i)
			deck_def=objectify.parse(path,parser=parser)
			try:
				deck_validator.assertValid(deck_def)
				deck_def=deck_def.getroot()
				self.deck_defs[deck_def.attrib['name']]={}
				self.deck_defs[deck_def.attrib['name']]['definition']=deck_def
				self.deck_defs[deck_def.attrib['name']]['skins']=[]
			except DocumentInvalid as e:
				print('File',path,'is invalid for these reason(s):',e,file=os.sys.stderr)

	def load_skins(self):
		deck_skins_path=QtCore.QDir("skins:/")
		for i in deck_skins_path.entryList():
			if str(i) in (".",".."):
				continue
			if deck_skins_path.exists("skins:/{i}/deck.ini".format(i=i)):
				skin_info=QtCore.QSettings("skins:/{i}/deck.ini".format(i=i), \
							QtCore.QSettings.IniFormat)
				skin_info.beginGroup("Deck Skin")
				for_deck=skin_info.value("definition","")
				if for_deck:
					if for_deck in self.deck_defs:
						if self.deck_defs[for_deck]['definition'].conforms(i):
							self.deck_defs[for_deck]['skins'].append(str(i))
							#copy metadata
						else:
							print(("Deck definition {for_deck}"
							" is not compatible with {i}"
							", skipping {i}...").format(**locals()))
					else:
						print(("Deck definition {for_deck} is not installed"
						", skipping {i}...").format(**locals()))
				else:
					print(("Cannot confirm which deck definitions"
					" {i} is compatible with, skipping...").format(i=i))
				skin_info.endGroup()
			else:
				print(("Cannot confirm which deck definitions"
				" {i} is compatible with, skipping...").format(i=i))

	def reset_settings(self):
		self.settings.beginGroup("Reading")
		self.deck_def=self.settings.value("deck","Rider Waite")
		self.negativity=float(self.settings.value("negativity",0.5))
		self.default_layout=self.settings.value("defaultLayout","Ellipse")
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		#deck_name is now deck_skin
		self.deck_skin=self.settings.value("skin","coleman-white")
		self.current_icon_override=self.settings.value("stIconTheme", "")
		if self.current_icon_override > "":
			QtGui.QIcon.setThemeName(self.current_icon_override)
		else:
			QtGui.QIcon.setThemeName(self.sys_icotheme)
		self.table=self.settings.value("table","skin:table.png")
		self.settings.endGroup()

		self.load_deck_defs()
		self.load_layouts()
		self.load_skins()

	def save_settings(self):
		self.settings.beginGroup("Reading")
		self.settings.setValue("deck",self.deck_def)
		self.settings.setValue("negativity",self.negativity)
		self.settings.setValue("defaultLayout",self.default_layout)
		self.settings.endGroup()

		self.settings.beginGroup("Appearance")
		self.settings.setValue("skin",self.deck_skin)
		self.settings.setValue("stIconTheme",self.current_icon_override)
		self.settings.setValue("table",self.table)
		self.settings.endGroup()

		self.settings.sync()
