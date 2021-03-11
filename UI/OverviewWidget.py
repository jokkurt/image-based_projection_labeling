import os
import programVariables as pv

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd
#from timeit import default_timer as timer
import threading
import UI.TimelineView as tlv

import VideoReader as vdr
import GazeReader as gdr
import DataProcessor as dpr

class OverviewWidget(QWidget):
    sendAdjustView = pyqtSignal()
    def __init__(self, parent=None):
        super(OverviewWidget,self).__init__(parent)
        uic.loadUi('UI\\overviewwidget.ui', self) # Load the .ui file

        self.sliderTime = self.findChild(QSlider, 'sliderTime')
        self.sliderTime.valueChanged.connect(self.sliderTimeChanged)
        self.graphicView = self.findChild(tlv.TimelineView, 'graphicsView')
        self.buttonSubmit = self.findChild(QToolButton, 'buttonSubmit')
        self.spinThreshold = self.findChild(QDoubleSpinBox, 'spinThreshold')
        self.spinThreshold.valueChanged.connect(self.spinValueChanged)
        self.checkLocal = self.findChild(QCheckBox,'checkLocal')
        self.checkLocal.toggled.connect(self.viewOptionsToggled)
        self.checkGlobal = self.findChild(QCheckBox,'checkGlobal')
        self.checkGlobal.toggled.connect(self.viewOptionsToggled)
        self.checkSim = self.findChild(QCheckBox, 'checkSim')
        self.checkSim.toggled.connect(self.viewOptionsToggled)
        self.progressBar = self.findChild(QProgressBar, 'progressBar')
        self.timeEdit = self.findChild(QTimeEdit, 'timeEdit')
        self.buttonScreenshot = self.findChild(QToolButton, 'buttonScreenshot')
        self.buttonScreenshot.clicked.connect(self.screenshot)
        self.parent = parent
        self.fileVideo = ''
        self.fileGaze = ''
        self.videoReader = None
        self.gazeReader = None
        self.dataProcessor = None

    def openFiles(self):
        self.fileVideo = QFileDialog.getOpenFileName(None,"Open Video", os.path.dirname(__file__), "Video Files (*.avi *.mp4 *.mpg)")[0]
        self.fileGaze = os.path.splitext(self.fileVideo)[0]+".txt"
        if len(self.fileVideo)>0:
            return True
        else:
            return False

    def initWidget(self):
        # init video
        self.videoReader = vdr.VideoReader(self.fileVideo)
        self.sliderTime.setMaximum(self.videoReader.videoCaptureFrameCount-1)
        # init gaze
        self.gazeReader = gdr.GazeReader(self.fileGaze)
        # calculate corresponding frames for each gaze point
        self.gazeReader.calculateFrameNumbers(self.videoReader.videoCaptureFps)
        #init data processor
        self.dataProcessor = dpr.DataProcessor(self,self.gazeReader,self.videoReader)
        self.dataProcessor.sendStatusUpdate.connect(self.progressBar.setValue)

        self.sendAdjustView.connect(self.adjustView)

        th = threading.Thread(target=self.processData)
        th.start()

    def processData(self):
        self.dataProcessor.extractSegments(self.gazeReader.gazeData,self.videoReader.videoCapture)
        self.sendAdjustView.emit()

    @pyqtSlot()
    def adjustView(self):
        self.graphicView.setSlitscanLocal(QPixmap.fromImage(self.dataProcessor.slitScanLocalImage))
        self.graphicView.setSlitscanGlobal(QPixmap.fromImage(self.dataProcessor.slitScanGlobalImage))
        self.graphicView.similarityPlot.setPixmap(self.dataProcessor.createSimilarityPlot())
        self.graphicView.drawSegments(self.dataProcessor.segments)

        self.graphicView.thresholdSlider =QGraphicsRectItem(0,0,self.videoReader.videoCaptureFrameCount,2)
        self.graphicView.thresholdSlider.setBrush(QColor(255,255,200,255))
        self.graphicView.thresholdSlider.setPen(QPen(QColor(255,0,0,100),2))
        self.graphicView.scene.addItem(self.graphicView.thresholdSlider)

        self.graphicsView.timelineScale.setPixmap(self.dataProcessor.createTimelineScale())

        self.dataProcessor.timeLineSegments = self.graphicView.segmentItems
        self.viewOptionsToggled(True)

    def spinValueChanged(self):
        value = self.spinThreshold.value()
        self.dataProcessor.segmentData(self.dataProcessor.similaritiesLocal, self.dataProcessor.similaritiesLocalSmoothed,value)
        self.graphicView.drawSegments(self.dataProcessor.segments)
        self.graphicView.thresholdSlider.setPos(0,(1.0-value)*pv.cropSize*2)
        self.dataProcessor.timeLineSegments = self.graphicView.segmentItems
    
    def linkItems(self,itemList):
        segments = self.graphicView.segmentItems
        i = 0

    def getFrame(self,val):
        image = self.videoReader.getFrame(val)
        pix = self.dataProcessor.convertCVImageToPixmap(image)
        self.dataProcessor.drawGaze(pix,val)
        self.graphicView.updateVideoframe(pix)

    @pyqtSlot(int)
    def sliderTimeChanged(self,val):
        self.graphicView.updateTime(val)
        self.getFrame(val)
        text,time = self.dataProcessor.frameToTime(val,self.videoReader.videoCaptureFps)
        self.timeEdit.setTime(time)

    @pyqtSlot(bool)
    def viewOptionsToggled(self,val):
        self.graphicView.toggleComponents(self.checkLocal.isChecked(),self.checkGlobal.isChecked(),self.checkSim.isChecked())

    @pyqtSlot()
    def screenshot(self):
        rect = self.graphicView.scene.sceneRect()
        image = QImage(rect.width(),rect.height(),QImage.Format_ARGB32)
        painter = QPainter(image)
        self.graphicView.scene.render(painter)
        painter.end()
        fname = self.videoReader.filename+"_screenshot.png"
        image.save(fname)