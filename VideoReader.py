import cv2 as cv
import numpy as np
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class VideoReader(object):
    """This class reads video data"""
    def __init__(self, filename):
        self.videoCapture = cv.VideoCapture(filename)  
        # get frames per second
        self.videoCaptureFps = self.videoCapture.get(cv.CAP_PROP_FPS)
        # get total frame count
        self.videoCaptureFrameCount = int(self.videoCapture.get(cv.CAP_PROP_FRAME_COUNT))
        self.videoHeight = int(self.videoCapture.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.videoWidth = int(self.videoCapture.get(cv.CAP_PROP_FRAME_WIDTH))
        self.lastFrame=0
        self.filename = filename
    def getFrame(self,fnr):
        """
        This function retrieves a video image by frame number
        """
        if self.lastFrame != fnr-1:
            self.videoCapture.set(cv.CAP_PROP_POS_FRAMES, fnr)
        success,frame = self.videoCapture.read()
        self.lastFrame=fnr

        if not success:
            frame = np.zeros((self.videoHeight, self.videoWidth, 3), np.uint8)
            self.lastFrame=0
        
        return frame

    def getPreview(self,fnr):
        """
        This function returns a preview image if it was saved before (see flag in program variables)
        """
        filename = self.filename
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+"."+str(fnr)+".g.png"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        success = False
        if os.path.isfile(finalName):
            return True,QPixmap(finalName)
        else:
            return False,QPixmap()

    def getCrop(self,fnr):
        """
        This function returns a thumbnail image if it was saved before (see flag in program variables)
        """
        filename = self.filename
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+"."+str(fnr)+".png"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        success = False
        frame = None
        if os.path.isfile(finalName):
            frame = cv.imread(finalName)
            success = True
        return success,frame