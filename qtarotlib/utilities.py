from PyQt4 import QtGui,QtCore
from lxml import objectify
from .xmlobjects import TarotCard

class QDeckBrowser(QtGui.QWidget):
	def __init__(self, parent = None, deck_source = None):
		QtGui.QWidget.__init__(self, parent)
		layout = QtGui.QGridLayout(self)
		self.deckPicker=QtGui.QComboBox(self)
		self.skinPicker=QtGui.QComboBox(self)
		self.deckPicker.currentIndexChanged['QString'].connect(self.populateSkins)
		self.skinPicker.currentIndexChanged['QString'].connect(self.populatePreview)

		self.previewArea=QtGui.QListView(self)
		self.previewArea.setGridSize(QtCore.QSize(128,128))
		self.previewArea.setViewMode (QtGui.QListView.IconMode)
		self.previewArea.setResizeMode (QtGui.QListView.Adjust)
		self.previewArea.setWrapping(True)

		m=QtGui.QStandardItemModel(self.previewArea)
		m.setColumnCount(1)

		self.previewArea.setModel(m)
		self.previewArea.setModelColumn(1)
		self.previewArea.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.previewArea.setUniformItemSizes (True)

		layout.addWidget(QtGui.QLabel("Deck"),0,0)
		layout.addWidget(QtGui.QLabel("Skin"),0,1)
		layout.addWidget(self.deckPicker,1,0)
		layout.addWidget(self.skinPicker,1,1)
		layout.addWidget(self.previewArea,2,0,1,2)

		self.deckSource=deck_source

	def populateSkins(self, new_def):
		if new_def in self.deckSource:
			skins_list=self.deckSource[new_def]['skins']
		else:
			skins_list=[]
		self.skinPicker.clear()
		self.skinPicker.addItems(skins_list)
		self.skinPicker.setCurrentIndex(0)

	def setDeckSource(self, new_source):
		self._deckSource=new_source
		self.deckPicker.addItems(list(self._deckSource.keys()))
		self.deckPicker.setCurrentIndex(0)

	def deckSource(self):
		return self._deckSource

	def currentDeck(self):
		return self.deckSource[self.deckPicker.currentText()]

	def populatePreview(self, new_skin):
		self.previewArea.model().removeRows(0,self.previewArea.model().rowCount())
		if not new_skin:
			return
		model=self.previewArea.model()
		for card in self.currentDeck()['definition'].cards():
			f=QtCore.QFileInfo(card.file.text)
			bf=f.baseName()
			sf=f.completeSuffix()
			fn="{bf}.{sf}".format(**locals())
			item=QtGui.QStandardItem(QtGui.QIcon("skins:/{new_skin}/{fn}".format(**locals())), \
			card.fullname())
			item.setData(card.getroottree().getpath(card),32)
			item.setData(new_skin,33)
			model.appendRow(item)

	deckSource = QtCore.pyqtProperty(dict, deckSource, setDeckSource)

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

	def addTarot(self, card, pos_data, rev=False):
		qtarotitem=QTarotItem(card, pos_data, rev)
		#qtarotitem.rev=rev
		self.addItem(qtarotitem)
		qtarotitem.refresh()
		qtarotitem.reposition()
		return qtarotitem

	table = QtCore.pyqtProperty("QPixmap", table, setTable)

class QTarotItem(QtGui.QGraphicsPixmapItem):

	class QTarotItemEmitter(QtCore.QObject):
		showAllInfo=QtCore.pyqtSignal([TarotCard,'bool',objectify.ObjectifiedElement])
		showName=QtCore.pyqtSignal(['QString'])
		clearName=QtCore.pyqtSignal([])

	def __init__(self, card, pos_data, reverse, parent=None, scene=None):
		QtGui.QGraphicsPixmapItem.__init__(self, parent=None, scene=None)
		#QtGui.QGraphicsObject.__init__(self, parent)
		self.setAcceptHoverEvents(True)
		self.card=card
		self.posData=pos_data
		self.rev=reverse

		self.emitter = QTarotItem.QTarotItemEmitter()

	def itemChange (self, change, value):
		if change == QtGui.QGraphicsItem.ItemSceneChange:
			self.refresh()
		return QtGui.QGraphicsPixmapItem.itemChange(self, change, value)

	def refresh(self):
		if None in (self.posData, self.card, self.scene()):
			return
		fn=self.card.file.text
		#or skin:fn
		px=QtGui.QPixmap("skin:{fn}".format(**locals()))
		largestDim=self.posData.getparent().largetDimension()
		shortest_dim_size=1/largestDim*self.scene().smallerD

		if px.width() < px.height():
			px=px.scaledToWidth(shortest_dim_size)
		else:
			px=px.scaledToHeight(shortest_dim_size)

		if self.rev:
			rm=QtGui.QMatrix()
			rm.rotate(180)
			px=px.transformed(rm)

		self.setPixmap(px)

	def reposition(self):
		largestDim=self.posData.getparent().largetDimension()
		shortest_dim_size=1/largestDim*self.scene().smallerD
		offset=self.scene().calculateOffset()
		pos=QtCore.QPointF(self.posData.x*self.scene().smallerD, \
				self.posData.y*self.scene().smallerD)
		#print self.posData.angle
		#print
		if self.posData.angle != 0 and self.rotation() != self.posData.angle:
			#self.rotate(self.posData.angle)
			self.setRotation(self.posData.angle)
		self.setPos(pos+offset)

	def setRev(self, rev):
		self.setData(34,rev)
		self.refresh()
	def setCard(self, card):
		self.setData(32, card)
		self.refresh()
	def setPosData(self, pos_data):
		self.setData(35, pos_data)
		self.setToolTip(self.posData.purpose.text)
		self.refresh()

	def card(self):
		return self.data(32)
	def rev(self):
		return self.data(34)
	def posData(self):
		return self.data(35)

	card = QtCore.pyqtProperty(TarotCard, card, setCard)
	posData = QtCore.pyqtProperty(objectify.ObjectifiedElement, posData, setPosData)
	rev = QtCore.pyqtProperty("bool", rev, setRev)

	def hoverEnterEvent(self, event):
		QtGui.QGraphicsPixmapItem.hoverEnterEvent(self,event)
		self.emitter.showName.emit(self.card.fullname())

	def hoverLeaveEvent(self, event):
		QtGui.QGraphicsPixmapItem.hoverLeaveEvent(self,event)
		self.emitter.clearName.emit()

	#http://python.6.n6.nabble.com/GraphicsItem-QObject-Inheritance-problem-td1923392.html
	#http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/new_style_signals_slots.html
	#http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/old_style_signals_slots.html
	def mouseDoubleClickEvent(self, event):
		QtGui.QGraphicsPixmapItem.mouseDoubleClickEvent(self,event)
		self.emitter.showAllInfo.emit(self.card, self.rev, self.posData)

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
			cursize=self.mapFromScene (self.sceneRect()).boundingRect()
			if cursize.width() > self.width() and \
			cursize.height() > self.height():
				self.scale(1/abs(scaleFactor), 1/abs(scaleFactor))
			else:
				self.fitInView (self.sceneRect(),mode=QtCore.Qt.KeepAspectRatio)

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
