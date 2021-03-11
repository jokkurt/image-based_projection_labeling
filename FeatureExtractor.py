from img2vec_pytorch import Img2Vec
from PIL import Image
from scipy import spatial
import cv2 as cv
import os
import numpy as np

class FeatureExtractor(object):
    """This class extracts feature vectors from images"""
    def __init__(self):
        self.featureExtractor = Img2Vec(cuda=True,model='alexnet')
        self.featuresLocal = []
        self.featuresGlobal = []
    
    def loadFeatures(self,filename):
        """
        Loads feature vectors from file if saved before (see flag in programVariables)
        """
        strfile = os.path.basename(filename)
        fname = os.path.splitext(strfile)[0]
        imagefname = fname+".features.npy"
        strpath = os.path.dirname(filename)+"/"+fname+"/"
        finalName = strpath+imagefname
        if os.path.isfile(finalName):
            with open(finalName, 'rb') as f:
                self.featuresLocal = np.load(f,allow_pickle=True)
                self.featuresGlobal= np.load(f,allow_pickle=True)

    def getFeatures(self, image,fnr,featureType):
        """
        This function extracts a feature vector from the input image and returns it.
        """
        if featureType == 'l' and len(self.featuresLocal) !=0:
            return self.featuresLocal[fnr]
        elif featureType == 'g' and len(self.featuresGlobal) !=0:
            return self.featuresGlobal[fnr]
        else:
            crop = Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB))
            currentFeatures = self.featureExtractor.get_vec(crop,tensor=False)
            return currentFeatures

    def compareFeatures(self, vec1, vec2):
        """
        This function takes two feature vectors and calculates the cosine distance between them.
        """
        similarity = 1 - abs(spatial.distance.cosine(vec1, vec2))
        return similarity
