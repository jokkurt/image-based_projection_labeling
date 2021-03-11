from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import programVariables as pv
import math

class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(QGraphicsScene, self).__init__(parent)
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

    def centerView(self,item):
        self.setSceneRect(item.boundingRect())
        self.update()

    def mouseDoubleClickEvent(self, event):
        opacity =1.0
        if len(self.selectedItems()) > 0:
            opacity = pv.itemTransparency
        for item in self.parent.segmentItems:
            if item.isSelected():
                item.setOpacity(1.0)
                item.timeLineSegment.setOpacity(1.0)
                item.timeLineSegment.scene().parent.centerOn(item.timeLineSegment)
                item.timeLineSegment.scene().parent.parent().sliderTime.setValue(item.frameNr)
            else:
                item.setOpacity(opacity)
                item.timeLineSegment.setOpacity(opacity)

    @pyqtSlot()
    def updateSelection(self, selectedItems):
        opacity =1.0
        if len(selectedItems) > 0:
            opacity = pv.itemTransparency
        for item in self.items():
            item.setOpacity(opacity)
        for item in selectedItems:
            if item.segmentItem != None:
                item.segmentItem.setOpacity(1.0)

    @pyqtSlot()
    def receiveSelectionUpdate(self):
        sendScene = self.sender()
        noneSelected = (len(sendScene.selectedItems()) == 0)
        for item in self.parent.segmentItems:
            if noneSelected:
                item.setOpacity(1.0)
                item.timeLineSegment.setOpacity(1.0)
            else:
                if item.timeLineSegment.scene() == sendScene:
                    item.setOpacity(item.timeLineSegment.opacity())
                    if (item.timeLineSegment.isSelected()):             
                        self.parent.centerOn(item)
                        self.update()
                else:
                    item.setOpacity(pv.itemTransparency)
                    item.timeLineSegment.setOpacity(pv.itemTransparency)
    
    @pyqtSlot(bool)
    def toogleShowLabeled(self,showLabeled):
        for item in self.parent.segmentItems:
            item.setVisible(True)
            if item.labelName != '':
                item.setVisible(showLabeled)

    def arrangeItems(self):
        items = self.selectedItems()
        if len(items) == 0:
            for item in self.parent.segmentItems:
                item.setPos(item.oldPos)
        else:
            self.calculateGridPositions(items)

    def calculateGridPositions(self, items):
        selItems = sorted(items, key= lambda t: t.pos().y())
        if (len(selItems) > 1):
            nx = math.ceil(math.sqrt(len(selItems)))
            ny = math.ceil(len(selItems)/nx)
            minX = min(selItems, key= lambda t: t.pos().x()).pos().x()
            minY = min(selItems, key= lambda t: t.pos().y()).pos().y()
            
            rowIter = 0
            while (len(selItems) >= nx):
                rowVals = selItems[0:nx]
                del selItems[0:nx]
                rowVals = sorted(rowVals, key= lambda t: t.pos().x())
                
                colIter = 0
                for rowVal in rowVals:
                    rowVal.setPos(minX+colIter*pv.cropSize*2,minY+rowIter*pv.cropSize*2)
                    colIter +=1
                rowIter +=1

            rowVals = sorted(selItems, key= lambda t: t.pos().x())
            colIter = 0
            for rowVal in rowVals:
                rowVal.setPos(minX+colIter*pv.cropSize*2,minY+rowIter*pv.cropSize*2)
                colIter +=1     

class ItemViewer(QGraphicsView):
    def __init__(self, parent=None):
        super(ItemViewer, self).__init__(parent)
        self._zoom = 1
        self._scene = GraphicsScene(self)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.segmentItems = []
        self.labels = {}
    
    def receiveSegments(self, images):
        for image in images:
            fvec = image.featureVec
            self.segmentItems.append(image)
            self._scene.addItem(image)
        self.update()

    def removeSegments(self):
        for item in self.segmentItems:
            self._scene.removeItem(item)
        self.segmentItems.clear()

    def wheelEvent(self, event):
        self._scene.setSceneRect(self._scene.itemsBoundingRect())
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor
        oldPos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)
        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())
        self.update()

    def keyPressEvent(self, event):
            if event.key() == Qt.Key_Alt:
                self._scene.arrangeItems()


        