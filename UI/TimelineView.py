from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import programVariables as pv

class TimelineSegment(QGraphicsRectItem):
    def __init__(self, x,y,w,h):
        super(TimelineSegment,self).__init__(x,y,w,h)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.segmentItem = None
        self.labelName =''
        self.labelColor = QColor(125,125,125)

    def updateLabel(self, name, color):
        self.labelName = name
        self.labelColor = color
        self.setBrush(color)
        if self.segmentItem != None:
            self.segmentItem.updateLabel(name,color,True)

class TimelineScene(QGraphicsScene):
    sendSelectionUpdate = pyqtSignal()
    def __init__(self, parent=None):
        super(TimelineScene, self).__init__(parent)
        self.parent = parent

    def contextMenuEvent(self, event):
        viewer = self.parent
        list = viewer.labels
        menu = QMenu()
        for key in list:
            aoiString = str(key)
            pixmap = QPixmap(50,50)
            pixmap.fill(list[key])      
            menu.addAction(QAction(QIcon(pixmap),aoiString,self)) 
        action = menu.exec_(event.screenPos())
        if action != None:
            self.labelItems(action.text())
    
    def labelItems(self,labelName):
        list = self.parent.labels
        selectedItems = self.selectedItems()
        for item in selectedItems:
            item.updateLabel(labelName,list[labelName])

    def mouseDoubleClickEvent(self, event):
        scene = None
        selection = self.selectedItems()
        for item in self.parent.segmentItems:
            if len(self.selectedItems()) == 0:
                item.setOpacity(1.0)
            elif item.isSelected():
                item.setOpacity(1.0)
            else: 
                item.setOpacity(pv.itemTransparency)
        self.sendSelectionUpdate.emit()

        if len(selection) == 1:
            self.parent.centerOn(selection[0])
            if selection[0].segmentItem != None:
                self.parent.parent().sliderTime.setValue(selection[0].segmentItem.frameNr)
            self.update()

class TimelineView(QGraphicsView):
    def __init__(self, parent):
        super(TimelineView, self).__init__(parent)
        self.zoom = 0
        self.scene = TimelineScene(self)
        self.slitscanLocal = QGraphicsPixmapItem()
        self.scene.addItem(self.slitscanLocal)
        self.slitscanGlobal = QGraphicsPixmapItem()
        self.slitscanGlobal.setPos(0,pv.cropSize*2+pv.plotHeight*2)
        self.scene.addItem(self.slitscanGlobal)
        self.similarityPlot = QGraphicsPixmapItem()
        self.scene.addItem(self.similarityPlot)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHint(QPainter.HighQualityAntialiasing,QPainter.SmoothPixmapTransform)
        self.segments = []
        self.segmentItems = []
        self.labels = {}
        
        self.slider=QGraphicsRectItem(0,-10,1,pv.cropSize*4+pv.plotHeight+20)
        self.slider.setBrush(QColor(255,255,200,255))
        self.slider.setPen(QPen(QColor(255,0,0,100),5))
        self.scene.addItem(self.slider)

        self.thresholdSlider = None
        self.timelineScale = QGraphicsPixmapItem()
        self.timelineScale.setPos(0,pv.cropSize*2+pv.plotHeight)
        self.scene.addItem(self.timelineScale)

        self.videoFrame = QGraphicsPixmapItem()
        self.scene.addItem(self.videoFrame)
        self.currentFrame = 0

    def drawSegments(self, segments):
        self.removeSegments()
        self.segments = segments
        for segment in self.segments:
            width = segment[1]-segment[0]+1
            rect = TimelineSegment(segment[0],2*pv.cropSize,width,pv.plotHeight)
            rect.setBrush(Qt.gray)
            rect.setPen(QPen(QColor(0,0,0,50),0))
            self.scene.addItem(rect)
            self.segmentItems.append(rect)
            self.scene.update()

    def removeSegments(self):
        for item in self.segmentItems:
            self.scene.removeItem(item)
        self.segmentItems.clear()

    def fitInView(self, scale=True):
        rect = QRectF(self.slitscanLocal.pixmap().rect())
        unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
        self.scale(1 / unity.width(), 1 / unity.height())
        viewrect = self.viewport().rect()
        scenerect = self.transform().mapRect(rect)
        factor = min(viewrect.width() / scenerect.width(), viewrect.height() / scenerect.height())
        self.scale(factor, factor)
        self.zoom = 0

    def setSlitscanLocal(self,pixmap):
        self.zoom = 0
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.slitscanLocal.setPixmap(pixmap)
        self.fitInView()
    def setSlitscanGlobal(self,pixmap):
        self.zoom = 0
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.slitscanGlobal.setPixmap(pixmap)
        self.fitInView()

    def wheelEvent(self, event):
            if event.angleDelta().y() > 0:
                factor = 1.25
                self.zoom += 1
            else:
                factor = 0.8
                self.zoom -= 1
            if self.zoom > 0:
                self.scale(factor, factor)
            elif self.zoom == 0:
                self.fitInView()
            else:
                self.zoom = 0
    
    def updateTime(self,val):
        self.slider.setPos(val,0)
        self.centerOn(self.slider)
        self.currentFrame = val

    def updateVideoframe(self,pixmap):
        self.videoFrame.setPixmap(pixmap)
        self.videoFrame.setScale(0.2)
        self.videoFrame.setPos(self.currentFrame+10,pv.cropSize*2+pv.plotHeight*2)

    def toggleComponents(self,localComp,globalComp,simComp):
        self.slitscanLocal.setVisible(localComp)
        self.slitscanGlobal.setVisible(globalComp)
        self.similarityPlot.setVisible(simComp)
        self.setSliderSize()
        self.update()

    def setSliderSize(self):
        height = pv.plotHeight*2
        startRect = self.slider.rect()
        if self.slitscanLocal.isVisible():
            height += pv.cropSize*2
            ypos = -10
        else:
            ypos = -10+pv.cropSize*2
        if self.slitscanGlobal.isVisible():
            height += pv.cropSize*2
        self.slider.setRect(startRect.x(),ypos,startRect.width(),height)
        self.thresholdSlider.setVisible(self.similarityPlot.isVisible())
