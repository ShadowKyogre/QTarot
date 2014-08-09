#!/usr/bin/python

from PyQt4 import QtCore, QtGui
from . import APPNAME,APPVERSION,AUTHOR,DESCRIPTION,YEAR,PAGE,EMAIL

def _counterClockwise(a, b, c):
	#http://gamedev.stackexchange.com/questions/22133/how-to-detect-if-object-is-moving-in-clockwise-or-counterclockwise-direction
	return ((b.x() - a.x())*(c.y() - a.y()) - (b.y() - a.y())*(c.x() - a.x())) > 0

class InteractableRectItem(QtGui.QGraphicsRectItem):
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
		
		self.setFlags(self.flags() | QtGui.QGraphicsItem.ItemIsSelectable)
		self._initialPos = None
		self._rotation = 0
		if isinstance(purpose, str):
			self.setToolTip(purpose)
	
	def mousePressEvent(self, event):
		self._initialPos = self.mapToScene(event.pos())
		super().mousePressEvent(event)
	
	def mouseDoubleClickEvent(self, event):
		purpose, ok = QtGui.QInputDialog.getText(None, "Testing Rect", "Type in a new purpose", text=self.toolTip())
		if ok:
			self.setToolTip(purpose)
		super().mouseDoubleClickEvent(event)
	
	def mouseMoveEvent(self, event):
		pos = self.mapToScene(event.pos())
		if _counterClockwise(self.boundingRect().center(), self._initialPos, pos):
			self._rotation +=1
		else:
			self._rotation -=1
		self.setTransformOriginPoint(self.boundingRect().center())
		if event.modifiers()&QtCore.Qt.ShiftModifier:
			self.setPos(self.pos()+(pos-self._initialPos))
		else:
			self.setRotation(self._rotation)
		self._initialPos = pos
		super().mouseMoveEvent(event)

class MoveRotateScene(QtGui.QGraphicsScene):
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

		self._initialPos = None
		self._rotation = 0

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

	def newCard(self):
		item = InteractableRectItem(x=15,y=15,width=30,height=30, purpose="Neeep! {}")
		self.view.scene().addItem(item)
		litem = QtGui.QListWidgetItem(item.toolTip(), self.listview)
		litem.setData(QtCore.Qt.UserRole, item)
	
	def updateSelection(self):
		sel = self.listview.selectedItems()
		print(sel)
		for i in range(self.listview.count()):
			item = self.listview.item(i)
			if item in sel:
				item.data(QtCore.Qt.UserRole).setSelected(True)
			else:
				item.data(QtCore.Qt.UserRole).setSelected(False)

	def initUI(self):
		self.setWindowTitle(app.applicationName())
		self.view = QtGui.QGraphicsView()
		self.setCentralWidget(self.view)
		scene = MoveRotateScene()
		#scene.changed.connect(self.updateListView)
		self.view.setScene(scene)

		newLayAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-new'), 'New Card', self)
		newLayAction.setShortcut('N')
		newLayAction.setStatusTip('Add a new card position to the layout')
		newLayAction.triggered.connect(self.newCard)
		
		aboutAction=QtGui.QAction(QtGui.QIcon.fromTheme('help-about'), 'About', self)
		aboutAction.triggered.connect(self.about)
		
		dockwidget = QtGui.QDockWidget(self)
		self.listview = QtGui.QListWidget()
		self.listview.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
		self.listview.itemSelectionChanged.connect(self.updateSelection)
		dockwidget.setWidget(self.listview)
		dockwidget.show()
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockwidget)
		
		toolbar = self.addToolBar('Exit')
		toolbar.addAction(newLayAction)
		toolbar.addAction(aboutAction)

def main():
	global app
	app = QtGui.QApplication([])
	editor = QTarotLayoutEdit()
	editor.show()
	exit(app.exec_())

if __name__ == "__main__":
	main()