import os
import programVariables as pv # global variables

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import VideoReader as vdr # component for video reading
import GazeReader as gdr # component for gaze reading
import DataProcessor as dpr # component for processing gaze and video

import UI.AppMainWindow as gui

if __name__ == '__main__':    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
    window = gui.Ui() # init qt gui
    app.exec()