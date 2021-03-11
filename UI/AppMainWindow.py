from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import os
import csv
import umap
import numpy as np
import UI.OverviewWidget as ovw
import UI.ItemViewer as itv
import UI.LabelDialog as lad

class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('UI\\appmainwindow.ui', self) # Load the .ui file
        self.show() # Show the GUI
        self.dockWidget = self.findChild(QDockWidget, 'dockWidget')
        self.itemViewer = self.findChild(itv.ItemViewer, 'itemViewer')
        self.checkShowLabeled = self.findChild(QCheckBox, 'checkShowLabeled')
        self.checkShowLabeled.toggled.connect(self.itemViewer._scene.toogleShowLabeled)
        self.listLabelsWidget = self.findChild(QListWidget, 'listLabels')
        self.sliderScale = self.findChild(QSlider, 'sliderScale')
        self.sliderScale.valueChanged.connect(self.adjustScale)
        self.buttonAdd = self.findChild(QToolButton, 'buttonAdd')
        self.buttonAdd.clicked.connect(self.addLabel)
        self.buttonRemove = self.findChild(QToolButton, 'buttonRemove')
        self.act_open = self.findChild(QAction, 'actionopen')
        self.act_open.triggered.connect(self.onActionLoadData)
        self.act_save = self.findChild(QAction, 'actionSave_Annotation')
        self.act_save.triggered.connect(self.onActionSaveAnnotation)

        self.buttonProjection = self.findChild(QToolButton, 'buttonProjection')
        self.buttonProjection.clicked.connect(self.projectNew)
        self.spinNeighbors = self.findChild(QSpinBox, 'spinNeighbors')
        self.comboMetric = self.findChild(QComboBox, 'comboMetric')
        self.buttonScreenshot = self.findChild(QToolButton, 'buttonScreenshot')
        self.buttonScreenshot.clicked.connect(self.screenshot)

        self.dataSets = []
        self.labels = {}
        self.itemViewer.labels = self.labels

        self.scrollArea = self.findChild(QScrollArea, 'scrollArea')
        self.marea = QMainWindow()
        self.scrollArea.setWidget(self.marea)

    @pyqtSlot()
    def onActionLoadData(self):
        overviewWidget = ovw.OverviewWidget()
        if (overviewWidget.openFiles()):
            overviewWidget.initWidget()
            item = QListWidgetItem()
            item.setSizeHint(overviewWidget.sizeHint())
            overviewWidget.buttonSubmit.clicked.connect(self.sendSegments)
            overviewWidget.graphicView.labels = self.labels
            overviewWidget.graphicView.scene.sendSelectionUpdate.connect(self.itemViewer._scene.receiveSelectionUpdate)

            overviewWidget.dataProcessor.sendSegmentsReady.connect(self.projectSegment)
            self.dataSets.append(overviewWidget)

            dock = QDockWidget()
            dock.setWidget(overviewWidget)
            dock.setWindowTitle(os.path.basename(overviewWidget.videoReader.filename))
            self.marea.addDockWidget(Qt.LeftDockWidgetArea,dock)
    
    @pyqtSlot()
    def sendSegments(self):
        overviewWidget = self.sender().parent()
        overviewWidget.dataProcessor.createSegmentItems()

    @pyqtSlot()
    def projectSegment(self):
        overviewWidget = self.sender().parent
        self.itemViewer.receiveSegments(overviewWidget.dataProcessor.segmentItems)    
        self.projectNew()

    @pyqtSlot()
    def projectNew(self):
        """
        Calculates a new 2D embedding of the feature vectors on demand
        """
        itemList = self.itemViewer.segmentItems
        featureVecs=[]
        for item in itemList:
            vec = item.featureVec
            featureVecs.append(item.featureVec)
        
        featureVecsarr = np.vstack(featureVecs)

        metricString = self.comboMetric.currentText() 
        neighbors = self.spinNeighbors.value()
        posScale = self.sliderScale.value()

        embedder = umap.UMAP(metric=metricString,n_neighbors=neighbors)
        embedding = embedder.fit_transform(featureVecsarr)
        
        i=0
        for item in itemList:
           pos = embedding[i]
           itemList[i].originalPos=pos
           itemList[i].setPos(pos[0]*posScale,pos[1]*posScale)
           itemList[i].oldPos = itemList[i].pos()
           i +=1 

    @pyqtSlot()
    def addLabel(self):
         dlg = lad.LabelDialog(self)
         if dlg.exec():
             labelName = dlg.lineName.text()
             color = dlg.labelColor
             self.labels[labelName] = color
         self.listLabelsWidget.clear()
         for key in self.labels:
             item = QListWidgetItem(key)
             pixmap = QPixmap(100,100)
             pixmap.fill(self.labels[key])
             item.setIcon(QIcon(pixmap))
             self.listLabelsWidget.addItem(item)

    @pyqtSlot(int)
    def adjustScale(self,value):
        for item in self.itemViewer.segmentItems:
            orgPos = item.originalPos
            item.setPos(orgPos[0]*value,orgPos[1]*value)
            item.oldPos = item.pos()

    @pyqtSlot()
    def screenshot(self):
        rect = self.itemViewer._scene.sceneRect()
        image = QImage(rect.width(),rect.height(),QImage.Format_ARGB32)
        painter = QPainter(image)
        self.itemViewer._scene.render(painter)
        painter.end()
        image.save("screenshot.png")

    @pyqtSlot()
    def onActionSaveAnnotation(self):
        """
        Save the annotation with one label per segment range, separate files for each input file
        """
        for dataSet in self.dataSets:
            fname= dataSet.videoReader.filename+'.csv'
            with open(fname, 'w', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(["Frames", "Label"])
                for num,segItem in enumerate(dataSet.dataProcessor.segmentItems):
                    bounds = str(dataSet.dataProcessor.segments[num])
                    labName = segItem.labelName
                    writer.writerow([bounds, labName])