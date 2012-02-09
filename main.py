#!/usr/bin/python

import sys
import argparse
from PyQt4 import QtGui,QtCore
from random import sample,random
from qtarotconfig import QTarotConfig
from utilities import ZPGraphicsView,QTarotScene,QTarotItem

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
			filename=QtGui.QFileDialog.getSaveFileName(self, caption="Save Current Reading",
				filter="Images (%s)" %(' '.join(formats)))
		if filename > "":
			fmt=filename.split(".",1)[-1]
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
			qtrcfg.deck_def=str(self.deck_defs.currentText())
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
		print new_def
		print qtrcfg.deck_defs.keys()
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
		self.connect(self.deck_def, QtCore.SIGNAL(("currentIndex"
		"Changed(const QString&)")), self.fillSkinsBox)
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
		self.setWindowTitle('Main window')


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

	app = QtGui.QApplication(sys.argv)
	app.setApplicationName("QTarot")

	qtrcfg = QTarotConfig()
	app.setApplicationName(qtrcfg.APPNAME)
	app.setApplicationVersion(qtrcfg.APPVERSION)

	parser = argparse.ArgumentParser(prog='qtarot',description="A simple")
	parser.add_argument('-l','--layout', help='The layout to use.',default=qtrcfg.default_layout)
	#should probably modified to skins:{default_skin}/table.png
	parser.add_argument('-t','--table', help='File to use as table',default="skin:table.png")
	parser.add_argument('-n','--negativity', help='How often cards are reversed', default=0.5,type=float)
	parser.add_argument('-o','--output', help='Save the reading to this file', default=None)
	args = parser.parse_args(sys.argv[1:])

	ex = QTarot()
	ex.updateTable(fn=args.table)
	ex.newReading(item=args.layout)
	if args.output > "":
		ex.saveReading(filename=args.output)
		sys.exit(app.exec_())
	else:
		ex.show()
		sys.exit(app.exec_())


if __name__ == '__main__':
	main()
