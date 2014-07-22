#!/usr/bin/python

import os
import argparse
from PyQt4 import QtGui,QtCore
from urllib.parse import urlparse
from random import sample,random
from pyqt_lxml_utils import LXMLModel

from .guiconfig import QTarotConfig
from .utilities import QDeckEdit
from .xmlobjects import objectify, parser
from . import APPNAME,APPVERSION,AUTHOR,DESCRIPTION,YEAR,PAGE,EMAIL

#http://www.sacred-texts.com/tarot/faq.htm#US1909

class QTarotDeckEdit(QtGui.QMainWindow):

	def __init__(self):
		super().__init__()
		self.initUI()

	def saveReadingAsIMG(self,filename,fmt):
		pixMap = QtGui.QPixmap(self.scene.sceneRect().width(),self.scene.sceneRect().height())

		c = QtGui.QColor(0)
		c.setAlpha(0)
		pixMap.fill(c)

		painter=QtGui.QPainter(pixMap)
		self.scene.render(painter)
		painter.end()
		pixMap.save(filename,format=fmt)

	def saveReadingAsHTML(self,filename):
		store_here="{}.files".format(filename.replace(".html",""))
		if not os.path.exists(store_here):
			os.makedirs(store_here)
		reading_px=os.path.join(store_here,"reading.png")
		reading_pxh=os.path.join(os.path.basename(store_here),"reading.png")
		self.saveReadingAsIMG(reading_px,'png')

		f=open(filename,'w')
		import shutil
		htmltpl=QtCore.QDir("htmltpl:/").absoluteFilePath('export_read.html')
		f2=open(htmltpl)
		template=f2.read()
		f2.close()

		cards=""
		layout="&lt;Unknown&gt;"
		deck_def_credits=""
		layout_credits=""
		deck=""
		for item in list(self.scene.items()):
			if isinstance(item,QTarotItem):
				if layout == "&lt;Unknown&gt;":
					layout=item.posData.getparent().get('name')
					layout_credits=self.generateCredits(item.posData)
				if not deck_def_credits:
					deck_def_credits=self.generateCredits(item.card)
					deck=item.card.getroottree().getroot().get('name')
				text,copy_from,save_file=self.generateCardText(item.card,\
				item.rev,item.posData.purpose.text,newfp=store_here)
				shutil.copy(copy_from,save_file)
				cards=''.join([cards,text])

		f.write(template.format(cards=cards,deck=deck,
		layout=layout,reading_px=reading_pxh,layout_credits=layout_credits,\
		deck_def_credits=deck_def_credits))
		f.close()

	def saveReading(self,filename=None):
		if not filename:
			filename=str(QtGui.QFileDialog.getSaveFileName(self, caption="Save Current Reading",
				filter="Images (%s);;HTML (*.html)" %(' '.join(formats))))
		if filename:
			fmt=filename.split(".",1)[-1]
			if fmt == 'html':
				self.saveReadingAsHTML(filename)
			elif "*.{}".format(fmt) in formats:
				self.saveReadingAsIMG(filename,fmt)
			else:
				QtGui.QMessageBox.critical(self, "Save Current Reading", \
				"Invalid format ({}) specified for {}!".format(fmt,filename))

	def about(self):
		QtGui.QMessageBox.about (self, "About {}".format(APPNAME),
		("<center><big><b>{0} Deck Editor {1}</b></big>"
		"<br />{2}<br />(C) <a href=\"mailto:{3}\">{4}</a> {5}<br />"
		"<a href=\"{6}\">{0} Homepage</a></center>")\
		.format(APPNAME,APPVERSION,DESCRIPTION,EMAIL,AUTHOR,YEAR,PAGE))

	def initUI(self):
		self.setWindowTitle(app.applicationName())
		#self.view = QDeckEdit(self)
		self.view = QtGui.QTreeView(self)
		blub=objectify.fromstring("""
		<deck>
			<author>me</author>
			<source>yeep</source>
			<suit name='them' affinity='durp'>
				<card name='you'>
					<file>selfie.png</file>
					<meaning>
						<normal>normal self</normal>
						<reversed>a&lt;i&gt;e&lt;/i&gt;a</reversed>
					</meaning>
					<source>yeep/you</source>
				</card>
			</suit>
		</deck>
		""",parser=parser)
		model = LXMLModel(blub)
		self.view.setModel(model)

		self.setCentralWidget(self.view)
		self.setDockNestingEnabled(True)

		exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(self.close)

		newLayAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-new'), 'Create a new deck definition', self)
		newLayAction.setShortcut('Ctrl+N')
		newLayAction.setStatusTip('Create a new deck definition')
		#newLayAction.triggered.connect(self.newReading)

		saveAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-save'), 'Save', self)
		saveAction.setShortcut('Ctrl+S')
		saveAction.setStatusTip('Save')
		#saveAction.triggered.connect(self.saveReading)

		openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'), 'Edit another deck definition', self)
		openAction.setShortcut('Ctrl+O')
		openAction.setStatusTip('Edit another deck definition')
		#openAction.triggered.connect(self.pickTable)
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
		fileMenu.addAction(newLayAction)
		#fileMenu.addAction(newChooseAction)
		fileMenu.addAction(openAction)
		fileMenu.addAction(saveAction)
		#fileMenu.addAction(settingsAction)

		toolbar = self.addToolBar('Exit')
		toolbar.addAction(exitAction)
		toolbar.addAction(newLayAction)
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

	#qtrcfg = QTarotConfig()
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
