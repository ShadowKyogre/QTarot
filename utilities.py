from PyQt4 import QtGui,QtCore

class ZPGraphicsView(QtGui.QGraphicsView):
	def __init__(self, *args):
		QtGui.QGraphicsView.__init__(self, *args)
		self.lastPanPoint=QtCore.QPoint()
		self.setCenter(QtCore.QPointF(self.sceneRect().width()/2.0, \
		self.sceneRect().height()/2.0))

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
		self.lastPanPoint = event.pos()
		self.setCursor(QtCore.Qt.ClosedHandCursor)

	def mouseReleaseEvent(self,event):
		self.setCursor(QtCore.Qt.OpenHandCursor)
		self.lastPanPoint = QtCore.QPoint()

	def mouseMoveEvent(self, event):
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