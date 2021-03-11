import pandas as pd
import numpy as np
import math
class GazeReader(object):
    """This class handles the gaze data from SMI Glasses"""
    def __init__(self, filename):
        # read gaze into dataframe
        self.gazeData = pd.read_csv (filename, sep='[;,\t]', comment='#', engine='python')
        # create a new column for frame number
        self.gazeData['FNR'] = 0
        self.filename = filename

    def calculateFrameNumbers(self,videoFps):
        """
        Calculates the frame number for each sample based on fps
        """
        frameTimes = self.gazeData['Frame']
        # calculate the frame for each sample
        for rowNr in range(len(frameTimes)):
            time = frameTimes[rowNr].split(':') 
            frameVal = float(time[0])*60.0*60.0*videoFps+float(time[1])*60.0*videoFps+float(time[2])*videoFps+float(time[3])
            self.gazeData.at[rowNr,'FNR'] = frameVal

    def getGaze(self,fnr):
        """
        Returns the first gaze sample for a specific frame
        """
        currentEntries = self.gazeData[self.gazeData['FNR'] == fnr]
        if not currentEntries.empty:
            positionX = int(currentEntries['B POR X [px]'].iloc[0])
            positionY = int(currentEntries['B POR Y [px]'].iloc[0])
            return True, [positionX,positionY]
        return False, [0,0]