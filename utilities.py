from PyQt4 import QtGui,QtCore

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
	def addTarot(self, pixmap, number, pos ,angle=0.0, rev=False):
		qtarotitem=QTarotItem(pixmap)
		self.addItem(qtarotitem)
		if angle != 0:
			qtarotitem.rotate(angle)
		qtarotitem.setPos(pos)
		qtarotitem.cardNumber=number
		qtarotitem.rev=rev
		#graphicsItem->setTransform(QTransform().translate(centerX, centerY).rotate(angle).translate(-centerX, -centerY));
		return qtarotitem

	table = QtCore.pyqtProperty("QPixmap", table, setTable)

class QTarotItem(QtGui.QGraphicsPixmapItem):
	def __init__(self, *args):
		QtGui.QGraphicsPixmapItem.__init__(self, *args)
		self.setAcceptHoverEvents(True)
	def hoverEnterEvent(self, event):
		QtGui.QGraphicsPixmapItem.hoverEnterEvent(self,event)
		window = self.scene().parent()
		if window:
			window.statusBar().showMessage(str(self.cardNumber))
	def hoverLeaveEvent(self, event):
		QtGui.QGraphicsPixmapItem.hoverLeaveEvent(self,event)
		window = self.scene().parent()
		if window:
			window.statusBar().clearMessage()
	def cardNumber(self):
		return self.data(32).toInt()[0]
	def setCardNumber(self, idx):
		#self.setGraphicsEffect(QtGui.QGraphicsDropShadowEffect())
		self.setData(32,idx)
	def setRev(self, rev):
		self.setData(34,rev)
	def rev(self):
		return self.data(34).toBool()
	def purpose(self):
		return self.data(33).toString()
	def setPurpose(self, string):
		self.setData(33, string)

	cardNumber = QtCore.pyqtProperty("int", cardNumber, setCardNumber)
	rev = QtCore.pyqtProperty("bool", rev, setRev)
	purpose = QtCore.pyqtProperty("QString", purpose, setPurpose)

class ZPGraphicsView(QtGui.QGraphicsView):
	def __init__(self, *args):
		QtGui.QGraphicsView.__init__(self, *args)
		self.lastPanPoint=QtCore.QPoint()
		self.setCenter(QtCore.QPointF(self.sceneRect().width()/2.0, \
		self.sceneRect().height()/2.0))
		self.setMouseTracking(True)
		self.viewport().setMouseTracking(True)

	def setCenter(self, centerPoint):
		#Get the rectangle of the visible area in scene coords
		visibleArea = self.mapToScene(self.rect()).boundingRect()

		#Get the scene area
		sceneBounds = self.sceneRect()

		boundX = visibleArea.width() / 2.0;
		boundY = visibleArea.height() / 2.0;
		boundWidth = sceneBounds.width() - 2.0 * boundX
		boundHeight = sceneBounds.height() - 2.0 * boundY

		#The max boundary that the centerPoint can be to
		bounds=QtCore.QRectF(boundX, boundY, boundWidth, boundHeight)

		if bounds.contains(centerPoint):
			#We are within the bounds
			self.currentCenterPoint = centerPoint
		else:
			#We need to clamp or use the center of the screen
			if visibleArea.contains(sceneBounds):
				#Use the center of scene ie. we can see the whole scene
				self.currentCenterPoint = sceneBounds.center()
			else:
				self.currentCenterPoint = centerPoint

				#We need to clamp the center. The centerPoint is too large
				if centerPoint.x() > bounds.x() + bounds.width():
					self.currentCenterPoint.setX(bounds.x() + bounds.width())
				elif centerPoint.x() < bounds.x():
					self.currentCenterPoint.setX(bounds.x())

				if centerPoint.y() > bounds.y() + bounds.height():
					self.currentCenterPoint.setY(bounds.y() + bounds.height())
				elif centerPoint.y() < bounds.y():
					self.currentCenterPoint.setY(bounds.y())
		#Update the scrollbars
		self.centerOn(self.currentCenterPoint)


	def mousePressEvent(self, event):
		#For panning the view
		QtGui.QGraphicsView.mousePressEvent(self,event)
		self.lastPanPoint = event.pos()
		self.setCursor(QtCore.Qt.ClosedHandCursor)

	def mouseReleaseEvent(self,event):
		QtGui.QGraphicsView.mouseReleaseEvent(self,event)
		self.setCursor(QtCore.Qt.OpenHandCursor)
		self.lastPanPoint = QtCore.QPoint()

	def mouseMoveEvent(self, event):
		QtGui.QGraphicsView.mouseMoveEvent(self,event)
		if not self.lastPanPoint.isNull():
			#Get how much we panned
			delta = self.mapToScene(self.lastPanPoint) - self.mapToScene(event.pos())
			self.lastPanPoint = event.pos()

			#Update the center ie. do the pan
			self.setCenter(self.currentCenterPoint + delta)

	def wheelEvent(self,event):
		#Get the position of the mouse before scaling, in scene coords
		pointBeforeScale=QtCore.QPointF(self.mapToScene(event.pos()))

		#Get the original screen centerpoint
		screenCenter = self.currentCenterPoint # //currentCenterPoint; //(visRect.center());

		#Scale the view ie. do the zoom
		numDegrees = event.delta() / 8
		numSteps = numDegrees / 15
		scaleFactor = 1.15*numSteps #How fast we zoom

		if(event.delta() > 0):
			self.scale(scaleFactor, scaleFactor)
		else:
			#Zooming out
			about_to_be=self.matrix().scale(numSteps / scaleFactor,numSteps / scaleFactor)
			about_to_be_size=about_to_be.mapRect(self.sceneRect()).size()
			if about_to_be_size.width() >= self.sceneRect().width() and \
			about_to_be_size.height() >= self.sceneRect().height():
				self.setMatrix(about_to_be)

		#Get the position after scaling, in scene coords
		pointAfterScale=QtCore.QPointF(self.mapToScene(event.pos()))

		#Get the offset of how the screen moved
		offset = pointBeforeScale - pointAfterScale

		#Adjust to the new center for correct zooming
		newCenter = screenCenter + offset
		self.setCenter(newCenter)

	def resizeEvent(self,event):
		#Get the rectangle of the visible area in scene coords
		visibleArea = self.mapToScene(self.rect()).boundingRect()
		self.setCenter(visibleArea.center())
		QtGui.QGraphicsView.resizeEvent(self,event)