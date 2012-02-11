#!/usr/bin/python

import os
import argparse
from PyQt4 import QtGui,QtCore
from random import sample,random
from qtarotconfig import QTarotConfig
from utilities import ZPGraphicsView,QTarotScene,QTarotItem

#http://www.sacred-texts.com/tarot/faq.htm#US1909

class QTarot(QtGui.QMainWindow):

	def __init__(self):
		super(QTarot, self).__init__()
		self.initUI()

	def updateCards(self):
		for item in self.scene.items():
			if isinstance(item,QTarotItem):
				item.refresh()
				item.reposition()
		self.scene.invalidate()

	def updateTable(self,fn="skin:table.png"):
		self.scene.table=QtGui.QPixmap(fn)
		for item in self.scene.items():
			if isinstance(item,QTarotItem):
				item.refresh()
				item.reposition()
		self.scene.invalidate()

	def pickTable(self):
		filename=QtGui.QFileDialog.getOpenFileName (self, caption="Open a new file", \
		directory=QtCore.QDir.homePath(), filter="Images (%s)" %(' '.join(formats)))
		if filename > "":
			self.updateTable(fn=filename)

	def saveReading(self,filename=None):
		if filename <= "":
			filename=str(QtGui.QFileDialog.getSaveFileName(self, caption="Save Current Reading",
				filter="Images (%s);;HTML (*.html)" %(' '.join(formats))))
		if filename > "":
			fmt=filename.split(".",1)[-1]
			if fmt == 'html':
				store_here="{}.files".format(filename.replace(".html",""))
				if not os.path.exists(store_here):
					os.makedirs(store_here)
				pixMap = QtGui.QPixmap(self.scene.sceneRect().width(),self.scene.sceneRect().height())
				painter=QtGui.QPainter(pixMap)
				self.scene.render(painter)
				painter.end()
				reading_px=os.path.join(store_here,"reading.png")
				reading_pxh=os.path.join(os.path.basename(store_here),"reading.png")
				pixMap.save(reading_px,format='png')

				f=open(filename,'wb')

				import shutil
				f2=open(os.path.join(os.sys.path[0],'export_read.html'))
				template=f2.read()
				f2.close()

				cards=""
				layout="&lt;Unknown&gt;"
				deck_def_credits=""
				layout_credits=""
				for item in self.scene.items():
					if isinstance(item,QTarotItem):
						if layout == "&lt;Unknown&gt;":
							layout=item.posData.getparent().get('name')
							layout_credits=self.generateCredits(item.posData)
						if not deck_def_credits:
							deck_def_credits=self.generateCredits(item.card)
						text,copy_from,save_file=self.generateCardText(item.card,\
						item.rev,item.posData.purpose.text,newfp=store_here)
						shutil.copy(copy_from,save_file)
						cards=''.join([cards,text])

				f.write(template.format(cards=cards,deck=qtrcfg.deck_def,\
				layout=layout,reading_px=reading_pxh,layout_credits=layout_credits,\
				deck_def_credits=deck_def_credits))
				f.close()
			else:
				pixMap = QtGui.QPixmap(self.scene.sceneRect().width(),self.scene.sceneRect().height())
				painter=QtGui.QPainter(pixMap)
				#here=QtCore.QRectF(self.scene.sceneRect().toRect())
				#self.scene.render(painter, here, here)
				self.scene.render(painter)
				painter.end()
				pixMap.save(filename,format=fmt)

	def newReading(self,item=None):
		if item is None or item == False:
			item,ok = QtGui.QInputDialog.getItem(self, "Generate new reading",
			"Layout to use:", qtrcfg.layouts.keys(), 0, False)
			if ok and not item.isEmpty():
				lay=qtrcfg.layouts[str(item)]
				self.currentLayout=lay
			else:
				return
		else:
			lay=qtrcfg.layouts[str(item)]
			self.currentLayout=lay
		self.scene.clear()
		self.scene.invalidate()

		offset=self.scene.calculateOffset()
		draws=sample(qtrcfg.deck_defs[qtrcfg.deck_def]\
			['definition'].cards(),len(lay.pos[:]))

		for (card,placement) in zip(draws, lay.pos[:]):
			#rectitem=self.scene.addRect(0,0,1/lay.largetDimension()*self.scene.smallerD,\
			#2/lay.largetDimension()*self.scene.smallerD,\
			#pen=QtGui.QPen(QtGui.QColor("red"),2),\
			#brush=QtGui.QBrush(QtGui.QColor("indigo")))

			rev=(random() <= qtrcfg.negativity)
			rectitem=self.scene.addTarot(card,placement,rev)
			rectitem.reposition()
			rectitem.emitter.showName.connect(self.statusBar().showMessage)
			rectitem.emitter.clearName.connect(self.statusBar().clearMessage)
			rectitem.emitter.showAllInfo.connect(self.cardInfoDialog)

	def generateCredits(self, card):
		def_data = card.getroottree().getroot()
		authors=[]
		sources=[]
		if def_data.tag == "deck":
			copytype="Deck definition"
		elif def_data.tag == "layout":
			copytype="Layout"
		else:
			copytype="&lt;Unknown&gt;"

		for a in def_data.author[:]:
			if a.text:
				authors.append(a.text)
			else:
				authors.append("&lt;Unknown&gt;")

		from urlparse import urlparse
		for s in def_data.source[:]:
			if s.text:
				if urlparse(s.text).scheme:
					sources.append(("<a href=\"{s.text}\">"
					"{s.text}</a>").format(s=s))
				else:
					sources.append(s.text)
			else:
				sources.append("&lt;Unknown&gt;")

		authors=', '.join(authors)
		sources='<br />\n'.join(sources)
		return ("{copytype} (c) {authors}"
		"<br />Sources consulted:<br />"
		"\n{sources}<br />\n").format(**locals())

	def generateCardText(self, card, reverse=None, purpose=None, newfp=None):
		f=open(os.path.join(os.sys.path[0],'card_info_template.html'))
		template=f.read()
		f.close()
		reading_specific=("<br />\n\t\tCurrent status: {status}<br />"
		"\n\t\tPurpose in layout: {purp}") if reverse is not None \
		and purpose is not None else ""
		if newfp:
			oldfn=str(QtCore.QDir("skin:/")\
			.absoluteFilePath(str(card.file.text)))
			fn=os.path.join(os.path.basename(newfp),os.path.basename(oldfn))
			newfn=os.path.join(newfp,os.path.basename(oldfn))
		else:
			fn="skin:{fn}".format(fn=str(card.file.text))
		revtext=card.meaning.reversed.text if card.meaning.reversed.text else "Cannot be reversed"
		result=template.format(fn=fn, name=card.fullname(), \
		n=card.number, suit=card.getparent().get('name'), \
		af=card.getparent().get('affinity'), \
		normal=card.meaning.normal.text, \
		reverse=revtext,
		reading_specific=reading_specific.format(purp=purpose,\
		status="Reversed" if reverse else "Normal"))
		if newfp:
			return result,oldfn,newfn
		else:
			return result

	def cardInfoDialog(self, card, reverse, posdata):
		dialog=QtGui.QDialog(self)
		layout=QtGui.QVBoxLayout(dialog)
		deck_def_credits=self.generateCredits(card)
		layout_credits=self.generateCredits(posdata)
		full_information=self.generateCardText(card,reverse,posdata.purpose.text)

		textdisplay=QtGui.QTextBrowser(dialog)
		textdisplay.setReadOnly(True)
		textdisplay.setAcceptRichText(True)
		textdisplay.setText(("{deck_def_credits}"
		"{layout_credits}"
		"{full_information}").format(**locals()))
		textdisplay.setOpenLinks(False)
		textdisplay.anchorClicked.connect(lambda url: QtGui.\
						QDesktopServices.\
						openUrl(QtCore.QUrl(url)))

		layout.addWidget(textdisplay)
		dialog.setWindowTitle("Info on {}".format(card.fullname()))
		dialog.open()

	def settingsWrite(self):
		self.settingsChange()
		qtrcfg.save_settings()
		self.settings_dialog.close()

	def settingsChange(self):
		qtrcfg.negativity=self.negativity.value()
		reload_deck=False
		if str(self.deck_skin.currentText()) != qtrcfg.deck_skin:
			qtrcfg.deck_skin=str(self.deck_skin.currentText())
			reload_deck=True
		if str(self.deck_def.currentText()) != qtrcfg.deck_def:
			qtrcfg.deck_def=str(self.deck_def.currentText())
			reload_deck=False
			#pop up a message box saying to save reading or something
		qtrcfg.default_layout=str(self.default_layout.currentText())
		qtrcfg.load_deck_defs()
		qtrcfg.load_layouts()
		qtrcfg.load_skins()
		qtrcfg.setup_skin()
		qtrcfg.current_icon_override=str(self.ico_theme.text())
		if reload_deck:
			self.updateCards()

	def settingsReset(self):
		qtrcfg.reset_settings()
		self.updateSettingsWidgets()

	def fillSkinsBox(self, new_def):
		if qtrcfg.deck_defs.has_key(str(new_def)):
			skins_list=qtrcfg.deck_defs[str(new_def)]['skins']
		else:
			skins_list=[]
		self.deck_skin.clear()
		self.deck_skin.addItems(skins_list)
		idx=self.deck_skin.findText(qtrcfg.deck_skin)
		self.deck_skin.setCurrentIndex(idx)

	def updateSettingsWidgets(self):
		self.default_layout.addItems(qtrcfg.layouts.keys())
		idx=self.default_layout.findText(qtrcfg.default_layout)
		self.default_layout.setCurrentIndex(idx)
		self.negativity.setValue(qtrcfg.negativity)
		#decks=list(QtCore.QDir("skins:/").entryList())
		#decks.remove(".")
		#decks.remove("..")
		self.deck_def.addItems(qtrcfg.deck_defs.keys())
		idx=self.deck_def.findText(qtrcfg.deck_def)
		self.deck_def.setCurrentIndex(idx)
		self.ico_theme.setText(qtrcfg.current_icon_override)

	def settings(self):
		self.settings_dialog=QtGui.QDialog(self)
		self.settings_dialog.setWindowTitle("Settings")

		label=QtGui.QLabel(("Note: These will not take effect"
		" until you make another reading"),self.settings_dialog)
		groupbox=QtGui.QGroupBox("Reading",self.settings_dialog)
		groupbox2=QtGui.QGroupBox("Appearance",self.settings_dialog)
		vbox=QtGui.QVBoxLayout(self.settings_dialog)
		gvbox=QtGui.QGridLayout(groupbox)
		gvbox2=QtGui.QGridLayout(groupbox2)

		self.negativity=QtGui.QDoubleSpinBox(groupbox)
		self.default_layout=QtGui.QComboBox(groupbox)
		self.negativity.setSingleStep(0.1)
		self.negativity.setRange(0,1)

		self.deck_def=QtGui.QComboBox(groupbox2)
		self.deck_def.currentIndexChanged['QString'].connect(self.fillSkinsBox)
		self.deck_skin=QtGui.QComboBox(groupbox2)
		self.ico_theme=QtGui.QLineEdit(groupbox2)
		self.ico_theme.setToolTip(("You should only set this if Qt isn't"
		" detecting your icon theme.\n"
		"Currently detected icon theme: %s\n"
		"Settings will take effect after a restart") \
		% (qtrcfg.sys_icotheme))

		gvbox.addWidget(QtGui.QLabel("Negativity"),0,0)
		gvbox.addWidget(self.negativity,0,1)
		gvbox.addWidget(QtGui.QLabel("Default Layout"),1,0)
		gvbox.addWidget(self.default_layout,1,1)
		gvbox2.addWidget(QtGui.QLabel("Deck Definitions"),0,0)
		gvbox2.addWidget(self.deck_def,0,1)
		gvbox2.addWidget(QtGui.QLabel("Deck Skins"),2,0)
		gvbox2.addWidget(self.deck_skin,2,1)
		gvbox2.addWidget(QtGui.QLabel("Override Icon Theme"),3,0)
		gvbox2.addWidget(self.ico_theme,3,1)

		buttonbox=QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
		resetbutton=buttonbox.addButton(QtGui.QDialogButtonBox.Reset)
		okbutton=buttonbox.addButton(QtGui.QDialogButtonBox.Ok)
		applybutton=buttonbox.addButton(QtGui.QDialogButtonBox.Apply)
		cancelbutton=buttonbox.addButton(QtGui.QDialogButtonBox.Cancel)

		resetbutton.clicked.connect(self.settingsReset)
		okbutton.clicked.connect(self.settingsWrite)
		applybutton.clicked.connect(self.settingsChange)
		cancelbutton.clicked.connect(self.settings_dialog.close)
		vbox.addWidget(label)
		vbox.addWidget(groupbox)
		vbox.addWidget(groupbox2)
		vbox.addWidget(buttonbox)

		self.updateSettingsWidgets()
		self.settings_dialog.exec_()

	def initUI(self):
		self.setWindowTitle(app.applicationName())
		self.scene=QTarotScene(self)

		self.view=ZPGraphicsView(self.scene,self)

		self.setCentralWidget(self.view)

		exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(self.close)

		newLayAction = QtGui.QAction(QtGui.QIcon.fromTheme('view-refresh'), 'Reload', self)
		newLayAction.setShortcut('Ctrl+R')
		newLayAction.setStatusTip('Reload')
		newLayAction.triggered.connect(self.newReading)

		saveAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-save'), 'Save', self)
		saveAction.setShortcut('Ctrl+S')
		saveAction.setStatusTip('Save')
		saveAction.triggered.connect(self.saveReading)

		openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'), 'Change Table', self)
		openAction.setShortcut('Ctrl+O')
		openAction.setStatusTip('Change the table image')
		openAction.triggered.connect(self.pickTable)

		settingsAction = QtGui.QAction(QtGui.QIcon.fromTheme('preferences-other'), 'Settings', self)
		settingsAction.setStatusTip('Settings')
		settingsAction.triggered.connect(self.settings)

		st=self.statusBar()

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(exitAction)
		fileMenu.addAction(newLayAction)
		fileMenu.addAction(openAction)
		fileMenu.addAction(saveAction)
		fileMenu.addAction(settingsAction)

		toolbar = self.addToolBar('Exit')
		toolbar.addAction(exitAction)
		toolbar.addAction(newLayAction)
		toolbar.addAction(openAction)
		toolbar.addAction(saveAction)
		toolbar.addAction(settingsAction)

		#self.resize(500, 400)
		self.setWindowTitle('QTarot')


def main():
	global formats
	global app
	global qtrcfg

	formats=set(["*."+str(QtCore.QString(i)).lower() for i in \
	QtGui.QImageWriter.supportedImageFormats ()])
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

	app.setApplicationName(QTarotConfig.APPNAME)
	app.setApplicationVersion(QTarotConfig.APPVERSION)

	qtrcfg = QTarotConfig()

	parser = argparse.ArgumentParser(prog='qtarot',description="A simple")
	parser.add_argument('-l','--layout', help='The layout to use.',default=qtrcfg.default_layout)
	#should probably modified to skins:{default_skin}/table.png
	parser.add_argument('-t','--table', help='File to use as table',default="skin:table.png")
	parser.add_argument('-n','--negativity', help='How often cards are reversed', default=0.5,type=float)
	parser.add_argument('-o','--output', help='Save the reading to this file', default=None)
	args = parser.parse_args(os.sys.argv[1:])

	ex = QTarot()
	ex.updateTable(fn=args.table)
	ex.newReading(item=args.layout)
	if args.output > "":
		ex.saveReading(filename=args.output)
		os.sys.exit(app.exec_())
	else:
		ex.show()
		os.sys.exit(app.exec_())


if __name__ == '__main__':
	main()
