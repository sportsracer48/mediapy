# 
# Media Wrappers for "Introduction to Media Computation"
# Started: Mark Guzdial, 2 July 2002
#
# Revisions:
# 18 June 2003: (ellie)
#    Added (blocking)play(AtRate)InRange methods to Sound class 
#      and global sound functions
#    Changed getSampleValue, setSampleValue to give the appearance 
#      of 1-based indexing
#    Added getLeftSampleValue and getRightSampleValue to Sound class
# 14 May 2003: Fixed discrepancy between getMediaPath and setMediaFolder (AdamW) 
# 8 Nov: Fixed getSamplingRate (MarkG)
# 1 Nov: Fixed printing pixel
# 31 Oct: Fixed pickAColor (MarkG)
# 30 Oct: Added raises, fixed error messages. Added repaint (MarkG)
# 10 Oct: Coerced value to integer in Sound.setSampleValue   (MarkR)
# 2 Oct:  Corrected calls in setSampleValueAt  (MarkG): 
# 30 Aug: Made commands more consistent and add type-checking (MarkG)
# 2 Aug: Changed to getSampleValueAt and setSampleValueAt (MarkG)
# 31 October 2005: Converted the package to no longer use Java
# 7 December Lots of new stuff
#       dumped wxwindows because it hates threads and really despises pygame
#       tkinter used as alternative this is python standard for windowing
#       add PIL as a requirement to allow for easy image export and save to jpeg
#       converted pickAFile, pickAFolder, pickAColor to TKDialog pop-ups
#       moved initialization out of the class init and into the main import
# 14 April 2007: (NadeemAbdulHamid)
#    Converted Picture and Pixel classes to use PythonImagingLibrary directly,
#    without going through pygame. This seems to provide a noticeable
#    performance increase. Fixed several bugs. Color.getRGB returns a
#    tuple in the format (r, g, b) -- before it was returning [b, g, r]!?
#    Also changed the Samples object to work as an iterator, lazily building
#    the sequence of samples from the sound, instead of building a
#    complete list of Sample objects in its constructor. Fixed some type-related
#    bugs with the values of samples; also added check to setSampleValue to ensure
#    value is not set above or below limits of int.
# 3 May 2007: (Nadeem)
#    Added in a Pixels iterator class to reduce up-front time when a
#    picture is first loaded and getPixels() is called.
# 30 May 2007: (Nadeem)
#    Only using pygame for the sound stuff (pygame.mixer module). Other
#    parts of the pygame library cause strange things to happen with
#    Tkinter on Mac OS X; added getFileName, getDirectory to Picture class
# 6 Jun 2007: (Nadeem)
#    Bug fix
# 10 Jun 2007: (Nadeem) version 1.5
#    Modified to use John Zelle's graphics library which runs the Tk loop
#    in a separate thread, making this safe to run in the normal IDLE
#    environment
# 15 Jun 2007:
#    Added pickASaveFile method; makeEmptyLength in sound takes number
#    of samples, not seconds
#


import sys
import os
import user
import traceback
import time
import numpy as Numeric
import struct

#from Tkinter import *
# import cStringIO
# from Queue import *


from threading import *
from math import sqrt
import thread
import Image
Im = Image
import ImageDraw
import ImageFont
import ImageTk
import tkFileDialog
import tkColorChooser
import pygame
import platform


# John Zelle's graphics library...
from graphics import *
_tkCall = tkCall
_tkExec = tkExec


ver = "1.5"


# only need to initialize the mixer -- other parts of pygame seem to
# interfere with Tkinter on the Mac
pygame.mixer.pre_init(22050, -16, False)
_tkExec(pygame.mixer.init)


try:
    if platform.system() == 'Darwin':
        defaultFont = ImageFont.truetype("/Library/Fonts/Times New Roman", 24)
    else:
        defaultFont = ImageFont.truetype("times.ttf", 24)
except:
        defaultFont = ImageFont.load_default()
# pygame.font.SysFont("times", 24)


mediaFolder = user.home + os.sep

print "Media Computation Library. Version " + str(ver)
print "Started by Mark Guzdial"
print "Updated by Nadeem Abdul Hamid, June 14 2007"

def version():
    global ver
    return ver

#Set a path to the media for those who want to have a shortcut (5/14/03 AW)
def setMediaPath(path=None):
    global mediaFolder
    if not path:
        path = pickAFolder()
    mediaFolder = path
    print "New media folder: "+mediaFolder
    
def getMediaPath(filename):
    global mediaFolder
    file = mediaFolder+filename
    if not os.path.isfile(file):
        print "Note: There is no file at "+file
    return file
    
def pickAFile(**options):
    path = _tkCall(tkFileDialog.askopenfilename)
    return path
    
def pickASaveFile(**options):
    path = _tkCall(tkFileDialog.asksaveasfilename)
    return path
    
def pickAFolder(**options):
    global mediaFolder
    folder = _tkCall(tkFileDialog.askdirectory)
    if folder == '':
        folder = mediaFolder
    else:
        folder = folder + os.sep
    return folder
    
def pickAColor(**options):
    color = _tkCall(tkColorChooser.askcolor)
    newColor = Color(color[0][0], color[0][1], color[0][2])
    return newColor

#And for those who think of things as folders (5/14/03 AW)  
def setMediaFolder(path=None):
    global mediaFolder
    if not path:
        path = pickAFolder()
    mediaFolder = path
    print "New media folder: "+mediaFolder

def getMediaFolder(filename):
    global mediaFolder
    file = mediaFolder+filename
    if not os.path.isfile(file) or not os.path.isdir(file):
        print "Note: There is no file at "+file
    return file
    
def getShortPath(filename):
    dirs = filename.split(os.sep)
    if len(dirs) < 1:
        return "."
    elif len(dirs) == 1:
        return dirs[0]
    else:
        return (dirs[len(dirs) - 2] + os.sep + dirs[len(dirs) - 1])

        
class PictureFrame(tk.Toplevel):

    def __init__(self, picture):
        tk.Toplevel.__init__(self)
        self.pic = picture
    
    def destroy(self):
        _tkExec(self.__destroy_help)

    def __destroy_help(self):
        self.pic.windowInactive()
        tk.Toplevel.destroy(self)


##
## IMAGE CLASSES
##          
class Picture:
    def __init__(self):
        self.title = "Unnamed"
        self.dispImage = None
        self.winActive = 0
        
    def windowInactive(self):
        self.winActive = 0

    def createImage(self, width, height):
        self.image = Im.new("RGB", (width, height))
        self.pixels = self.image.load()
        if not self.pixels:
            raise RuntimeError, 'Picture.pixels is None. Python Imaging Library 1.1.6 required.'
        self.filename = ''
        self.title = 'None'
        
    def loadImage(self,filename):
        global mediaFolder
        if not os.path.isabs(filename):
            filename = mediaFolder + filename
        self.image = Im.open(filename)
        self.pixels = self.image.load()
        if not self.pixels:
            raise RuntimeError, 'Picture.pixels is None. Python Imaging Library 1.1.6 required.'
        self.filename = filename
        self.title = getShortPath(filename)
    
    def __str__(self):
        return "Picture, filename "+self.filename+" height "+str(self.getHeight())+" width "+str(self.getWidth()) 
    
    def repaint(self):
        _tkExec(self.__repaint_help)

    def __repaint_help(self):        
        if self.winActive:
            self.dispImage = ImageTk.PhotoImage(self.getImage())
            self.item = self.canvas.create_image(0, 0, image=self.dispImage, anchor='nw')
        else:
            self.show()
        
    def show(self):
        _tkExec(self.__show_help)

    def __show_help(self):
        if not self.winActive:
            self.window = PictureFrame(self)
            self.canvas = tk.Canvas(self.window, width=self.getWidth(), 
                height=self.getHeight())
            self.dispImage = ImageTk.PhotoImage(self.getImage())
            self.item = self.canvas.create_image(0, 0, image=self.dispImage, anchor='nw')
            self.canvas.pack()
            self.winActive = 1
        else:
            self.repaint()

    def setTitle(self, title):
        self.title = title
        
    def getTitle(self):
        return self.title

    def getFileName(self):
        return self.filename

    def getDirectory(self):
        return self.filename[ : self.filename.rfind(os.sep) + 1]
        
    def getImage(self):
        return self.image

    def getTkImage(self):
        self.dispImage = ImageTk.PhotoImage(self.getImage())
        return self.dispImage
        
    def getWidth(self):
                return self.image.size[0]
    
    def getHeight(self):
                return self.image.size[1]
    
    def getPixel(self,x,y):
        return Pixel(self.pixels,x,y)
    
    def getPixels(self):
        return Pixels(self)
#        collect = []
#        for x in xrange(1,self.getWidth()+1):
#            for y in xrange(1,self.getHeight()+1):
#                collect.append(Pixel(self.pixels,x,y))
#        return collect

    # color should be a 3-tuple
    def setColorXY(self, x, y, color):
        self.pixels[x-1, y-1] = color

    # returns a 3-tuple
    def getColorXY(self, x, y):
        return self.pixels[x-1, y-1]

    def writeTo(self,filename):
        if not os.path.isabs(filename):
            filename = mediaFolder + filename
        image = self.getImage()
        image.save(filename, None, quality=90)
        self.filename = filename
        
    # draw stuff on pictures
    def addRectFilled(self,acolor,x,y,w,h):
        d = ImageDraw.Draw(self.image)
        d.rectangle( [ (x, y), (x+w, y+h) ], outline=acolor.getRGB(),
                     fill=acolor.getRGB() )
        
    def addRect(self, acolor,x,y,w,h):
        d = ImageDraw.Draw(self.image)
        d.rectangle( [ (x, y), (x+w, y+h) ], outline=acolor.getRGB() )
    
    def addOvalFilled(self, acolor,x,y,w,h):
        d = ImageDraw.Draw(self.image)
        d.ellipse( [ (x, y), (x+w, y+h) ], outline=acolor.getRGB(),
                   fill=acolor.getRGB() )
        
    def addOval(self, acolor,x,y,w,h):
        d = ImageDraw.Draw(self.image)
        d.ellipse( [ (x, y), (x+w, y+h) ], outline=acolor.getRGB() )

    def addArcFilled(self, acolor,x,y,w,h,start,angle):
        d = ImageDraw.Draw(self.image)
        d.chord( [ (x, y), (x+w, y+h) ], start, start+angle,
               outline=acolor.getRGB(), fill=acolor.getRGB() )
    
    def addArc(self, acolor,x,y,w,h,start,angle):
        d = ImageDraw.Draw(self.image)
        d.arc( [ (x, y), (x+w, y+h) ], start, start+angle,
               outline=acolor.getRGB() )
        
    def addLine(self, acolor, x1, y1, x2, y2):
        d = ImageDraw.Draw(self.image)
        d.line( [ (x1, y1), (x2, y2) ], fill=acolor.getRGB() )

    def addText(self, acolor, x, y, string):
        global defaultFont
        d = ImageDraw.Draw(self.image)
        d.text( (x, y), string, font=defaultFont, fill=acolor.getRGB())

    #def addTextWithStyle(self, acolor, x, y, string, style):


# To use Picture objects with John Zelle's graphics library:
##    win = GraphWin('Test', 500, 500)
##    p = makePicture(pickAFile())
##    im = Image(Point(250, 250), Pixmap(p.getTkImage()))
##    im.draw(win)




class Pixels:
    def __init__(self, aPicture):
        self.picture = aPicture
        self.cur = 0
        self.curx = 0  # will be incremented before first pixel is returned
        self.cury = 1
        self.len = self.picture.getWidth() * self.picture.getHeight()

    def __iter__(self):
        return self

    def next(self):
        if self.cur >= self.len:
            raise StopIteration
        self.cur += 1
        self.curx += 1
        if self.curx > self.picture.getWidth():
            self.curx = 1
            self.cury += 1
        return Pixel(self.picture.pixels, self.curx, self.cury)

    def __str__(self):
        return "Pixels, length " + str(self.len)

    def __rep__(self):
        return "Pixels, length " + str(self.len)

    def getPicture(self):
        return self.picture
        

#
# CLASS PIXEL
#
class Pixel:
    def __init__(self,pixels,x,y):
        self.x = x - 1
        self.y = y - 1
        self.pixels = pixels
    
    def __str__(self):
        return "Pixel, color="+str(self.getColor())
        
    def setRed(self,r):
                self.pixels[self.x, self.y] = (int(r), self.getGreen(), self.getBlue())
        
    def setGreen(self,g):
        self.pixels[self.x, self.y] = (self.getRed(), int(g), self.getBlue())
    
    def setBlue(self,b):
        self.pixels[self.x, self.y] = (self.getRed(), self.getGreen(), int(b))
        
    def getRed(self):
        return self.pixels[self.x, self.y][0]
        
    def getGreen(self):
        return self.pixels[self.x, self.y][1]
        
    def getBlue(self):
        return self.pixels[self.x, self.y][2]
    
    def getColor(self):
        return Color(self.getRed(),self.getGreen(), self.getBlue())

    def setColor(self,color):
                self.pixels[self.x, self.y] = (color.getRed(),
                                               color.getGreen(),
                                               color.getBlue())
                
    def getX(self):
        return self.x + 1
        
    def getY(self):
        return self.y + 1

        
class Color:
    def __init__(self,r,g,b):
        r = int(r)
        if r < 0:
            while(r<0):
                r = 256 + r
        if r > 255:
            while(r>255):
                r = r - 256
        g = int(g)
        if g < 0:
            while(g<0):
                g = 256 + g
        if g > 255:
            while(g>255):
                g = g - 256
        b = int(b)
        if b < 0:
            while(b<0):
                b = 256 + b
        if b > 255:
            while(b>255):
                b = b - 256
        self.r=r
        self.g=g
        self.b=b
    
    def __str__(self):
        return "color r="+str(self.getRed())+" g="+str(self.getGreen())+" b="+str(self.getBlue())
            
    def distance(self,color):
        r = pow((self.r - color.r),2)
        g = pow((self.g - color.g),2)
        b = pow((self.b - color.b),2)
        return sqrt(r+g+b)
    
    def __sub__(self,color):
        return Color((self.r-color.r),(self.g-color.g),(self.b-color.b))
    
    def difference(self,color):
        return self-color
        
    def getRGB(self):
        return (self.r, self.g, self.b)

    def rgbString(self):
        return color_rgb(self.r, self.g, self.b)
    
    def setRGB(self,atuple):
        self.r = atuple[1]
        self.g = atuple[2]
        self.b = atuple[3]
        
    def getRed(self):
        return int(self.r)
    
    def getGreen(self):
        return int(self.g)
    
    def getBlue(self):
        return int(self.b)
    
    def setRed(self,value):
        self.r=value
    
    def setGreen(self,value):
        self.g=value
    
    def setBlue(self,value):
        self.b=value
    
    def makeLighter(self):
        self.r = (255 - self.r) * .35 + self.r
        self.g = (255 - self.g) * .35 + self.g
        self.b = (255 - self.b) * .35 + self.b
    
    def makeDarker(self):
        self.r = self.r * .65
        self.g = self.g * .65
        self.b = self.b * .65   
        

#Constants
black = Color(0,0,0)
white = Color(255,255,255)
blue = Color(0,0,255)
red = Color(255,0,0)
green = Color(0,255,0)
gray = Color(128,128,128)
darkGray = Color(64,64,64)
lightGray = Color(192,192,192)
yellow = Color(255,255,0)
orange = Color(255,200,0)
pink = Color(255,175,175)
magenta = Color(255,0,255)
cyan = Color(0,255,255)


##
## Global picture functions
##
def makePicture(filename):
    picture = Picture()
    picture.loadImage(filename)
    try:
        # ??? w = picture.getWidth()
        return picture
    except:
        print "Was unable to load the image in " + filename +"\nMake sure it's a valid image file." 

def makeEmptyPicture(width, height):
    picture = Picture()
    picture.createImage(width, height)
    return picture
    
def getPixels(picture):
    if not picture.__class__ == Picture:
        print "getPixels(picture): Input is not a picture"
        raise ValueError 
    return picture.getPixels()

def getWidth(picture):
    if not picture.__class__ == Picture:
        print "getWidth(picture): Input is not a picture"
        raise ValueError 
    return picture.getWidth()

def getHeight(picture):
    if not picture.__class__ == Picture:
        print "getHeight(picture): Input is not a picture"
        raise ValueError 
    return picture.getHeight()

def show(picture, title=None):
    if not picture.__class__ == Picture:
        print "show(picture): Input is not a picture"
        raise ValueError 
    picture.show()

def repaint(picture):
    if not picture.__class__ == Picture:
        print "repaint(picture): Input is not a picture"
        raise ValueError 
    picture.repaint()

def addLine(picture,x1,y1,x2,y2):
    if not picture.__class__ == Picture:
        print "addLine(picture,x1,y1,x2,y2): Input is not a picture"
        raise ValueError 
    picture.addLine(black,x1,y1,x2,y2)

def addText(picture,x1,y1,string):
    if not picture.__class__ == Picture:
        print "addText(picture,x1,y1,string): Input is not a picture"
        raise ValueError 
    picture.addText(black,x1,y1,string)

def addRect(picture,x,y,w,h):
    if not picture.__class__ == Picture:
        print "addRect(picture,x,y,w,h): Input is not a picture"
        raise ValueError 
    picture.addRect(black,x,y,w,h)

def addRectFilled(picture,x,y,w,h,acolor):
    if not picture.__class__ == Picture:
        print "addRectFilled(picture,x,y,w,h,acolor): Input is not a picture"
        raise ValueError 
    picture.addRectFilled(acolor,x,y,w,h)

def addOval(picture,x,y,w,h):
    if not picture.__class__ == Picture:
        print "addOval(picture,x,y,w,h): Input is not a picture"
        raise ValueError 
    picture.addOval(black,x,y,w,h)

def addOvalFilled(picture,x,y,w,h,acolor):
    if not picture.__class__ == Picture:
        print "addOvalFilled(picture,x,y,w,h,acolor): Input is not a picture"
        raise ValueError 
    picture.addOvalFilled(acolor,x,y,w,h)

def getPixel(picture,x,y):
    if not picture.__class__ == Picture:
        print "getPixel(picture,x,y): Input is not a picture"
        raise ValueError 
    return picture.getPixel(x,y)
    
def setRed(pixel,value):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "setRed(pixel,value): Input is not a pixel or a color"
        raise ValueError 
    pixel.setRed(value)

def getRed(pixel):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "getRed(pixel): Input is not a pixel or a color"
        raise ValueError 
    return pixel.getRed()

def setBlue(pixel,value):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "setBlue(pixel,value): Input is not a pixel or a color"
        raise ValueError 
    pixel.setBlue(value)

def getBlue(pixel):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "getBlue(pixel): Input is not a pixel or a color"
        raise ValueError 
    return pixel.getBlue()

def setGreen(pixel,value):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "setGreen(pixel,value): Input is not a pixel or a color"
        raise ValueError 
    pixel.setGreen(value)

def getGreen(pixel):
    if not (pixel.__class__ == Pixel or pixel.__class__ == Color):
        print "getGreen(pixel): Input is not a pixel or a color"
        raise ValueError 
    return pixel.getGreen()

def getColor(pixel):
    if not pixel.__class__ == Pixel:
        print "getColor(pixel): Input is not a pixel"
        raise ValueError 
    return pixel.getColor()

def getColorXY(pic, x, y):
    return pic.getColorXY(x, y)

def setColorXY(pic, x, y, color):
    pic.setColorXY(x, y, color)

def setColor(pixel,color):
    if not pixel.__class__ == Pixel:
        print "setColor(pixel,color): Input is not a pixel."
        raise ValueError 
    if not color.__class__ == Color:
        print "setColor(pixel,color): Input is not a color."
        raise ValueError 
    pixel.setColor(color)
    
def getX(pixel):
    if not pixel.__class__ == Pixel:
        print "getX(pixel): Input is not a pixel"
        raise ValueError 
    return pixel.getX()

def getY(pixel):
    if not pixel.__class__ == Pixel:
        print "getY(pixel): Input is not a pixel"
        raise ValueError 
    return pixel.getY()

def distance(c1,c2):
    if not c1.__class__ == Color:
        print "distance(c1,c2): First input is not a color."
        raise ValueError 
    if not c2.__class__ == Color:
        print "distance(c1,c2): Second input is not a color."
        raise ValueError 
    return c1.distance(c2)

def writePictureTo(pict,filename):
    if not pict.__class__ == Picture:
        print "writePictureTo(pict,filename): Input is not a picture"
        raise ValueError
    pict.writeTo(filename)
    #if not os.path.exists(filename):
    #   print "writePictureTo(pict,filename): Path is not valid"
    #   raise ValueError

def makeDarker(color):
    if not color.__class__ == Color:
        print "makeDarker(color): Input is not a color."
        raise ValueError 
    color.makeDarker()
    # return color

def makeLighter(color):
    if not color.__class__ == Color:
        print "makeLighter(color): Input is not a color."
        raise ValueError 
    color.makeLighter()
    # return color

def rgbString(color):
    if not color.__class__ == Color:
        print "rgbString(color): Input is not a color."
        raise ValueError 
    return color.rgbString()

def makeColor(red,green,blue):
    return Color(red,green,blue)

def newColor(red,green,bllue):
    return Color(red,green,blue)

def quit():
    sys.exit(0)
        
def getFileName(pict):
    return pict.getFileName()

def getDirectory(pict):
    return pict.getDirectory()



##
## The Sound Stuff
##

#
# Sound
#
class Sound:
    def __init__(self,filename=None):
        global mediaFolder
        try:    
            self.m = pygame.mixer
            #self.m.init(22050, -16, False)
        except:
            print "Unable to initialize sound system."
            return

        tmp = pygame.sndarray

        if (filename == None):
            self.s = tmp.make_sound( Numeric.array([0]) )
        else:
            if not os.path.isabs(filename):
                filename = mediaFolder + filename
            self.filename = filename
            try:
                self.s = self.m.Sound(filename)
            except:
                print "Unable to open file."
            self.a = tmp.samples(self.s)
            self.alen = len(self.a)
                
                    
    def __str__(self):
        return "Sound of length "+str(self.getLength())
        
    def __rep__(self):
        return "Sound of length "+str(self.getLength())

        def __class__(self):
                return Sound

    def makeEmptyLength(self,size):
        tmp = pygame.sndarray
        self.s = tmp.make_sound( Numeric.zeros( size ) )  # .nah. sec * 22050 ) )
        self.a = tmp.samples(self.s)
        self.alen = len(self.a)

        
    def play(self):
        try:
            self.s.play()
        except:
            print "Trouble accessing the sound device."
            
        def playInRange(self,start,stop):
            try:
                if start > 0 and stop <= self.getLength() and start < stop:
                    tmp = pygame.sndarray
                    tmpsnd = tmp.make_sound( self.a[start-1:stop-1] )
                    tmpsnd.play()
                else:
                    print "invalid range in PlayInRange()."
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                print exc_type
                print exc_value
                print traceback.extract_tb(exc_tb)
                print "Trouble accessing the sound device."     


    def blockingPlay(self):
      try:
         chan = self.s.play()
         while chan.get_busy(): #still playing
            pygame.time.wait(10)        
      except:
         print "Trouble accessing the sound device."


    def blockingPlayInRange(self,start,stop):
       try:
          if start > 0 and stop <= self.getLength() and start < stop:
              tmp = pygame.sndarray
              tmpsnd = tmp.make_sound( self.a[start-1:stop-1] )
              chan = tmpsnd.play()
              while chan.get_busy(): #still playing
                  time.wait(10)       
          else:
              print "invalid range in blockingPlayInRange()."
       except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            print exc_type
            print exc_value
            print traceback.extract_tb(exc_tb)
            print "Trouble accessing the sound device."

    def getSamples(self):
        return Samples(self)
    
    def getLength(self):
        return self.alen
    
    def getSampleValue(self,index):
                if index > 0 and index <= self.alen:
                        # .nah. optimization -- not calling getLength() in if
                   return int(self.a[index-1])
                else:
                        print "invalid index in getSampleValue()."
                        return 0

    def getFileName(self):
        return self.filename

    def getDirectory(self):
        return self.filename[ : self.filename.rfind(os.sep) + 1]
        
    def setSampleValue(self,index,value):
                if index > 0 and index <= self.alen:
                        # .nah. optimization -- not calling getLength() in if
                        self.a[index-1] = max( min(int(value), 32767), -32768 )
                else:
                        print "invalid index in setSampleValue()."

    def getSamplingRate(self):
        return 22050
        
    def getSampleObjectAt(self,index):
                if index > 0 and index <= self.alen:
                        # .nah. optimization -- not calling getLength() in if
                   return Sample(self,index)
                else:
                        print "invalid index in getSampleObjectAt()."
    
    def writeTo(self,filename):
                global mediaFolder
                if not os.path.isabs(filename):
                    filename = mediaFolder + filename
                try:
                        binfile = open(filename, 'wb')
                except:
                        print "Unable to create file."
                        return

                self.filename = filename

                # RIFF header
                binfile.write( struct.pack( '<4s', "RIFF" ) )
                binfile.write( struct.pack( '<l', self.getLength()+36) )
                binfile.write( struct.pack( '<4s', "WAVE" ) )

                # WAVE format chunk
                binfile.write( struct.pack( '<4s', "fmt " ) )
                binfile.write( struct.pack( '<l', 16 ) )
                binfile.write( struct.pack( '<h', 1 ) )
                binfile.write( struct.pack( '<h', 1 ) )
                binfile.write( struct.pack( '<l', self.getSamplingRate() ) )
                binfile.write( struct.pack( '<l', self.getSamplingRate()*2) )
                binfile.write( struct.pack( '<h', 2 ) )
                binfile.write( struct.pack( '<h', 16 ) )

                # WAVE data chunk
                binfile.write( struct.pack( '<4s', "data" ) )
                binfile.write( struct.pack( '<l', self.getLength()*2 ) )
                for ii in xrange(self.getLength()):
                        data = struct.pack('<h', self.a[ii])
                        binfile.write(data)
                binfile.close()





class Samples:
    def __init__(self,aSound):
        #self.myList = []
        self.sound = aSound
        self.cur = 0
        self.len = self.sound.getLength()
        #for s in xrange(1,aSound.getLength()+1):
        #   self.myList.append(Sample(aSound,s))

        def __iter__(self):
                return self

        def next(self):
                if self.cur >= self.len:
                        raise StopIteration
                self.cur = self.cur + 1
                return Sample(self.sound, self.cur)
    
    def __str__(self):
        return "Samples, length "+str(self.sound.getLength())
    
    def __rep__(self):
        return "Samples, length "+str(self.sound.getLength())
    
    # .nah. Are these really needed?
    def __getitem__(self,item):
                return self.sound.getSampleValue(item)
        #return self.myList[item]
    
    def __setitem__(self,item,value):
        self.sound.setSampleValue(item,value)
    
    def getSound(self):
        return self.sound
    
        
class Sample:
    def __init__(self,aSound,index):
        self.sound=aSound
        self.index=index

    def __str__(self):
        return "Sample at "+str(self.index)+" value at "+str(self.getValue())

    def __rep__(self):
        return "Sample at "+str(self.index)+" value at "+str(self.getValue())
    
    def setValue(self,value):
        self.sound.setSampleValue(self.index,int(round(value)))
    
    def getValue(self):
        return self.sound.getSampleValue(self.index)
        
    def getSound(self):
        return self.sound



##      
## Global sound functions
##
def makeSound(filename):
    global mediaFolder
    if not os.path.isabs(filename):
            filename = mediaFolder + filename
    if not os.path.isfile(filename):
        print "There is no file at "+filename
        raise ValueError 
    return Sound(filename)

def makeEmptySound(size):
    snd = Sound()
    snd.makeEmptyLength(size)
    return snd

def getSamples(sound):
    if not sound.__class__ == Sound:
        print "getSamples(sound): Input is not a sound."
        raise ValueError 
    return Samples(sound)

def play(sound):
    if not sound.__class__ == Sound:
        print "play(sound): Input is not a sound."
        raise ValueError 
    sound.play()

def blockingPlay(sound):
    if not sound.__class__ == Sound:
        print "blockingPlay(sound): Input is not a sound."
        raise ValueError 
    sound.blockingPlay()


#20June03 new functionality in JavaSound (ellie)
def playInRange(sound,start,stop):
        if not sound.__class__ == Sound:
                print "playInRange(sound,start,stop):  Input is not a sound."
                raise ValueError
        sound.playInRange(start,stop)

#20June03 new functionality in JavaSound (ellie)
def blockingPlayInRange(sound,start,stop):
        if not sound.__class__ == Sound:
                print "blockingPlayInRange(sound,start,stop): Input is not a sound."
                raise ValueError
        sound.blockingPlayInRange(start,stop)
    
def getSamplingRate(sound):
    if not sound.__class__ == Sound:
        print "getSamplingRate(sound): Input is not a sound."
        raise ValueError 
    return sound.getSamplingRate()

def setSampleValueAt(sound,index,value):
    if not sound.__class__ == Sound:
        print "setSampleValueAt(sound,index,value): Input is not a sound."
        raise ValueError 
    sound.setSampleValue(index,value)

def getSampleValueAt(sound,index):
    if not sound.__class__ == Sound:
        print "getSampleValueAt(sound,index): Input is not a sound."
        raise ValueError 
    return sound.getSampleValue(index)

def getSampleObjectAt(sound,index):
    if not sound.__class__ == Sound:
        print "getSampleObjectAt(sound,index): Input is not a sound."
        raise ValueError 
    return sound.getSampleObjectAt(index)

def setSample(sample,value):
    if not sample.__class__ == Sample:
        print "setSample(sample,value): Input is not a sample."
        raise ValueError 
    # Need to coerce value to integer
    return sample.setValue(value)

def getSample(sample):
    if not sample.__class__ == Sample:
        print "getSample(sample): Input is not a sample."
        raise ValueError 
    return sample.getValue()

def getSound(sample):
    if not sample.__class__ == Sample:
        print "getSound(sample): Input is not a sample."
        raise ValueError 
    return sample.getSound()

def getLength(sound):
    if not sound.__class__ == Sound:
        print "getLength(sound): Input is not a sound."
        raise ValueError 
    return sound.getLength()


def writeSoundTo(sound,filename):
    global mediaFolder
    if not os.path.isabs(filename):
            filename = mediaFolder + filename
    if not sound.__class__ == Sound:
        print "writeSoundTo(sound,filename): Input is not a sound."
        raise ValueError 
    sound.writeTo(filename)
    
