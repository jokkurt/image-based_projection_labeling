from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import programVariables as pv

class SegmentItem(QGraphicsPixmapItem):
    def __init__(self, pix):
        super(SegmentItem,self).__init__(pix)
        self.originalPos=[]
        self.oldPos = QPointF(0.0,0.0)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.featureVec = []
        self.timeLineSegment = None
        self.labelName = ''
        self.labelColor = QColor(125,125,125)
        self.overviewPixmap = QGraphicsPixmapItem(self)
        self.overviewPixmap.setVisible(False)
        self.frameNr = 0


    def updateLabel(self, name, color,fromTimeline=False):
        self.labelName = name
        self.labelColor = color
        pix= self.pixmap()
        painter = QPainter(pix)   
        painter.setRenderHint( QPainter.Antialiasing )
        painter.setPen(QPen(self.labelColor,10))
        painter.setBrush(QColor(color.red(),color.green(),color.blue(),100))
        painter.drawRect(0,0,pv.cropSize*2,pv.cropSize*2)
        painter.end()
        self.setPixmap(pix)
        if not fromTimeline:
            self.timeLineSegment.updateLabel(self.labelName,self.labelColor)
    
    def hoverEnterEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.overviewPixmap.setVisible(True)

    def hoverLeaveEvent(self, event):
        self.overviewPixmap.setVisible(False)

