#!/usr/bin/python
from PyQt4 import QtCore, QtGui
from lxml import objectify, etree
from lxml.etree import DocumentInvalid

import os
#import argparse

from .utilities import ZPGraphicsView
from . import APPNAME,APPVERSION,AUTHOR,DESCRIPTION,YEAR,PAGE,EMAIL
from .xmlobjects import parser, layout_validator

def _counterClockwise(a, b, c):
	#http://gamedev.stackexchange.com/questions/22133/how-to-detect-if-object-is-moving-in-clockwise-or-counterclockwise-direction
	return ((b.x() - a.x())*(c.y() - a.y()) - (b.y() - a.y())*(c.x() - a.x())) > 0

class InteractableRectItem(QtGui.QGraphicsRectItem):
	class ItemEmitter(QtCore.QObject):
		tooltipChanged = QtCore.pyqtSignal(['QString'])
	def __init__(self, purpose=None, rect=None, x=None, y=None, width=None, height=None, parent=None):
		if isinstance(rect, QtCore.QRectF):
			super().__init__(rect, parent=parent)
		elif all((isinstance(x, int) or isinstance(x, float),
		         isinstance(y, int) or isinstance(y, float),
		         isinstance(width, int) or isinstance(width, float),
		         isinstance(height, int) or isinstance(height, float))):
				super().__init__(x, y, width, height, parent=parent)
		else:
			super().__init__(parent=parent)
		self.setTransformOriginPoint(self.boundingRect().center())
		self.setFlags(self.flags() | QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemSendsGeometryChanges)
		self._initialPos = None
		self.emitter = InteractableRectItem.ItemEmitter()
		if isinstance(purpose, str):
			self.setToolTip(purpose)
	
	def itemChange(self, change, value):
		#print(change, value)
		if change == QtGui.QGraphicsItem.ItemPositionChange and self.scene():
			#print(self.sceneBoundingRect(), self._rotation)
			half_width = self.sceneBoundingRect().width()/2
			half_height = self.sceneBoundingRect().height()/2
			if self.rotation() != 0:
				if self.x() < half_width/4:
					value.setX(half_width/4)
				elif self.x() > self.scene().width()-1.75*half_width:
					value.setX(self.scene().width()-1.75*half_width)

				if self.y() < half_height/4:
					value.setY(half_height/4)
				elif self.y() > self.scene().height()-1.75*half_height:
					value.setY(self.scene().height()-1.75*half_height)
			else:
				if self.x() < 0:
					value.setX(0)
				elif self.x() > self.scene().width()-2*half_width:
					value.setX(self.scene().width()-2*half_width)

				if self.y() < 0:
					value.setY(0)
				elif self.y() > self.scene().height()-2*half_height:
					value.setY(self.scene().height()-2*half_height)
			
			return value
		return super().itemChange(change, value)
	
	def mousePressEvent(self, event):
		self._initialPos = self.mapToScene(event.pos())
		super().mousePressEvent(event)
	
	def mouseDoubleClickEvent(self, event):
		if not event.modifiers()&QtCore.Qt.ShiftModifier:
			purpose, ok = QtGui.QInputDialog.getText(None, "Testing Rect", "Type in a new purpose", text=self.toolTip())
			if ok:
				self.setToolTip(purpose)
				self.emitter.tooltipChanged.emit(purpose)
		else:
			rotation, ok = QtGui.QInputDialog.getDouble(None, "Testing Rect", "Type a new rotation value", value=self.rotation(), min=0, max=360)
			if ok:
				self.setTransformOriginPoint(self.boundingRect().center())
				self.setRotation(rotation)
		super().mouseDoubleClickEvent(event)
	
	def mouseMoveEvent(self, event):
		pos = self.mapToScene(event.pos())
		#print(self.scenePos())
		#print(self.scenePos())
		#print("---")
		if event.modifiers()&QtCore.Qt.ShiftModifier:
			self.setPos(self.pos()+(pos-self._initialPos))
		else:
			tmprot = self.rotation()
			if _counterClockwise(self.boundingRect().center(), self._initialPos, pos):
				tmprot +=1
			else:
				tmprot -=1
			self.setRotation(tmprot)
		self._initialPos = pos
		super().mouseMoveEvent(event)

class MoveRotateScene(QtGui.QGraphicsScene):
	def __init__(self, grid_x=None, grid_y=None, rect=None, x=None, y=None, width=None, height=None, parent=None):
		if isinstance(rect, QtCore.QRectF):
			super().__init__(rect, parent=parent)
		elif all((isinstance(x, int) or isinstance(x, float),
		         isinstance(y, int) or isinstance(y, float),
		         isinstance(width, int) or isinstance(width, float),
		         isinstance(height, int) or isinstance(height, float))):
				#print("Initting here!")
				super().__init__(x, y, width, height, parent=parent)
		else:
			super().__init__(parent=parent)

		self._initialPos = None
		self._rotation = 0
		#self._grid_x = grid_x
		#self._grid_y = grid_y

	def drawBackground(self, painter, rect):
		#if None not in (self._grid_x, self._grid_y):
		recty = rect.intersect(self.sceneRect())
		left = int(recty.left()) - int(recty.left()) % 30
		top = int(recty.top()) - int(recty.top()) % 30
		lines=[]
		for x in range(left, int(recty.right())+1, 30):
			lines.append(QtCore.QLineF(x, recty.top(), x, recty.bottom()))
		for y in range(top, int(recty.bottom())+1, 30):
			lines.append(QtCore.QLineF(recty.left(), y, recty.right(), y))
		painter.drawLines(lines)

	def mousePressEvent(self, event):
		pitem = self.itemAt(event.scenePos())
		self._initialPos = event.scenePos()
		if pitem is None or len(self.selectedItems()) <= 1:
			super().mousePressEvent(event)
			return

		for item in self.selectedItems():
			item.mousePressEvent(event)
		#super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		pitem = self.itemAt(event.scenePos())
		pos = event.scenePos()
		if pitem is None or len(self.selectedItems()) <= 1:
			super().mouseMoveEvent(event)
			self._initialPos = pos
			self._rotation = 0
			return

		'''
		center = self.selectionArea().boundingRect().center()
		if _counterClockwise(center, self._initialPos, pos):
			self._rotation +=1
		else:
			self._rotation -=1
		'''

		for item in self.selectedItems():
			if event.modifiers()&QtCore.Qt.ShiftModifier:
				item.setPos(item.pos()+(pos-self._initialPos))
			else:
				pass
		self._initialPos = pos
		#super().mouseMoveEvent(event)

class QTarotLayoutEdit(QtGui.QMainWindow):

	def __init__(self):
		super().__init__()
		self.initUI()

	def about(self):
		QtGui.QMessageBox.about (self, "About {}".format(APPNAME),
		("<center><big><b>{0} Layout Editor {1}</b></big>"
		"<br />{2}<br />(C) <a href=\"mailto:{3}\">{4}</a> {5}<br />"
		"<a href=\"{6}\">{0} Homepage</a></center>")\
		.format(APPNAME,APPVERSION,DESCRIPTION,EMAIL,AUTHOR,YEAR,PAGE))

	def newCard(self, checked=False, x=15, y=15, width=None, height=None, angle=None, purpose="Neeep! {}"):
		item = InteractableRectItem(x=0, y=0, width=30, height=30, purpose=purpose)
		item.setPos(x, y)
		col = self.palette().highlight().color()
		col.setAlphaF(0.6)
		brush = QtGui.QBrush(col)
		pen = QtGui.QPen(self.palette().highlightedText().color())
		pen.setWidth(0)
		item.setBrush(brush)
		item.setPen(pen)
		if angle is not None:
			item.setRotation(angle)
		
		self.view.scene().addItem(item)
		litem = QtGui.QListWidgetItem(item.toolTip(), self.listview)
		litem.setData(QtCore.Qt.UserRole, item)
		litem.setFlags(litem.flags() | QtCore.Qt.ItemIsEditable)
		item.emitter.tooltipChanged.connect(litem.setText)

	def delCard(self):
		for item in self.listview.selectedItems():
			canvas_item = item.data(QtCore.Qt.UserRole)
			self.view.scene().removeItem(canvas_item)
			self.listview.takeItem(self.listview.row(item))
	
	def updateListView(self):
		for i in range(self.listview.count()):
			item = self.listview.item(i)
			canvas_item = item.data(QtCore.Qt.UserRole)
			if canvas_item.isSelected():
				item.setSelected(True)
			else:
				item.setSelected(False)
	
	def updateView(self):
		sel = self.listview.selectedItems()
		for i in range(self.listview.count()):
			item = self.listview.item(i)
			if item in sel:
				item.data(QtCore.Qt.UserRole).setSelected(True)
			else:
				item.data(QtCore.Qt.UserRole).setSelected(False)

	def syncView(self, item):
		canvas_item = item.data(QtCore.Qt.UserRole)
		canvas_item.setToolTip(item.text())
	
	def updateGrid(self):
		self.view.scene().setSceneRect(0, 0, self.widthBox.value()*30, self.heightBox.value()*30)

	def allSel(self, selected=False):
		for i in range(self.listview.count()):
			item = self.listview.item(i)
			item.setSelected(selected)

	def initUI(self):
		self.setWindowTitle(app.applicationName())
		self.view = ZPGraphicsView()
		self.setCentralWidget(self.view)
		scene = MoveRotateScene(x=0, y=0, width=90, height=90)
		self.widthBox = QtGui.QSpinBox()
		self.widthBox.setValue(3)
		self.heightBox = QtGui.QSpinBox()
		self.heightBox.setValue(3)
		self.view.setScene(scene)

		self.widthBox.valueChanged.connect(self.updateGrid)
		self.heightBox.valueChanged.connect(self.updateGrid)

		dockwidget = QtGui.QDockWidget("Layout Editor", parent=self)
		holder = QtGui.QWidget()
		layout = QtGui.QFormLayout(holder)
		self.nameEdit = QtGui.QLineEdit()
		self.authorEdit = QtGui.QLineEdit()
		self.sourceEdit = QtGui.QLineEdit()
		self.purposeEdit = QtGui.QLineEdit()
		self.listview = QtGui.QListWidget()
		self.listview.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
		self.listview.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)

		self.listview.itemSelectionChanged.connect(self.updateView)
		self.listview.itemChanged.connect(self.syncView)
		
		layout.addRow("Name", self.nameEdit)
		layout.addRow("Width", self.widthBox)
		layout.addRow("Height", self.heightBox)
		layout.addRow("Purpose", self.purposeEdit)
		layout.addRow("Author", self.authorEdit)
		layout.addRow("Source", self.sourceEdit)
		layout.addRow(self.listview)

		dockwidget.setWidget(holder)
		dockwidget.show()
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockwidget)

		scene.selectionChanged.connect(self.updateListView)

		newLayAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-new'), 'New Card', self)
		newLayAction.setShortcut('N')
		newLayAction.setStatusTip('Add a new card position to the layout')
		newLayAction.triggered.connect(self.newCard)

		openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'), 'Open Layout', self)
		openAction.setShortcut('Ctrl+O')
		openAction.setStatusTip('Open another file')
		openAction.triggered.connect(self.openFile)

		saveAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-save'), 'Save', self)
		saveAction.setShortcut('Ctrl+S')
		saveAction.setStatusTip('Save')
		saveAction.triggered.connect(self.saveFile)

		delAction = QtGui.QAction(QtGui.QIcon.fromTheme('edit-delete'), 'Delete Card', self)
		delAction.setShortcut('Delete')
		delAction.setStatusTip('Delete selected card positions')
		delAction.triggered.connect(self.delCard)
		
		unselectAllAction = QtGui.QAction(QtGui.QIcon.fromTheme('durp'), 'Unselect all card positions', self)
		unselectAllAction.setShortcut('Ctrl+Shift+A')
		unselectAllAction.setStatusTip('Unselect all card positions')
		unselectAllAction.triggered.connect(lambda: self.allSel(False))

		selectAllAction = QtGui.QAction(QtGui.QIcon.fromTheme('durp'), 'Select all card positions', self)
		selectAllAction.setShortcut('Ctrl+A')
		selectAllAction.setStatusTip('Select all card positions')
		selectAllAction.triggered.connect(lambda: self.allSel(True))

		aboutAction=QtGui.QAction(QtGui.QIcon.fromTheme('help-about'), 'About', self)
		aboutAction.triggered.connect(self.about)

		toolbar = self.addToolBar('Exit')
		toolbar.addAction(newLayAction)
		toolbar.addAction(openAction)
		toolbar.addAction(saveAction)
		toolbar.addAction(selectAllAction)
		toolbar.addAction(unselectAllAction)
		toolbar.addAction(delAction)
		toolbar.addAction(aboutAction)

	def openFile(self, checked=False, filename=None):
		if filename is None:
			filename = QtGui.QFileDialog.getOpenFileName (self, 
						caption="Open a layout file", 
						directory=QtCore.QDir.homePath(), 
						filter="*.xml")
		if filename != "":
			print("Opening file...")
			try:
				lay = objectify.parse(filename, parser=parser).getroot()
				layout_validator.assertValid(lay)
				self.nameEdit.setText(lay.attrib['name'])
				self.heightBox.setValue(float(lay.attrib['height']))
				self.widthBox.setValue(float(lay.attrib['width']))
				self.purposeEdit.setText(lay.purpose.text)
				self.authorEdit.setText(lay.author.text)
				self.sourceEdit.setText(lay.source.text)
				for i in lay.iterchildren(tag='pos'):
					self.newCard(x=i.x*self.view.scene().width(), y=i.y*self.view.scene().height(), angle=i.angle, purpose=i.purpose.text)
			except DocumentInvalid as e:
				print(filename, "was an invalid layout xml file, starting empty.")
			except OSError as e:
				print(filename, "doesn't exist, starting empty.")

	def saveFile(self, checked=False, filename=None):
		xmlobj = etree.fromstring('<layout></layout>')
		xmlobj.attrib['name']=self.nameEdit.text()
		xmlobj.attrib['height']=str(self.heightBox.value())
		xmlobj.attrib['width']=str(self.widthBox.value())
		etree.SubElement(xmlobj, 'purpose').text = self.purposeEdit.text()
		etree.SubElement(xmlobj, 'author').text = self.authorEdit.text()
		etree.SubElement(xmlobj, 'source').text = self.sourceEdit.text()
		for i in range(self.listview.count()):
			item = self.listview.item(i)
			canvas_item = item.data(QtCore.Qt.UserRole)
			true_pos = canvas_item.pos()
			pos = etree.SubElement(xmlobj, 'pos')
			purpose = etree.SubElement(pos, 'purpose')
			x = etree.SubElement(pos, 'x')
			y = etree.SubElement(pos, 'y')
			angle = etree.SubElement(pos, 'angle')
			purpose.text = canvas_item.toolTip()
			x.text = str(true_pos.x()/canvas_item.scene().width())
			y.text = str(true_pos.y()/canvas_item.scene().height())
			angle.text = str(canvas_item.rotation())
		tree_string = etree.tostring(xmlobj, pretty_print=True).decode('utf-8')
		if not filename:
			filename = QtGui.QFileDialog.getSaveFileName(self, caption="Save Layout", 
			                                             filter="*.xml" )
		if filename:
			with open(filename, 'w', encoding='utf-8') as f:
				f.write(tree_string)

def main():
	global app

	app = QtGui.QApplication(os.sys.argv)
	app.setApplicationName(APPNAME)
	app.setApplicationVersion(APPVERSION)
	app.setWindowIcon(QtGui.QIcon.fromTheme("qtarot"))

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

	editor = QTarotLayoutEdit()
	editor.show()
	
	if len(os.sys.argv) == 2:
		editor.openFile(filename=os.sys.argv[1])
	exit(app.exec_())

if __name__ == "__main__":
	main()
