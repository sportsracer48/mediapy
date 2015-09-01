'''
Created on Jul 11, 2015

@author: Henry
'''
#import pyaudio  # @UnusedImport
import math  # @UnusedImport
from mymedia import *  # @UnusedWildImport
import time  # @UnusedImport

path = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\02DayIsDone.aif.aiff'
path2 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\moondog.Bird_sLament.wav'
path3 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\seedburns.aif'
path4 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\boygeorge.au'
path5 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\Blip.wav'
path6 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\g722.aifc' #shouldn't work, aifc not supported
path7 = 'C:\\Users\\Henry\\Documents\\LiClipse Workspace\\jes\\tests\\test-sounds\\acidisneeded.aif'


image = makeEmptyPicture(600, 600)
addText(image, 100, 100, "It worked")
show(image)