#!/usr/bin/python

import os
import re
import argparse

from PyQt4 import QtGui,QtCore
from lxml import objectify, etree, html
from lxml.etree import DocumentInvalid

from urllib.parse import quote as urlquote
from random import sample,random
from collections import OrderedDict as od

from .guiconfig import QTarotConfig
from .xmlobjects import parser, deck_validator 
from . import APPNAME,APPVERSION,AUTHOR,DESCRIPTION,YEAR,PAGE,EMAIL

DECK_IMAGE_ROLE = QtCore.Qt.UserRole
NUMBER_ROLE = QtCore.Qt.UserRole + 1
NORMAL_MEANING_ROLE = QtCore.Qt.UserRole + 2
REVERSED_MEANING_ROLE = QtCore.Qt.UserRole + 3
NO_BODY = re.compile('</?body[^>]*>')

#http://www.sacred-texts.com/tarot/faq.htm#US1909

class DeckEditWidget(QtGui.QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.model = QtGui.QStandardItemModel()
		self.model.setHorizontalHeaderLabels(["Name", "Affiliation"])

		layout = QtGui.QVBoxLayout(self)

		self.cview = QtGui.QTableView()
		self.cview.verticalHeader().hide()
		self.cview.horizontalHeader().setStretchLastSection(True)
		self.cview.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
		self.cview.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.cview.setDragEnabled(True)
		self.cview.setAcceptDrops(True)
		self.cview.setDropIndicatorShown(True)
		self.cview.setModel(self.model)
		self.cview.resizeColumnsToContents()

		self.iview = QtGui.QListView()
		self.cview.selectionModel().currentChanged.connect(self.descendList)

		self.pvw = ItemPreviewWidget(self.model)
		self.pvw.layout().setMargin(0)
		self.pvw.blankOut()

		removeIButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-delete"), "Delete card")
		removeCButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-delete"), "Delete suite")
		addIButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-add"), "Add card")
		addCButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-add"), "Add suite")

		removeIButton.clicked.connect(self.removeItem)
		removeCButton.clicked.connect(self.removeCategory)
		addIButton.clicked.connect(self.addItem)
		addCButton.clicked.connect(self.addCategory)

		self.deck_name = QtGui.QLineEdit()
		self.deck_name.setPlaceholderText("Deck Name")
		self.author = QtGui.QLineEdit()
		self.author.setPlaceholderText("Author")
		self.source = QtGui.QLineEdit()
		self.source.setPlaceholderText("Source")

		splitty = QtGui.QSplitter()

		hold_me = QtGui.QWidget()
		hold_me_layout = QtGui.QVBoxLayout(hold_me)
		hold_me_layout.setMargin(0)

		hold_me_close = QtGui.QWidget()
		hold_me_close_layout = QtGui.QVBoxLayout(hold_me_close)
		hold_me_close_layout.setMargin(0)

		splitty.addWidget(hold_me)
		splitty.addWidget(hold_me_close)
		splitty.addWidget(self.pvw)

		layout.addWidget(self.deck_name)
		layout.addWidget(self.author)
		layout.addWidget(self.source)

		hold_me_layout.addWidget(self.cview)
		hold_me_layout.addWidget(addCButton)
		hold_me_layout.addWidget(removeCButton)

		hold_me_close_layout.addWidget(self.iview)
		hold_me_close_layout.addWidget(addIButton)
		hold_me_close_layout.addWidget(removeIButton)

		layout.addWidget(splitty)

		self.setupModel()

	def descendList(self, idx, pidx):
		if self.iview.model() is not self.model:
			self.iview.setModel(self.model)
			self.iview.selectionModel().currentChanged.connect(self.pvw.updatePreview)
		if idx.column() > 0:
			idx = idx.sibling(idx.row(), 0)
		self.iview.setRootIndex(idx)

	def addItem(self):
		idx = self.cview.currentIndex()
		if idx.column() > 0:
			idx = idx.sibling(idx.row(), 0)
		if idx.isValid():
			paritem = self.model.itemFromIndex(idx)

			item = QtGui.QStandardItem()
			item.setText("Edit meh!")
			item.setFlags(QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)

			item.setData("document-edit", DECK_IMAGE_ROLE)
			item.setData("I <i>am</i> rich!", NORMAL_MEANING_ROLE)
			item.setData("I <i>am</i> poor!", REVERSED_MEANING_ROLE)

			paritem.appendRow(item)
			self.iview.setCurrentIndex(item.index())

	def addCategory(self):
		item = QtGui.QStandardItem()
		item.setText("Edit meh!")
		item.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsUserCheckable)
		item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

		affil = QtGui.QStandardItem()
		affil.setText("Dunno")
		affil.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable)

		self.model.appendRow([item, affil])

	def removeItem(self):
		idx = self.iview.currentIndex()
		if idx.isValid():
			self.pvw.blankOut()
			paritem = self.model.itemFromIndex(idx.parent())
			paritem.takeRow(idx.row())

	def removeCategory(self):
		idx = self.cview.currentIndex()
		if idx.isValid():
			btn = QtGui.QMessageBox.warning(self, "Confirm delete category", 
			                                "Are you sure you want to delete this?", 
			                                buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
			if btn == QtGui.QMessageBox.Yes:
				self.pvw.blankOut()
				self.model.takeRow(idx.row())

	def toXml(self):
		xmlobj = etree.fromstring('<deck></deck>')
		xmlobj.attrib['name']=self.deck_name.text()
		etree.SubElement(xmlobj, 'author').text = self.author.text()
		etree.SubElement(xmlobj, 'source').text = self.source.text()

		for sidx in range(self.model.rowCount()):
			suite_item = self.model.item(sidx)
			suite_el = etree.SubElement(xmlobj, 'suit')
			suite_el.attrib['affinity'] = self.model.item(sidx, 1).text()
			suite_el.attrib['name'] = suite_item.text()
			suite_el.attrib['nosuitname'] = str(True if suite_item.checkState() == QtCore.Qt.Checked else False).lower()
			for cidx in range(suite_item.rowCount()):
				card_item = suite_item.child(cidx)

				card_el = etree.SubElement(suite_el, 'card')
				card_el.attrib['name'] = card_item.text()

				number_el = etree.SubElement(card_el, 'number')
				number_el.text = card_item.data(NUMBER_ROLE)

				file_el = etree.SubElement(card_el, 'file')
				file_el.text = urlquote(card_item.data(DECK_IMAGE_ROLE))

				meaning_el = etree.SubElement(card_el, 'meaning')
				normal_el = etree.SubElement(meaning_el, 'normal')
				reversed_el = etree.SubElement(meaning_el, 'reversed')
				normal_el.text = card_item.data(NORMAL_MEANING_ROLE)
				reversed_el.text = card_item.data(REVERSED_MEANING_ROLE)

				for src_idx in range(card_item.rowCount()):
					src_item = card_item.child(src_idx)
					source_el = etree.SubElement(card_el, 'source')
					source_el.text = src_item.text()

		return xmlobj

	def fromXml(self, xmlobj):
		self.model.clear()
		self.deck_name.setText(xmlobj.attrib['name'])
		self.author.setText(xmlobj.author.text)
		self.source.setText(xmlobj.source.text)

		for suit_el in xmlobj.iterchildren(tag='suit'):
			suit_item = QtGui.QStandardItem()
			suit_item.setText(suit_el.attrib['name'])
			suit_item.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsUserCheckable)
			suit_item.setData(QtCore.Qt.Checked if suit_el.attrib['nosuitname'] else QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

			affil = QtGui.QStandardItem()
			affil.setText(suit_el.attrib["affinity"])
			affil.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable)

			self.model.appendRow([suit_item, affil])

			for card_el in suit_el.iterchildren(tag='card'):
				card_item = QtGui.QStandardItem()
				card_item.setText(card_el.attrib['name'])
				card_item.setFlags(QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)

				card_item.setData(card_el.number.text, NUMBER_ROLE)
				card_item.setData(card_el.file.text, DECK_IMAGE_ROLE)
				card_item.setData(card_el.meaning.normal.text, NORMAL_MEANING_ROLE)
				card_item.setData(card_el.meaning.reversed.text, REVERSED_MEANING_ROLE)

				for source_el in card_el.iterchildren(tag='source'):
					source_item = QtGui.QStandardItem()
					source_item.setText(source_el.text)
					card_item.appendRow(source_item)

				suit_item.appendRow(card_item)

	def setupModel(self, filename=None):
		self.model.clear()
		self.author.setText("")
		self.source.setText("")
		dummy_deck_contents = od((
		                        ('Graphics', ('gimp', 'mypaint')),
		                        ('Editors', ('gvim', 'wine')),
		))
		for key, val in dummy_deck_contents.items():
			item = QtGui.QStandardItem()
			item.setText(key)
			item.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsUserCheckable)
			item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

			affil = QtGui.QStandardItem()
			affil.setText("durp")
			affil.setFlags(QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable)
			for v in val:
				child_item = QtGui.QStandardItem()
				child_item.setText(v.upper())
				child_item.setData('IX', NUMBER_ROLE)
				child_item.setData(v, DECK_IMAGE_ROLE)
				child_item.setData("I <i>am</i> rich!", NORMAL_MEANING_ROLE)
				child_item.setData("I <i>am</i> poor!", REVERSED_MEANING_ROLE)
				item.appendRow(child_item)
				child_item.setFlags(QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.model.appendRow([item, affil])

class ItemPreviewWidget(QtGui.QWidget):
	def __init__(self, model, parent=None):
		super().__init__(parent=parent)
		layout = QtGui.QVBoxLayout(self)

		self.label = QtGui.QLabel()
		self.edit_ico_name = QtGui.QLineEdit()
		self.edit_ico_name.setPlaceholderText("Card Theme Filepath")
		self.edit_card_num = QtGui.QLineEdit()
		self.edit_card_num.setPlaceholderText("Card Number")
		self.edit_card_name = QtGui.QLineEdit()
		self.edit_card_name.setPlaceholderText("Card Name")

		self.combobox = QtGui.QComboBox()
		self.combobox.setModel(model)
		self.combobox.currentIndexChanged['int'].connect(self.changeParent)
		self.edit_ico_name.textEdited.connect(self.editImageText)
		self.edit_card_name.textEdited.connect(self.editNameText)
		self.edit_card_num.textEdited.connect(self.editNumText)

		self.normal_meaning = QtGui.QTextEdit()
		self.normal_meaning.textChanged.connect(self.editNormalText)
		self.reversed_meaning = QtGui.QTextEdit()
		self.reversed_meaning.textChanged.connect(self.editReversedText)

		self.sources_list = QtGui.QListView()
		self.sources_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

		self.splitty = QtGui.QSplitter()
		self.splitty.setOrientation(QtCore.Qt.Vertical)

		self.smallSplitty = QtGui.QSplitter()
		self.smallSplitty.setOrientation(QtCore.Qt.Horizontal)
		self.smallSplitty.addWidget(self.normal_meaning)
		self.smallSplitty.addWidget(self.reversed_meaning)

		sources_widget = QtGui.QWidget()
		sources_layout = QtGui.QGridLayout(sources_widget)
		sources_layout.setMargin(0)

		addSButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-add"), "Add Source")
		addSButton.clicked.connect(self.addSource)
		removeSButton = QtGui.QPushButton(QtGui.QIcon.fromTheme("edit-delete"), "Remove Source")
		removeSButton.clicked.connect(self.removeSource)

		sources_layout.addWidget(self.sources_list, 0, 0, 1, 2)
		sources_layout.addWidget(addSButton, 1, 0)
		sources_layout.addWidget(removeSButton, 1, 1)

		self.splitty.addWidget(self.smallSplitty)
		self.splitty.addWidget(sources_widget)

		layout.addWidget(self.combobox)
		layout.addWidget(self.edit_card_name)
		layout.addWidget(self.edit_card_num)
		layout.addWidget(self.edit_ico_name)
		layout.addWidget(self.label)
		layout.addWidget(self.splitty)
		self._idx = None

	def addSource(self):
		if self._idx is not None and self._idx.isValid():
			item = self._idx.model().itemFromIndex(self._idx)
			subitem = QtGui.QStandardItem("Edit me!")
			item.appendRow(subitem)

	def removeSource(self):
		to_remove = [QtCore.QPersistentModelIndex(idx) for idx in self.sources_list.selectedIndexes()[::-1]]
		item = self._idx.model().itemFromIndex(self._idx)
		for idx in to_remove:
			item.takeRow(idx.row())

	def editReversedText(self):
		if self._idx is not None and self._idx.isValid():
			dirty_html = self.reversed_meaning.toHtml()
			htmlbase = html.fromstring(dirty_html).cssselect('body')[0]
			clean_html = NO_BODY.sub("", etree.tostring(htmlbase, pretty_print=True).decode('utf-8'))
			self._idx.model().itemFromIndex(self._idx).setData(clean_html, REVERSED_MEANING_ROLE)

	def editNormalText(self):
		if self._idx is not None and self._idx.isValid():
			dirty_html = self.normal_meaning.toHtml()
			htmlbase = html.fromstring(dirty_html).cssselect('body')[0]
			clean_html = NO_BODY.sub("", etree.tostring(htmlbase, pretty_print=True).decode('utf-8'))
			self._idx.model().itemFromIndex(self._idx).setData(clean_html, NORMAL_MEANING_ROLE)

	def editNameText(self, text):
		if self._idx is not None and self._idx.isValid():
			self._idx.model().itemFromIndex(self._idx).setText(text)

	def editNumText(self, text):
		if self._idx is not None and self._idx.isValid():
			self._idx.model().itemFromIndex(self._idx).setData(text, NUMBER_ROLE)

	def editImageText(self, text):
		if self._idx is not None and self._idx.isValid():
			self._idx.model().itemFromIndex(self._idx).setData(text, DECK_IMAGE_ROLE)
			self.label.setPixmap(QtGui.QIcon.fromTheme(self._idx.data(DECK_IMAGE_ROLE)).pixmap(256, 256))

	def changeParent(self, idx):
		print("idx is:", self._idx)
		if self._idx is not None and self._idx.isValid():
			print(self._idx.isValid(), self._idx.data(0))
			item = self._idx.model().itemFromIndex(self._idx)
			orig_parent = item.parent()
			new_parent = self.combobox.model().item(idx)
			print(orig_parent, new_parent, orig_parent is new_parent)
			if orig_parent is not new_parent and new_parent is not None:
				orig_parent.takeRow(item.row())
				new_parent.appendRow(item)
				#self._idx = self.parent().parent().currentIndex() # <- this points to an invalid idx
				print("current index is now", self._idx, self._idx.data(0) if self._idx is not None else None)
				print("changed parents")

			print(orig_parent.rowCount())
			if orig_parent.rowCount() == 0:
				print("Hiding due to orig parent having no children")
				self.blankOut()
		else:
			print("invalid index or is none")
			self.blankOut()
		print("---")

	def blankOut(self):
		self.label.setPixmap(QtGui.QPixmap(256, 256))
		self.label.hide()
		self.edit_ico_name.setText("")
		self.edit_ico_name.hide()
		self.edit_card_name.setText("")
		self.edit_card_name.hide()
		self.edit_card_num.setText("")
		self.edit_card_num.hide()
		self.normal_meaning.setText("")
		self.reversed_meaning.setText("")
		self.combobox.hide()
		self.splitty.hide()
		self.sources_list.setModel(None)
		self._idx = None

	def updatePreview(self, idx, pidx):
		print("Updating widget")
		#print(idx.isValid(), idx.parent().isValid())
		if idx.isValid() and idx.parent().isValid():
			self._idx = idx
			self.sources_list.setModel(idx.model())
			self.sources_list.setRootIndex(idx)
			self.label.setPixmap(QtGui.QIcon.fromTheme(idx.data(DECK_IMAGE_ROLE)).pixmap(256, 256))
			self.label.show()
			self.combobox.setCurrentIndex(idx.parent().row())
			self.combobox.show()
			self.edit_ico_name.setText(idx.data(DECK_IMAGE_ROLE))
			self.edit_ico_name.show()
			self.edit_card_name.setText(idx.data(QtCore.Qt.DisplayRole))
			self.edit_card_name.show()
			self.edit_card_num.setText(idx.data(NUMBER_ROLE))
			self.edit_card_num.show()
			self.splitty.show()

			self.normal_meaning.setHtml(idx.data(NORMAL_MEANING_ROLE))
			self.reversed_meaning.setHtml(idx.data(REVERSED_MEANING_ROLE))
		else:
			self.combobox.setCurrentIndex(idx.parent().row())
			self.blankOut()

class QTarotDeckEdit(QtGui.QMainWindow):

	def __init__(self):
		super().__init__()
		self.initUI()

	def newDeck(self):
		self.view.setupModel()

	def openDeck(self, filename=None):
		if not filename:
			filename = str(QtGui.QFileDialog.getOpenFileName(self, caption="Open deck", filter="XML (*.xml)"))
		if filename:
			try:
				print("opening deck def " + filename)
				xmlobj = objectify.parse(filename, parser=parser).getroot()
				deck_validator.assertValid(xmlobj)
				self.view.fromXml(xmlobj)
			except DocumentInvalid as e:
				print(filename, "was an invalid deck xml file, starting empty.")
			except OSError as e:
				print(filename, "doesn't exist, starting empty.")

	def saveDeck(self, filename=None):
		if not filename:
			filename=str(QtGui.QFileDialog.getSaveFileName(self, caption="Save deck",
				filter="XML (*.xml)"))
		if filename:
			print("saving deck def " + filename)
			xmlobj = self.view.toXml()
			tree_string = etree.tostring(xmlobj, pretty_print=True).decode('utf-8')
			if not filename:
				filename = QtGui.QFileDialog.getSaveFileName(self, caption="Save deck", filter="*.xml" )
			if filename:
				with open(filename, 'w', encoding='utf-8') as f:
					f.write(tree_string)

	def about(self):
		QtGui.QMessageBox.about (self, "About {}".format(APPNAME),
		("<center><big><b>{0} Deck Editor {1}</b></big>"
		"<br />{2}<br />(C) <a href=\"mailto:{3}\">{4}</a> {5}<br />"
		"<a href=\"{6}\">{0} Homepage</a></center>")\
		.format(APPNAME,APPVERSION,DESCRIPTION,EMAIL,AUTHOR,YEAR,PAGE))

	def initUI(self):
		self.setWindowTitle(app.applicationName())
		self.view = DeckEditWidget(parent=self)
		self.setCentralWidget(self.view)
		self.setDockNestingEnabled(True)

		exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(self.close)

		newDeckAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-new'), 'Create a new deck definition', self)
		newDeckAction.setShortcut('Ctrl+N')
		newDeckAction.setStatusTip('Create a new deck definition')
		newDeckAction.triggered.connect(self.newDeck)

		saveAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-save'), 'Save', self)
		saveAction.setShortcut('Ctrl+S')
		saveAction.setStatusTip('Save')
		saveAction.triggered.connect(self.saveDeck)

		openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'), 'Edit another deck definition', self)
		openAction.setShortcut('Ctrl+O')
		openAction.setStatusTip('Edit another deck definition')
		openAction.triggered.connect(self.openDeck)
		#self.findChildren(QtGui.QDockWidget, QString name = QString())

		'''
		settingsAction = QtGui.QAction(QtGui.QIcon.fromTheme('preferences-other'), 'Settings', self)
		settingsAction.setStatusTip('Settings')
		settingsAction.triggered.connect(self.settings)

		browsingAction = QtGui.QAction(QtGui.QIcon.fromTheme('applications-graphics'), 'Browse Decks', self)
		browsingAction.setStatusTip('Browse all deck definitions and deck skins you have')
		browsingAction.triggered.connect(self.browseDecks)
		'''

		aboutAction=QtGui.QAction(QtGui.QIcon.fromTheme('help-about'), 'About', self)
		aboutAction.triggered.connect(self.about)

		st=self.statusBar()

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(exitAction)
		fileMenu.addAction(newDeckAction)
		#fileMenu.addAction(newChooseAction)
		fileMenu.addAction(openAction)
		fileMenu.addAction(saveAction)
		#fileMenu.addAction(settingsAction)

		toolbar = self.addToolBar('Exit')
		toolbar.addAction(exitAction)
		toolbar.addAction(newDeckAction)
		toolbar.addAction(openAction)
		toolbar.addAction(saveAction)
		#toolbar.addAction(browsingAction)
		#toolbar.addAction(settingsAction)
		toolbar.addAction(aboutAction)

		#self.resize(500, 400)
		self.setWindowTitle('QTarot')

def main():
	global formats
	global app
	global qtrcfg

	formats=set(["*."+''.join(i).lower() for i in \
		QtGui.QImageWriter.supportedImageFormats()])

	formats=sorted(list(formats),key=str.lower)
	try:
		formats.remove('*.bw')
	except ValueError:
		pass
	try:
		formats.remove('*.rgb')
	except ValueError:
		pass
	try:
		formats.remove('*.rgba')
	except ValueError:
		pass

	app = QtGui.QApplication(os.sys.argv)

	app.setApplicationName(APPNAME)
	app.setApplicationVersion(APPVERSION)
	app.setWindowIcon(QtGui.QIcon.fromTheme("qtarot"))

	sys_icotheme = QtGui.QIcon.themeName()

	qtrcfg = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,
	                          AUTHOR, APPNAME)

	qtrcfg.beginGroup("Appearance")
	#deck_name is now deck_skin
	current_icon_override = qtrcfg.value("stIconTheme", "")
	if current_icon_override > "":
		QtGui.QIcon.setThemeName(current_icon_override)
	else:
		QtGui.QIcon.setThemeName(sys_icotheme)
	qtrcfg.endGroup()

	'''
	parser = argparse.ArgumentParser(prog='qtarot',description="A simple tarot fortune teller")
	parser.add_argument('-l','--layout', help='The layout to use.',default=qtrcfg.default_layout,choices=list(qtrcfg.layouts.keys()))
	parser.add_argument('-t','--table', help='File to use as table',default=qtrcfg.table)
	parser.add_argument('-n','--negativity', help='How often cards are reversed', default=qtrcfg.negativity,type=float)
	parser.add_argument('-o','--output', help='Save the reading to this file', default=None)
	parser.add_argument('-d','--deck', help='Deck definition to use', default=qtrcfg.deck_def, choices=list(qtrcfg.deck_defs.keys()))
	parser.add_argument('-s','--skin', help='Deck skin to use (valid values depend on deck definition)',default=qtrcfg.deck_skin)
	args = parser.parse_args(os.sys.argv[1:])
	'''

	ex = QTarotDeckEdit()
	'''
	ex.updateTable(fn=args.table)
	if args.deck != qtrcfg.deck_def or  args.skin != qtrcfg.deck_skin:
		if args.skin not in qtrcfg.deck_defs[args.deck]['skins']:
			print(("Invalid skin \"{}\" for {}!\n"
			"Valid skins: {}").format(args.skin,args.deck,qtrcfg.deck_defs[args.deck]['skins']))
			exit(1)
	ex.newReading(item=args.layout,neg=args.negativity,skin=args.skin,deck=args.deck)

	if args.output:
		ex.saveReading(filename=args.output)
		#os.sys.exit(app.exec_())
	else:
		ex.show()
		os.sys.exit(app.exec_())
	'''
	ex.show()
	os.sys.exit(app.exec_())

if __name__ == "__main__":
	main()
