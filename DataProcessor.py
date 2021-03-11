import FeatureExtractor as fe
import programVariables as pv
import UI.SegmentItem as si
import cv2 as cv
import numpy as np
import pandas as pd
import threading
import os
import math
import json
import umap
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class DataProcessor(QObject):
    """
    This class handles how video and gaze is processed
    """
    sendStatusUpdate = pyqtSignal(int)
    sendSegmentsReady = pyqtSignal()

    def __init__(self,parent,gaze,video):
        QObject.__init__(self,parent)
        # init feature extractor
        self.parent = parent
        self.featureExtractor = fe.FeatureExtractor()
        self.featureExtractor.loadFeatures(video.filename)
        self.gazeReader = gaze
        self.videoReader = video
        self.slitScanLocal = self.create_blank((2*pv.cropSize),self.videoReader.videoCaptureFrameCount)
        self.slitScanGlobal = self.create_blank((2*pv.cropSize),self.videoReader.videoCaptureFrameCount)
        self.slitScanLocalImage = None
        self.slitScanGlobalImage = None

        self.similaritiesLocal = []
        self.similaritiesGlobal = []
        self.similaritiesLocalSmoothed = []
        self.similaritiesGlobalSmoothed = []
        self.featureVectorsLocal = []
        self.featureVectorsGlobal = []
        self.segments = []
        self.segmentItems = []
        self.timeLineSegments = []

    def extractSegments(self,gaze,video):
        """
        This function extracts the feature vectors from the data and creates segments
        :param gaze: is the gaze data which contains a dataframe
        :param video: is the video in form of an opencv videoreader
        """
        previousFeaturesLocal = []
        currentFeaturesLocal = []
        previousFeaturesGlobal = []
        currentFeaturesGlobal = []
        count = 100.0/self.videoReader.videoCaptureFrameCount
        for currentFnr in range(int(self.videoReader.videoCaptureFrameCount)):
            #reset the measures for each new frame
            currentSimilarityLocal = 0.0
            currentSimilarityGlobal = 0.0
            tempcrop = []
            currentFeaturesLocal = []
            currentFeaturesGlobal = []

            ret, img = video.read()
            # get the gaze data for the current frame
            currentEntries = gaze[gaze['FNR'] == currentFnr]
            # get the first gaze point in a frame 
            if not currentEntries.empty:
                positionX =-1
                positionY =-1
                valisnan = math.isnan(currentEntries['B POR X [px]'].iloc[0])
                if not valisnan:
                    positionX = int(currentEntries['B POR X [px]'].iloc[0])
                    positionY = int(currentEntries['B POR Y [px]'].iloc[0])

                # try to crop the image to the gaze position
                success, tempcrop = self.getCrop(img,positionX,positionY,pv.cropSize)
                # only proceed it a crop could be performed
                if success:
                    #extract features from crop
                    currentFeaturesLocal = self.featureExtractor.getFeatures(tempcrop,currentFnr,'l')
                    currentFeaturesGlobal = self.featureExtractor.getFeatures(img,currentFnr,'g')
                    # save thumbnail if flag is enabled
                    if pv.saveThumbnails:
                        self.saveThumbnail(currentFnr,self.videoReader.filename,tempcrop)
                    #save preview image if flag is enabled
                    if pv.saveImage:
                        overview = self.convertCVImageToPixmap(img)
                        self.drawGaze(overview,currentFnr)
                        overview = overview.scaledToWidth(250)
                        self.saveImage(currentFnr,self.videoReader.filename,overview)


                    # if features from the previous frame exist, compare them
                    if len(previousFeaturesLocal)!=0:
                        currentSimilarityLocal = 1.0-self.featureExtractor.compareFeatures(previousFeaturesLocal,currentFeaturesLocal) 
                        currentSimilarityGlobal = 1.0-self.featureExtractor.compareFeatures(previousFeaturesGlobal,currentFeaturesGlobal)
                    # remember the features
                    previousFeaturesLocal = currentFeaturesLocal
                    previousFeaturesGlobal = currentFeaturesGlobal

                    # add this frame to the slitscan
                    self.renderSlitScan(currentFnr,currentSimilarityLocal,currentSimilarityGlobal,tempcrop,img,int(0))
            
            #append values to list
            self.similaritiesLocal.append(currentSimilarityLocal)
            self.similaritiesGlobal.append(currentSimilarityGlobal)
            self.featureVectorsLocal.append(currentFeaturesLocal)
            self.featureVectorsGlobal.append(currentFeaturesGlobal)

            self.sendStatusUpdate.emit(int(currentFnr*count))

        self.similaritiesLocalSmoothed = savgol_filter(self.similaritiesLocal, 5, 2)
        self.similaritiesGlobalSmoothed = gaussian_filter1d(self.similaritiesGlobal,1)
        self.sendStatusUpdate.emit(100)
        if pv.saveFeatures:
            self.saveFeatures(self.videoReader.filename)

        self.segmentData(self.similaritiesLocal, self.similaritiesLocalSmoothed)
        self.convertSlitScan() # converts the slitscan into a qimage
    
    def saveFeatures(self,filename):
        """
        If flag is set, save the feature vectors to a binary file
        """
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+".features.npy"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        if not os.path.isfile(finalName):
            with open(finalName, 'wb') as f:
                np.save(f, self.featureVectorsLocal)
                np.save(f, self.featureVectorsGlobal)

    def saveThumbnail(self,fnr,filename,image):
        """
        If flag is set, save thumbnails to file
        """
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+"."+str(fnr)+".png"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        if not os.path.exists(strpath):
            os.makedirs(strpath)
        if not os.path.isfile(finalName):
            cv.imwrite(finalName,image)
        
    def saveImage(self,fnr,filename,image):
        """
        If flag is set, save previews to file
        """
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+"."+str(fnr)+".g.png"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        if not os.path.isfile(finalName):
            image.save(finalName)

    def segmentData(self,simValues,smoothedValues,threshold=1.0):
        """
        Calculates segment borders based on similarity value and threshold (gradient and smoothed values not applied)
        """
        self.segments = []
        left = 0
        right = 0
        i=0
        gradients = np.gradient(simValues)
        previousGradient = -1
        previousValue = 0
        for value in simValues:
            if i == len(simValues)-1:
                right = i
                self.segments.append((left,right))
            elif value == 0:
                if previousValue!=0:
                    right = i-1
                    self.segments.append((left,right))
                left=i
                right = i
            else:
                if previousValue ==0:
                    left = i
                    right = i
                if value > threshold:
                    right = i-1
                    self.segments.append((left,right))
                    left = i

            previousGradient = gradients[i]
            previousValue = value
            i+=1

    def createSegmentItems(self):
        """
        Starts a thread for the creation of segment items for the projection view
        """
        self.segmentItems.clear()
        th = threading.Thread(target=self.processSegmentItems)
        th.start()

    def processSegmentItems(self):
        """
        Iterates through segments and creates images for each segment
        """
        i = 0
        count = 100.0/len(self.segments)
        for segment in self.segments:
            item = self.segmentToPixmap(segment,i)
            if item != None:
                self.segmentItems.append(item)        
            i += 1
            self.sendStatusUpdate.emit(int(i*count))
        self.sendSegmentsReady.emit()

    def segmentToPixmap(self,segment, segmentNr):
        """
        Creates an image for a segment of the data
        """
        # Extract image from video for the segment
        centerFrame = round((segment[0]+segment[1])/2.0)
        segmentSize = segment[1]-segment[0]+1
        gaze = self.gazeReader.gazeData
        currentEntries = gaze[gaze['FNR'] == centerFrame]
        timeLineSegment = self.timeLineSegments[segmentNr]
            # get the first gaze point in a frame 
        if not currentEntries.empty:
            positionX =-1
            positionY =-1
            valisnan = math.isnan(currentEntries['B POR X [px]'].iloc[0])
            if not valisnan:
                positionX = int(currentEntries['B POR X [px]'].iloc[0])
                positionY = int(currentEntries['B POR Y [px]'].iloc[0])
            
            crop_success,crop = self.videoReader.getCrop(centerFrame)
            #pixmap_crop = None
            if not crop_success:
                image= self.videoReader.getFrame(centerFrame)
                success,crop = self.getCrop(image,positionX,positionY,pv.cropSize)
                if success:
                    pixmap_crop = self.convertCVImageToPixmap(crop)
                    crop_success = True
 
            preview_success, preview = self.videoReader.getPreview(centerFrame)
            if not preview_success:
                preview = self.videoReader.getFrame(centerFrame)
                preview_pix = self.convertCVImageToPixmap(preview)
                self.drawGaze(preview_pix,centerFrame)
                preview = preview_pix.scaledToWidth(250)
                preview_success = True

            if crop_success and preview_success:
                pixmap_crop = self.convertCVImageToPixmap(crop)
                pixmap2 = self.drawSegmentLength(pixmap_crop,segmentSize)
                pixmapItem = si.SegmentItem(pixmap2)
                pixmapItem.featureVec = self.featureVectorsLocal[centerFrame].copy()
                pixmapItem.overviewPixmap.setPixmap(preview)
                pixmapItem.timeLineSegment = timeLineSegment
                timeLineSegment.segmentItem = pixmapItem
                pixmapItem.frameNr = centerFrame
                return pixmapItem
        return None

    def drawSegmentLength(self,pix,segmentSize):
        """
        Draws a drop shadow for the image according to the segment length
        """
        pm = QPixmap(pix.width()+segmentSize,pix.height()+segmentSize)
        pm.fill(QColor(0,0,0,0))
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.HighQualityAntialiasing,QPainter.SmoothPixmapTransform)
        painter.setBrush(QColor(0,0,0,100))
        painter.setPen(QPen(QColor(0,0,0,0),0))
        painter.drawRect(segmentSize,segmentSize,pix.width(),pix.height())
        painter.drawPixmap(0,0,pix)
        painter.end()
        return pm

    def convertCVImageToPixmap(self,image):
        """
        Conversion from OpenCV image to Qt QPixmap
        """
        h, w, ch = image.shape
        image = image.copy()
        bytes_per_line = ch * w
        outImage = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        outImage = outImage.rgbSwapped()
        return QPixmap.fromImage(outImage)
    
    def drawGaze(self,image,fnr):
        """
        Draws the gaze point on an image
        """
        success, pos = self.gazeReader.getGaze(fnr)
        if success:
            painter = QPainter(image)
            painter.setRenderHint( QPainter.Antialiasing )
            painter.setPen(QPen(QColor(255,255,200,200),10))
            painter.drawRect(pos[0]-pv.cropSize,pos[1]-pv.cropSize,pv.cropSize*2,pv.cropSize*2)
            painter.drawEllipse(pos[0],pos[1],5,5)
            painter.end()

    def convertSlitScan(self):
        """
        Converts the slitscans to QImages
        """
        h, w, ch = self.slitScanLocal.shape
        bytes_per_line = ch * w
        self.slitScanLocalImage = QImage(self.slitScanLocal.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.slitScanLocalImage = self.slitScanLocalImage.rgbSwapped()
        self.slitScanGlobalImage = QImage(self.slitScanGlobal.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.slitScanGlobalImage = self.slitScanGlobalImage.rgbSwapped()

    def getCrop(self, image, xpos, ypos, cropsize):
        """
        This function checks if the gaze position is within the bounds of the image.
        :param image: image to crop
        :param xpos: x gaze coordinate
        :param ypos: y gaze coordinate
        :param cropsize:
        :return: true if succes and cropped image
        """
        height = image.shape[0]
        width = image.shape[1]
        #check if crop is within image boundaries    
        if (xpos >= cropsize and xpos < width-cropsize and ypos >= cropsize and ypos < height-cropsize  ):
            crop = image[(ypos-cropsize):(ypos+cropsize),(xpos-cropsize):(xpos+cropsize)]
            return True, crop
        else:
            return False, 0

    def renderSlitScan(self, fnr, similarityLocal, similarityGlobal, image, globalImage,thresh):
        """
        This function adds the current frame to a slitscan representation of the gaze+video data.
        """
        adjustedSimilarityL = int(round(similarityLocal*100))
        adjustedSimilarityG = int(round(similarityGlobal*100))

        if len(image) > 0:
                # process local image
                slitHeight = self.slitScanLocal.shape[0]
                height = image.shape[0]
                width = image.shape[1]
                crop = image[0:height,pv.cropSize-1:pv.cropSize]
                self.slitScanLocal[0:height,fnr:fnr+1] = crop
                #process global image
                resized = cv.resize (globalImage, (globalImage.shape[1], height), interpolation = cv.INTER_AREA)
                globalCrop = resized[0:height,int(globalImage.shape[1]/2):int(globalImage.shape[1]/2)+1]
                self.slitScanGlobal[0:height,fnr:fnr+1] = globalCrop

    def create_blank(self,width, height, rgb_color=(255, 255, 255)):
        """
        This function creates an empty image
        """
        # Create black blank image
        image = np.zeros((width, height, 3), np.uint8)
        # Since OpenCV uses BGR, convert the color first
        color = tuple(reversed(rgb_color))
        # Fill image with color
        image[:] = color
        return image
    
    def projectItems(self,itemList):
        """
        Calculates a 2D embedding for the feature vectors of the items and scales the position
        """
        featureVecs=[]
        for item in itemList:
            featureVecs.append(item.featureVec)
       
        embedder = umap.UMAP(metric='cosine',n_neighbors=5)
        embedding = embedder.fit_transform(featureVecs)
        
        i=0
        for item in itemList:
           pos = embedding[i]
           itemList[i].originalPos=pos
           itemList[i].setPos(pos[0]*pv.positionScale,pos[1]*pv.positionScale)
           itemList[i].oldPos = itemList[i].pos()
           i +=1 

    def createSimilarityPlot(self):
        """
        Renders the calculated similarity values
        """
        pix = QPixmap(self.videoReader.videoCaptureFrameCount,(2*pv.cropSize))
        pix.fill(QColor(255,255,255,100))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.HighQualityAntialiasing,QPainter.SmoothPixmapTransform)
        painter.setPen(QPen(QColor(50,50,50,200),2,Qt.SolidLine,Qt.RoundCap))
        xPos =0
        oldPos = QPoint(0,0)
        for value in self.similaritiesLocal:
            yPos = (1.0-value)*(2.0*pv.cropSize) 
            painter.drawLine(oldPos,QPoint(xPos,yPos))
            oldPos= QPoint(xPos,yPos)
            xPos +=1
        painter.end()
        return pix

    def createTimelineScale(self):
        """
        Renders the scale for the timestamps on the timelines
        """
        fps = int(self.videoReader.videoCaptureFps)
        fcount = self.videoReader.videoCaptureFrameCount
        pix = QPixmap(self.videoReader.videoCaptureFrameCount,pv.plotHeight)
        smallTick = pv.plotHeight/4
        bigTick = pv.plotHeight/2
        pix.fill(QColor(0,0,0,0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.HighQualityAntialiasing,QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.TextAntialiasing,True)
        painter.setPen(QPen(QColor(50,50,50,255),1,Qt.SolidLine,Qt.RoundCap))
        for fnr in range(fcount):
            tick = fnr % fps
            if tick == 0 or fnr ==fcount-1:
                painter.drawLine(fnr,0,fnr,smallTick)
                if (fnr%(fps*5))==0:
                    stringText, time = self.frameToTime(fnr,self.videoReader.videoCaptureFps)
                    painter.drawLine(fnr,0,fnr,bigTick)
                    painter.drawText(fnr,pv.plotHeight,stringText)
            fnr +=1
        painter.end()
        return pix

    def frameToTime(self,fnr,fps):
        """
        Calculates the timestamp of a frame
        """
        secFactor = 1000.0/float(fps)
        secs = round(float(fnr)*secFactor)
        timestring = QTime(0,0,0,0)
        timestring = timestring.addMSecs(secs)
        return timestring.toString('hh.mm.ss'), timestring