#!/usr/bin/python

import sys
from PyQt4 import QtGui,QtCore
from random import sample,random
from qtarotconfig import QTarotConfig
from utilities import ZPGraphicsView

class QTarotScene(QtGui.QGraphicsScene):
	def __init__(self,*args):
		QtGui.QGraphicsScene.__init__(self, *args)
		self.tableitem=self.addPixmap(QtGui.QPixmap())
		self.tableitem.setZValue(-1000.0)
	def calculateOffset(self):
		xoffset=(self.sceneRect().width()-self.smallerD)/2.0
		yoffset=(self.sceneRect().height()-self.smallerD)/2.0
		return QtCore.QPointF(xoffset,yoffset)
	def clear(self):
		px=self.tableitem.pixmap()
		QtGui.QGraphicsScene.clear(self)
		self.tableitem=self.addPixmap(px)
	@property
	def smallerD(self):
		return self.sceneRect().width() if \
		self.sceneRect().width() < self.sceneRect().height() else \
		self.sceneRect().height()
	def setTable(self, table):
		self.tableitem.setPixmap(table)
		if self.smallerD == 0:
			self.setSceneRect(QtCore.QRectF(0,0,500,500))
		else:
			self.setSceneRect(QtCore.QRectF(table.rect()))
	def table(self):
		return self.tableitem.pixmap()
	def addTarot(self, pixmap, number, pos,angle=0.0):
		qtarotitem=QTarotItem(pixmap)
		self.addItem(qtarotitem)
		if angle != 0:
			qtarotitem.rotate(angle)
		qtarotitem.setPos(pos)
		qtarotitem.cardNumber=number
		#graphicsItem->setTransform(QTransform().translate(centerX, centerY).rotate(angle).translate(-centerX, -centerY));
		return qtarotitem

	table = QtCore.pyqtProperty("QPixmap", table, setTable)

class QTarotItem(QtGui.QGraphicsPixmapItem):
	def cardNumber(self):
		return self.data(32).toInt()[0]

	def setCardNumber(self, idx):
		#self.setGraphicsEffect(QtGui.QGraphicsDropShadowEffect())
		self.setData(32,idx)

	def purpose(self):
		return self.data(33).toString()

	def setPurpose(self, string):
		self.setData(33, string)

	cardNumber = QtCore.pyqtProperty("int", cardNumber, setCardNumber)
	purpose = QtCore.pyqtProperty("QString", purpose, setPurpose)

class QTarot(QtGui.QMainWindow):

	def __init__(self):
		super(QTarot, self).__init__()
		self.initUI()

	def updateCards(self):
		j=0
		offset=self.scene.calculateOffset()
		for item in self.scene.items():
			if isinstance(item,QTarotItem):
				card=item.data(32).toInt()[0]
				item.setPixmap(qtrcfg.deck[card].scaledToWidth(self.scene.smallerD/self.currentLayout.largetDimension))
				i=self.currentLayout.elements[j]
				pos=QtCore.QPointF(i[0]*self.scene.smallerD,i[1]*self.scene.smallerD)
				item.setPos(pos+offset)
				j+=1
		self.scene.invalidate()

	def updateTable(self,fn="deck:table.png"):
		self.scene.table=QtGui.QPixmap(fn)
		j=0
		offset=self.scene.calculateOffset()
		for item in self.scene.items():
			if isinstance(item,QTarotItem):
				item.setPixmap(item.pixmap().\
				scaledToWidth(self.scene.smallerD/self.currentLayout.largetDimension))
				i=self.currentLayout.elements[j]
				pos=QtCore.QPointF(i[0]*self.scene.smallerD,i[1]*self.scene.smallerD)
				item.setPos(pos+offset)
				j+=1
		self.scene.invalidate()

	def pickTable(self):
		filename=QtGui.QFileDialog.getOpenFileName (self, caption="Open a new file", \
		directory=QtCore.QDir.homePath(), filter="Images (%s)" %(' '.join(formats)))
		if filename is not None and filename != "":
			self.updateTable(fn=filename)

	def saveReading(self):
		filename=QtGui.QFileDialog.getSaveFileName(self, caption="Save Current Reading",
			filter="Images (%s)" %(' '.join(formats)))
		if filename is not None and filename != "":
			fmt=filename.split(".",1)[-1]
			pixMap = QtGui.QPixmap(self.scene.sceneRect().width(),self.scene.sceneRect().height())
			painter=QtGui.QPainter(pixMap)
			here=QtCore.QRectF(self.scene.sceneRect().rect())
			self.scene.render(painter, here, here)
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
		draws=sample(xrange(len(qtrcfg.deck)),len(lay.elements))
		for (card,placement) in zip(draws, lay.elements):
			#rectitem=self.scene.addRect(0,0,1/lay.largetDimension*self.smallerD,\
			#2/lay.largetDimension*self.smallerD,\
			#pen=QtGui.QPen(QtGui.QColor("red"),2),\
			#brush=QtGui.QBrush(QtGui.QColor("indigo")))
			px=qtrcfg.deck[card].scaledToWidth(1/lay.largetDimension*self.scene.smallerD)
			if random() <= qtrcfg.negativity:
				rm=QtGui.QMatrix()
				rm.rotate(180)
				px=px.transformed(rm)
			pos=QtCore.QPointF(placement[0]*self.scene.smallerD,placement[1]*self.scene.smallerD)
			rectitem=self.scene.addTarot(px,card,pos+offset,angle=placement[2])
			rectitem.setToolTip(placement[3])

	def settingsWrite(self):
		self.settingsChange()
		qtrcfg.save_settings()
		self.settings_dialog.close()

	def settingsChange(self):
		qtrcfg.negativity=self.negativity.value()
		reload_deck=False
		if str(self.deck.currentText()) != qtrcfg.deck_name:
			qtrcfg.deck_name=str(self.deck.currentText())
			reload_deck=True
		qtrcfg.default_layout=str(self.default_layout.currentText())
		qtrcfg.load_layouts()
		qtrcfg.load_deck()
		if reload_deck:
			self.updateCards()

	def settingsReset(self):
		qtrcfg.reset_settings()
		self.updateSettingsWidgets()

	def updateSettingsWidgets(self):
		self.default_layout.addItems(qtrcfg.layouts.keys())
		idx=self.default_layout.findText(qtrcfg.default_layout)
		self.default_layout.setCurrentIndex(idx)
		self.negativity.setValue(qtrcfg.negativity)
		decks=list(QtCore.QDir("decks:/").entryList())
		decks.remove(".")
		decks.remove("..")
		self.deck.addItems(decks)
		idx=self.deck.findText(qtrcfg.deck_name)
		self.deck.setCurrentIndex(idx)

	def settings(self):
		self.settings_dialog=QtGui.QDialog(self)
		self.settings_dialog.setWindowTitle("Settings")

		label=QtGui.QLabel(("Note: These will not take effect"
		"until you make another reading"),self.settings_dialog)
		groupbox=QtGui.QGroupBox("Reading",self.settings_dialog)
		groupbox2=QtGui.QGroupBox("Appearance",self.settings_dialog)
		vbox=QtGui.QVBoxLayout(self.settings_dialog)
		gvbox=QtGui.QGridLayout(groupbox)
		gvbox2=QtGui.QGridLayout(groupbox2)

		self.negativity=QtGui.QDoubleSpinBox(groupbox)
		self.default_layout=QtGui.QComboBox(groupbox)
		self.negativity.setSingleStep(0.1)
		self.negativity.setRange(0,1)

		self.deck=QtGui.QComboBox(groupbox2)

		gvbox.addWidget(QtGui.QLabel("Negativity"),0,0)
		gvbox.addWidget(self.negativity,0,1)
		gvbox.addWidget(QtGui.QLabel("Default Layout"),1,0)
		gvbox.addWidget(self.default_layout,1,1)
		gvbox2.addWidget(QtGui.QLabel("Deck"),0,0)
		gvbox2.addWidget(self.deck,0,1)

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

		self.updateTable()

		self.view=ZPGraphicsView(self.scene,self)

		self.setCentralWidget(self.view)
		self.newReading(item=qtrcfg.default_layout)

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

		self.setGeometry(300, 300, 350, 250)
		self.setWindowTitle('Main window')
		self.show()


def main():
	global formats
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
	global app
	app = QtGui.QApplication(sys.argv)
	global qtrcfg
	qtrcfg = QTarotConfig()
	app.setApplicationName(qtrcfg.APPNAME)
	ex = QTarot()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()