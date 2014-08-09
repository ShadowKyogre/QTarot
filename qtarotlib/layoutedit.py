#!/usr/bin/python

from PyQt4 import QtCore, QtGui

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
	
	def _counterClockwise(self, b, c):
		#http://gamedev.stackexchange.com/questions/22133/how-to-detect-if-object-is-moving-in-clockwise-or-counterclockwise-direction
		a = self.boundingRect().center()
		return ((b.x() - a.x())*(c.y() - a.y()) - (b.y() - a.y())*(c.x() - a.x())) > 0
	
	def mouseDoubleClickEvent(self, event):
		purpose, ok = QtGui.QInputDialog.getText(None, "Testing Rect", "Type in a new purpose", text=self.toolTip())
		if ok:
			self.setToolTip(purpose)
		super().mouseDoubleClickEvent(event)
	
	def mouseMoveEvent(self, event):
		pos = self.mapToScene(event.pos())
		if self._counterClockwise(self._initialPos, pos):
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

def main():
	app = QtGui.QApplication([])
	canvas_view = QtGui.QGraphicsView()
	scene = QtGui.QGraphicsScene()
	canvas_view.setScene(scene)
	for i in range(3):
		item = InteractableRectItem(x=15,y=15,width=30,height=30, purpose="Neeep! {}".format(i))
		scene.addItem(item)
	canvas_view.show()
	exit(app.exec_())

if __name__ == "__main__":
	main()