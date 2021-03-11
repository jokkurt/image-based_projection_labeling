from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

class LabelDialog(QDialog):
    def __init__(self, parent=None):
        super(LabelDialog,self).__init__(parent)
        uic.loadUi('UI\\labeldialog.ui', self) # Load the .ui file
        self.lineName = self.findChild(QLineEdit, 'lineName')
        self.buttonColor = self.findChild(QToolButton, 'buttonColor')
        self.buttonColor.clicked.connect(self.pickColor)
        self.labelColor = QColor(125,125,125)
        pixmap = QPixmap(100,100)
        pixmap.fill(self.labelColor)
        self.buttonColor.setIcon(QIcon(pixmap))

    @pyqtSlot()
    def pickColor(self):
        self.labelColor = QColorDialog.getColor()
        pixmap = QPixmap(100,100)
        pixmap.fill(self.labelColor)
        self.buttonColor.setIcon(QIcon(pixmap))