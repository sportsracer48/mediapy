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
# 14 Jul 2015:
#    Changed sound to use pyaudio, to allow variable framerates
#    Added several missing functions from canon media.py
# 28 Jul 2015: removed John Zelle's graphics library, because it was preventing
#    the creation of new windows.
#    added sound explorer.
#    added picture explorer.
#    added arcs and other msic missing functions.
#    added playNote, but don't count on it working well
#    added dialogue boxes
#    reverted 1 based indexing


import user
import numpy
import struct
import sndhdr
import wave
import aifc
import sunau
import threading
import random
import ttk
import os
import sys
from math import sqrt,cos,radians,sin
from PIL import ImageDraw, ImageTk, ImageFont, Image as Im
import tkFileDialog
import tkColorChooser
import copy
import math
import pyaudio
import tkMessageBox
#Fredrik Lundh's dialog box helper class
from tkSimpleDialog import Dialog
import Tkinter
#Martin C. Doege's audio synthesis library
#with slight modification by Henry Rachootin
import synth.pysynth_b as pysynth
import turtle as tur

pyAudio = pyaudio.PyAudio() #should never change
tk = Tkinter #alias
noteList=['a', 'a#', 'b', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#'] #should never change, used to interface with pysynth

ver = "1.7"

#TODO: there are TWO global, non-constant variables in this module.
#root, colorWrapAround
#these belong somewhere else
root = None
colorWrapAround = True

true = 1
false = 0

italic = "italic"
bold = "bold"
plain = "plain"

dirPath = os.path.dirname(__file__)
mono = os.path.join(dirPath,"..","monospace")
serif = os.path.join(dirPath,"..","serif")
sansSerif = os.path.join(dirPath,"..","sans-serif")

#Name nine types of public domain fonts I found on the internet
fontTable = {mono:{italic:os.path.join(mono,"Hack-Oblique.ttf"),
                   bold:os.path.join(mono,"Hack-Bold.ttf"),
                   plain:os.path.join(mono,"Hack-Regular.ttf")},
             serif:{italic:os.path.join(serif,"OldStandard-Italic.ttf"),
                   bold:os.path.join(serif,"OldStandard-Bold.ttf"),
                   plain:os.path.join(serif,"OldStandard-Regular.ttf")},
             sansSerif:{italic:os.path.join(sansSerif,"Arimo-Italic.ttf"),
                   bold:os.path.join(sansSerif,"Arimo-Bold.ttf"),
                   plain:os.path.join(sansSerif,"Arimo-Regular.ttf")}}


defaultFont = ImageFont.truetype(fontTable[serif][plain], 24)

mediaFolder = user.home + os.sep



# print "Media Computation Library. Version " + str(ver)
# print "Started by Mark Guzdial"
# print "Updated by Nadeem Abdul Hamid, June 14 2007"
# print "Updated by Henry Rachootin July 14 2015"

def tkGet(callback,*args,**kvargs):
    """
    Executes <callback> in the tkinter thread, and waits for it to complete
    before returning the return value of <callback>. If <callback> calls tkGet or tkDo, this
    function will deadlock.
    """
    returnHolder = [None]
    #condition will be used to alert this thread that tkinter is done executing the callback
    condition = threading.Condition()
    
    def helper():
        returnHolder[0]=callback(*args,**kvargs)
        condition.acquire()
        condition.notifyAll()
        condition.release()
    
    condition.acquire()
    root.after(0,helper)
    condition.wait()
    condition.release()
    
    return returnHolder[0]

def tkDo(callback,*args,**kvargs):
    """
    Executes <callback> in the tkinter thread, eventually. Don't really count on
    this being completed too soon. If <callback> calls tkGet or tkDo, this
    function will deadlock.
    """
    root.after(0,callback,*args,**kvargs)
    

def setRoot(newRoot):
    global root
    root = newRoot

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
    
def setTestMediaFolder():
    global mediaFolder
    mediaFolder = os.getcwd() + os.sep
    
def showMediaFolder():
    global mediaFolder
    print "The media path is currently: ", mediaFolder
    
def getMediaPath(filename):
    global mediaFolder
    filePath = mediaFolder+filename
    if not os.path.isfile(filePath):
        print "Note: There is no file at "+filePath
    return filePath
    
def pickAFile():
    path = tkGet(tkFileDialog.askopenfilename)
    return path
    
def pickASaveFile():
    path = tkGet(tkFileDialog.asksaveasfilename)
    return path
    
def pickAFolder():
    global mediaFolder
    folder = tkFileDialog.askdirectory()
    if folder == '':
        folder = mediaFolder
    else:
        folder = folder + os.sep
    return folder

def showInformation(message):
    tkGet(tkMessageBox.showinfo,"",message)
    
def showWarning(message):
    tkGet(tkMessageBox.showwarning,"",message)
    
def showError(message):
    tkGet(tkMessageBox.showerror,"",message)
    
##
## Request Classes
##

class RequestDialog(Dialog):
    def __init__(self, parent, message, valHolder):
        self.message = message
        self.valHolder = valHolder
        Dialog.__init__(self, parent, title="")
    
    def body(self, master):

        ttk.Label(master, text=self.message).grid(row=0,sticky=tk.W)

        self.e1 = ttk.Entry(master)
        self.e1.grid(row=1, column=0,sticky=tk.W+tk.E)
        return self.e1 # initial focus

    def apply(self):
        self.valHolder[0] = self.e1.get()
        
def requestString(message):
    valHolder = [None]
    tkGet(RequestDialog,root,message,valHolder)
    return valHolder[0]

def requestNumber(message):
    valHolder = [None]
    while True:
        tkGet(RequestDialog,root,message,valHolder)
        try:
            return float(valHolder[0])
        except:
            if valHolder[0] is None:
                return None
            message = "Try again. that wasn't a number!"
            valHolder = [None]
        
def requestInteger(message):
    valHolder = [None]
    while True:
        tkGet(RequestDialog,root,message,valHolder)
        try:
            return int(valHolder[0])
        except:
            if valHolder[0] is None:
                return None
            message = "Try again. that wasn't an integer!"
            valHolder = [None]
            
def requestIntegerInRange(message,minVal,maxVal):
    valHolder = [None]
    while True:
        tkGet(RequestDialog,root,message,valHolder)
        try:
            candidate = int(valHolder[0])
            if candidate>=minVal and candidate<=maxVal:
                return candidate
        except:
            pass
        if valHolder[0] is None:
            return None
        message = "Try again. that wasn't an between {} and {}!".format(minVal,maxVal)
        valHolder = [None]
        


def addLibPath(directory=None):
    if directory is None:
        directory = pickAFolder()

    if os.path.isdir(directory):
        sys.path.insert(0, directory)
    elif directory is not None:
        raise ValueError("There is no directory at " + directory)

    return directory

setLibPath = addLibPath

def printNow(text):
    print text
    
def pickAColor():
    color = tkGet(tkColorChooser.askcolor)
    if color[0] is None:
        return black
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
    filePath = mediaFolder+filename
    if not os.path.isfile(filePath) or not os.path.isdir(filePath):
        print "Note: There is no file at "+filePath
    return filePath
    
def getShortPath(filename):
    dirs = filename.split(os.sep)
    if len(dirs) < 1:
        return "."
    elif len(dirs) == 1:
        return dirs[0]
    else:
        return (dirs[len(dirs) - 2] + os.sep + dirs[len(dirs) - 1])



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

    def createImage(self, width, height, acolor):
        self.image = Im.new("RGB", (width, height), color = acolor.getRGB())
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
    
    def _repaint_tkCallback(self):
        self.dispImage = ImageTk.PhotoImage(self.getImage())
        #necessary due to garbage collection
        self.canvas.img = self.dispImage
        self.item = self.canvas.create_image(0, 0, image=self.dispImage, anchor='nw')
    
    def repaint(self):
        if self.winActive:
            tkGet(self._repaint_tkCallback)
        else:
            self.show()

    
    def _show_tkCallback(self):
        self.frame = tk.Toplevel(root)
        if self.filename is not None and self.filename != '':
            self.frame.title(self.filename)
        else:
            self.frame.title("Jes Picture")
        self.canvas = tk.Canvas(self.frame, width=self.getWidth(), height=self.getHeight())            
        self.dispImage = ImageTk.PhotoImage(self.getImage())
        
        #necessary due to garbage collection. If the main thread
        #closes, then the Picture is lost, unless it is added to the
        #canvas.
        self.canvas.img = self.dispImage
        
        
        self.item = self.canvas.create_image(0, 0, image=self.dispImage, anchor='nw')
        self.canvas.pack()
        
    
    def show(self):
        if not self.winActive:
            #this needs to be here, or subsequent calls to repaint will open a new window
            #rather than queuing a repaint for the current one. As long as winActive
            #is 1, show will never be called.
            self.winActive = 1
            tkGet(self._show_tkCallback)
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

    # color should be a 3-tuple
    def setColorXY(self, x, y, color):
        self.pixels[x, y] = color

    # returns a 3-tuple
    def getColorXY(self, x, y):
        return self.pixels[x, y]

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
        d.pieslice( [ (x, y), (x+w, y+h) ], start-90, start+angle-90,
               outline=acolor.getRGB(), fill=acolor.getRGB() )
    
    def addArc(self, acolor,x,y,w,h,start,angle):
        d = ImageDraw.Draw(self.image)
        d.arc( [ (x, y), (x+w, y+h) ], start-90, start+angle-90,fill=acolor.getRGB() )
        
    def addLine(self, acolor, x1, y1, x2, y2):
        d = ImageDraw.Draw(self.image)
        d.line( [ (x1, y1), (x2, y2) ], fill=acolor.getRGB() )

    def addText(self, acolor, x, y, string, style):
        d = ImageDraw.Draw(self.image)
        d.text( (x, y), string, font=style, fill=acolor.getRGB())
        
    def drawPicture(self,picture,x,y):
        self.image.paste(picture.image,(x,y))


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
        self.x = x
        self.y = y
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
        return self.x
        
    def getY(self):
        return self.y

        
class Color:
    def __init__(self,r,g,b):
        r,g,b = int(r),int(g),int(b)
        if(colorWrapAround):
            r,g,b = r%256,g%256,b%256
        else:
            r,g,b = max(r,0),max(g,0),max(b,0)
            r,g,b = min(r,255),min(g,255),min(b,255)
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
    
    def getRGBString(self):
        return '#%02x%02x%02x' % (self.r,self.g,self.b)
    
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
        r = (255 - self.r) * .35 + self.r
        g = (255 - self.g) * .35 + self.g
        b = (255 - self.b) * .35 + self.b
        return Color(r,g,b)
    
    def makeDarker(self):
        r = self.r * .65
        g = self.g * .65
        b = self.b * .65
        return Color(r,g,b)
        

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

def makeEmptyPicture(width, height, acolor=white):
    picture = Picture()
    picture.createImage(width, height,acolor)
    return picture
    
def getPixels(picture):
    if not picture.__class__ == Picture:
        print "getPixels(picture): Input is not a picture"
        raise ValueError 
    return picture.getPixels()

def getPixelAt(picture,x,y):
    if not picture.__class__ == Picture:
        print "getPixelAt(picture,x,y): Input is not a picture"
        raise ValueError 
    return picture.getPixel(x,y)

def getAllPixels(picture):
    return getPixels(picture)

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

def addLine(picture,x1,y1,x2,y2,acolor=black):
    if not picture.__class__ == Picture:
        print "addLine(picture,x1,y1,x2,y2): Input is not a picture"
        raise ValueError 
    picture.addLine(acolor,x1,y1,x2,y2)

def makeStyle(fontName,emph,size):
    if fontName in fontTable:
        return ImageFont.truetype(fontTable[fontName][emph],size)
    #As far as I'm concerned it is impossible to say which index is
    #italic or bold, so I'm always going with the default.
    return ImageFont.truetype(fontName,size)

def addText(picture,x1,y1,string,acolor=black):
    if not picture.__class__ == Picture:
        print "addText(picture,x1,y1,string): Input is not a picture"
        raise ValueError 
    picture.addText(acolor,x1,y1,string,defaultFont)
    
def addTextWithStyle(picture, x, y, string, style, acolor=black):
    if not picture.__class__ == Picture:
        print "addText(picture,x,y,string,style,[acolor]): Input is not a picture"
        raise ValueError
    picture.addText(acolor,x,y,string,style)

def addRect(picture,x,y,w,h,acolor=black):
    if not picture.__class__ == Picture:
        print "addRect(picture,x,y,w,h): Input is not a picture"
        raise ValueError 
    picture.addRect(acolor,x,y,w,h)
    
def setAllPixelsToAColor(picture,color):
    if not picture.__class__ == Picture:
        print "setAllPixelsToAColor(picture,color): Input is not a picture"
        raise ValueError
    addRectFilled(picture, 0, 0, picture.getWidth(), picture.getHeight(), color)

def addRectFilled(picture,x,y,w,h,acolor=black):
    if not picture.__class__ == Picture:
        print "addRectFilled(picture,x,y,w,h,acolor): Input is not a picture"
        raise ValueError 
    picture.addRectFilled(acolor,x,y,w,h)
    
def addArc(picture,x,y,w,h,start,angle,acolor = black):
    if not picture.__class__ == Picture:
        print "addArc(picture,x,y,w,h,start,angle,[acolor]): Input is not a picture"
        raise ValueError 
    picture.addArc(acolor,x,y,w,h,start,angle)
    
def addArcFilled(picture,x,y,w,h,start,angle,acolor = black):
    if not picture.__class__ == Picture:
        print "addArcFilled(picture,x,y,w,h,start,angle,[acolor]): Input is not a picture"
        raise ValueError 
    picture.addArcFilled(acolor,x,y,w,h,start,angle)

def addOval(picture,x,y,w,h,acolor=black):
    if not picture.__class__ == Picture:
        print "addOval(picture,x,y,w,h): Input is not a picture"
        raise ValueError 
    picture.addOval(acolor,x,y,w,h)

def addOvalFilled(picture,x,y,w,h,acolor=black):
    if not picture.__class__ == Picture:
        print "addOvalFilled(picture,x,y,w,h,acolor): Input is not a picture"
        raise ValueError 
    picture.addOvalFilled(acolor,x,y,w,h)
    
def copyInto(smallPicture,bigPicture,startX,startY):
    if not smallPicture.__class__ == Picture:
        print "copyInto(smallPicture,bigPicture,startX,startY): First input is not a picture"
        raise ValueError 
    if not bigPicture.__class__ == Picture:
        print "copyInto(smallPicture,bigPicture,startX,startY): Second input is not a picture"
        raise ValueError 
    bigPicture.drawPicture(smallPicture,startX,startY)
    
def duplicatePicture(picture):
    if not picture.__class__ == Picture:
        print "duplicatePicture(picture): Input is not a picture"
        raise ValueError
    newPic = makeEmptyPicture(picture.getWidth(), picture.getHeight())
    newPic.drawPicture(picture, 0, 0)
    return newPic
    

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
    return color.makeDarker()

def makeLighter(color):
    if not color.__class__ == Color:
        print "makeLighter(color): Input is not a color."
        raise ValueError 
    return color.makeLighter()
    
makeBrighter = makeLighter

def setColorWrapAround(setting):
    global colorWrapAround
    colorWrapAround = setting

def getColorWrapAround():
    return colorWrapAround

def makeColor(red,green,blue):
    return Color(red,green,blue)

def _setColorTo(color,other):
    color.setRGB((other.r,other.g,other.b))

def newColor(red,green,blue):
    return Color(red,green,blue)
        
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
    
    @staticmethod
    def getNumpyType(byteWidth):
        if byteWidth<=2:
            return numpy.int8
        if byteWidth<=4:
            return numpy.int16
        if byteWidth<=8:
            return numpy.int32
        if byteWidth<=16:
            return numpy.int64
        return None
    @staticmethod
    def getFormatString(byteWidth):
        if byteWidth<=1:
            return 'b'
        if byteWidth<=2:
            return 'h'
        if byteWidth<=4:
            return 'i'
        if byteWidth<=8:
            return 'l'
        return None
    
    def __init__(self,filename=None):
        global mediaFolder
        global pyAudio
        self.soundFile = None
        self.CHUNK = 1024
        
        self.playing = False
        self.filename = filename
        
        soundTypeDict = {'wav':wave, 'aiff':aifc, 'au':sunau}
        
        
        if(filename is not None):
            
            if(not os.path.isabs(filename)):
                filename = getMediaPath(filename)
            
            self.soundType = sndhdr.what(filename)[0]
            
            if(self.soundType not in soundTypeDict):
                print filename + " is not a supported format (wav, aiff, au)"
                raise ValueError
            
            internalSoundType = soundTypeDict[self.soundType]
            
            self.soundFile = internalSoundType.open(filename,'r')
            
            
            self.sampwidth = self.soundFile.getsampwidth()
            self.rawchannels = self.soundFile.getnchannels()
            self.nchannels = self.rawchannels
            #the use of samplerate is wrong. It should read framerate, but
            #I really don't want to change it.
            self.samplerate = self.soundFile.getframerate()
            
            data = self.soundFile.readframes(self.soundFile.getnframes())
            
            
            
            dtype = Sound.getNumpyType(self.soundFile.getsampwidth())
            
            self.a = numpy.fromstring(data, dtype = dtype)
            
            
            
            #aiff files are big endian, and pyaudio is little endian. 
            #To accommodate for this, we must reverse the bytes in each window
            if self.rawchannels>1 and self.soundType == 'aiff':
                for i in range(self.rawchannels/2):
                    temp = self.a[i::self.rawchannels].copy()
                    self.a[i::self.rawchannels] = self.a[self.rawchannels-i-1::self.rawchannels]
                    self.a[self.rawchannels-i-1::self.rawchannels] = temp
            
            self.alen = self.a.size
            self.nsamples = self.alen/self.sampwidth
            self.nframes = self.nsamples/self.nchannels
            self.soundFile.close()
                    
    def __str__(self):
        return "Sound of length "+str(self.nframes)
        
    def __rep__(self):
        return "Sound of length "+str(self.nframes)

    def __class__(self):
        return Sound
    
    def makeEmptyLength(self,numSamples, samplingRate = 22050):
        self.a = numpy.zeros([numSamples*2],dtype = numpy.int8)
        self.alen = self.a.size
        self.soundType = 'wav'
        self.sampwidth = 2
        self.samplerate = samplingRate
        self.nchannels = 1
        self.nsamples = self.alen/self.sampwidth
        self.nframes = self.nsamples/self.nchannels
        
    def stopPlaying(self):
        self.playing=False    
            
    def play(self):
        self.playing = True
        playThread = threading.Thread(target = self.blockingPlay)
        playThread.start()
            
    def playInRange(self,start,stop,callback = None):
        self.playing = True
        playThread = threading.Thread(target = self.blockingPlayInRange, args = (start,stop))
        playThread.start()
        
        

    def blockingPlay(self):
        self.playing = True
        self.blockingPlayInRange(0,self.a.size)
    
    def createStream(self):
        global pyAudio
        return pyAudio.open(format = pyAudio.get_format_from_width(self.sampwidth),
                                       channels = self.nchannels,
                                       rate = self.samplerate,
                                       output = True)

    def blockingPlayInRange(self,start,stop):
        self.playing=True
        stream = self.createStream()
        self.blockingPlayWithStreamInRange(stream,start,stop)
        
        
    def blockingPlayWithStreamInRange(self,stream,start,stop):
        if start<0:
            start = 0
        start = start*self.sampwidth*self.nchannels
        stop = stop*self.sampwidth*self.nchannels
        pointer = start
        remaining = stop - pointer
        toRead = 0
        if(remaining>self.CHUNK):
            toRead = self.CHUNK
        else:
            toRead = remaining
            
        data = self.a[pointer:pointer+toRead]
        read = toRead
        while pointer < stop and self.playing:
            stream.write(data)
            pointer += read
            remaining = stop - pointer
            if(remaining>self.CHUNK):
                toRead = self.CHUNK
            else:
                toRead = remaining
            data = self.a[pointer:pointer+toRead]
            read = toRead
            
        stream.stop_stream()
        stream.close()
    
    def blockingPlayAtRateInRange(self, rate, start, stop):
        self.playing=True
        global pyAudio
        stream = pyAudio.open(format = pyAudio.get_format_from_width(self.sampwidth),
                                       channels = self.nchannels,
                                       rate = int(rate*self.samplerate),
                                       output = True)
        self.blockingPlayWithStreamInRange(stream,start,stop)
        
    def playAtRateInRange(self, rate, start, stop):
        self.playing = True
        playThread = threading.Thread(target = self.blockingPlayAtRateInRange, args = (rate,start,stop))
        playThread.start()
        

    def getSamples(self):
        return Samples(self)
    
    def getLength(self):
        return self.alen
    
    def getSampleValue(self,index):
                if index >= 0 and index < self.nsamples:
                    return struct.unpack(
                                         Sound.getFormatString(self.sampwidth),
                                         self.a[index*self.sampwidth:index*self.sampwidth+self.sampwidth]
                                        )[0]
                else:
                        print "invalid index in getSampleValue()."
                        return 0

    def getFileName(self):
        return self.filename

    def getDirectory(self):
        return self.filename[ : self.filename.rfind(os.sep) + 1]
    
    def getChannel(self,index):
        return [self.getSampleValue(i) for i in range(index,self.nsamples,self.nchannels)]
    
    def setSampleValue(self,index,value):
        if index >= 0 and index < self.nsamples:
                bytesList = struct.pack(Sound.getFormatString(self.sampwidth),value)
                self.a[index*self.sampwidth:index*self.sampwidth+self.sampwidth] = numpy.frombuffer(bytesList, dtype = numpy.int8)
        else:
                print "invalid index in setSampleValue()."
                        
    def getChannelSampleValue(self,index,channel):
        if index >= 0 and index < self.nframes and channel>=0 and channel < self.nchannels:
            return self.getSampleValue(index*self.nchannels+channel)
        else:
            print "invalid index or channel in getChannelSampleValue"

    def getSamplingRate(self):
        return self.samplerate
        
    def getSampleObjectAt(self,index):
        if index >= 0 and index < self.nsamples:
            # .nah. optimization -- not calling getLength() in if
            return Sample(self,index)
        else:
            print "invalid index in getSampleObjectAt()."
    
    def writeTo(self,filename):
        global mediaFolder
        if not os.path.isabs(filename):
            filename = mediaFolder + filename
        try:
                wavFile = wave.open(filename, 'w')
        except:
                print "Unable to create file."
                return

        self.filename = filename

        wavFile.setnchannels(self.nchannels)
        wavFile.setsampwidth(self.sampwidth)
        wavFile.setframerate(self.samplerate)
        wavFile.setnframes(self.nframes)
        wavFile.writeframes(self.a)
        wavFile.close()





class Samples:
    def __init__(self,aSound):
        #self.myList = []
        self.sound = aSound
        self.cur = 0
        self.len = self.sound.nsamples
        #for s in xrange(1,aSound.getLength()+1):
        #   self.myList.append(Sample(aSound,s))

    def __iter__(self):
            return self

    def next(self):
            if self.cur >= self.len:
                raise StopIteration
            toReturn = Sample(self.sound, self.cur)
            self.cur = self.cur + 1
            return toReturn
    
    def __str__(self):
        return "Samples, length "+str(self.sound.nframes)
    
    def __rep__(self):
        return "Samples, length "+str(self.sound.nframes)
    
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

def makeEmptySound(size, sampleRate = 22050):
    snd = Sound()
    snd.makeEmptyLength(size, sampleRate)
    return snd

def makeEmptySoundBySeconds(seconds, samplingRate = 22050):
    snd = Sound()
    snd.makeEmptyLength(seconds*samplingRate, samplingRate)
    return snd

def duplicateSound(sound):
    if not sound.__class__ == Sound:
        print "duplicateSound(sound): Input is not a sound."
        raise ValueError
    copySound = copy.copy(sound)
    copySound.a = numpy.copy(sound.a)
    return copySound

def getSamples(sound):
    if not sound.__class__ == Sound:
        print "getSamples(sound): Input is not a sound."
        raise ValueError 
    return Samples(sound)

def stopPlaying(sound):
    if not sound.__class__ == Sound:
        print "stopPlaying(sound): Input is not a sound."
        raise ValueError
    sound.stopPlaying()

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

#using pysynth, I have attempted to approximate the midi functionality of JES,
#without midi. This has a smaller range of notes it can play (only those found on a piano)
#but it works without any external libraries needing to be installed.
#It has a noticeable delay before the sound starts to play. C'est la vei.
#It also cannot play anything for more than three seconds or so.
#Generally this is the worst function here, but it's better than nothing.
#TODO: rewrite playNote to be good instead of bad.
def playNote(note,duration,intensity=64):
    intensity = numpy.clip(intensity, 0, 127)
    note-=20
    octave = str((note-4)/12+1)
    string = noteList[(note-1)%12]
    noteName = string + octave
    song = ((noteName,4),)
    data = pysynth.make_wav(song,bpm=int(60000/duration),silent=True)
    sound=makeEmptySound(data.size, sampleRate=44100)
    sound.a=numpy.frombuffer(data,dtype=numpy.int8)
    for i in xrange(int(sound.samplerate*duration/1000)):
        sound.setSampleValue(i, int(sound.getSampleValue(i)*intensity/64))
    sound.blockingPlayInRange(0,int(sound.samplerate*duration/1000))
    


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
        
def playAtRate(sound,rate):
    if not sound.__class__ == Sound:
        print "playAtRate(sound,rate): Input is not a sound."
        raise ValueError
    sound.playAtRateInRange(rate,0,sound.nframes)
    
def playAtRateDur(sound,rate,dur):
    if not sound.__class__ == Sound:
        print "playAtRateDur(sound,rate,dur): Input is not a sound."
        raise ValueError
    sound.playAtRateInRange(rate,0,dur)
    
def playAtRateInRange(sound,rate,start,stop):
    if not sound.__class__ == Sound:
        print "playAtRateInRange(sound,rate,start,stop): Input is not a sound."
        raise ValueError
    sound.playAtRateInRange(rate,start,stop)
    
def blockingPlayAtRateInRange(sound,rate,start,stop):
    if not sound.__class__ == Sound:
        print "blockingPlayAtRateInRange(sound,rate,start,stop): Input is not a sound."
        raise ValueError
    sound.blockingPlayAtRateInRange(rate,start,stop)
    
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
    
def setSampleValue(sample, value):
    setSample(sample,value)
    
def getSampleValue(sample):
    return getSample(sample)

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
    return sound.nframes

def getNumSamples(sound):
    if not sound.__class__ == Sound:
        print "getNumSamples(sound): Input is not a sound."
        raise ValueError
    return sound.nsamples

def getDuration(sound):
    if not sound.__class__ == Sound:
        print "getDuration(sound): Input is not a sound."
        raise ValueError
    return sound.nframes/(sound.samplerate)


def writeSoundTo(sound,filename):
    global mediaFolder
    if not os.path.isabs(filename):
            filename = mediaFolder + filename
    if not sound.__class__ == Sound:
        print "writeSoundTo(sound,filename): Input is not a sound."
        raise ValueError 
    sound.writeTo(filename)


##
## Explore classes
##
        
class SoundCanvas(tk.Canvas):
    def __init__(self,parent,sound,channel,**cnf):
        tk.Canvas.__init__(self, parent, cnf,bg="black")
        self.sound=sound
        self.width = 640
        self.height = 196
        self.channel = channel
        self.maxFramesPerPixel = int(self.sound.nframes/self.width)
        self.framesPerPixel = self.maxFramesPerPixel
        self.selectedFrame = int(self.sound.nframes/2)
        self.parent=parent
        self.selection = None
        parent.pixelSizeVar.set(self.framesPerPixel)
        parent.indexVar.set(self.selectedFrame)
        parent.valueVar.set(self.sound.getChannelSampleValue(self.selectedFrame,0))
    
    
    def getSampleValue(self,index,offset=0):
        sample = offset+index
        if sample>=0 and sample < self.sound.nframes:
            return self.sound.getChannelSampleValue(self.framesPerPixel*sample,self.channel)
        return 0
    
    def framesPerScreen(self):
        return self.framesPerPixel*self.width
    
    def sampleToY(self,sample):
        if sample is not None:
            return int(-sample*self.height/(math.pow(2, self.sound.sampwidth*8-1)*2)+self.height/2)
        else:
            return 0
        
    def zoomToMax(self):
        self.parent.pixelSizeVar.set(1)
        
    def zoomToMin(self):
        self.parent.pixelSizeVar.set(int(self.sound.nframes/self.width))
    
    def moveToSelectedFrame(self):
        if self.selectedFrame<=self.getFrameAt(0) or self.selectedFrame>self.getFrameAt(self.width):
            self.xview_moveto(float(self.selectedFrame-self.framesPerScreen()/2)/self.sound.nframes) 
        self.render()
    
    #called by listeners to the pixelSizeVar
    def updateZoom(self):
        self.config(scrollregion=(0,0,int(self.sound.nframes/self.framesPerPixel),self.height))
        self.moveToSelectedFrame()
    
    def getFrameAt(self,x):
        return int(self.canvasx(x)*self.framesPerPixel)
    
    def getPixelAt(self,frame):
        return int(frame/self.framesPerPixel)
    
    def select(self,minX,maxX):
        self.selection = (self.getFrameAt(minX),self.getFrameAt(maxX))
        self.selection = numpy.clip(self.selection, 0, self.sound.nframes-1)
        self.render()
                
    def render(self):
        
        width = self.width
        height = self.height
        
        lastVal = None
        
        self.delete(tk.ALL)
        
        offset = int(self.canvasx(0)) 
        #getting information out of the canvas hack.
        #this will tell us how far along the canvas is
        #scrolled.
        
        if(self.selection is not None):
            self.create_rectangle(
                                  self.getPixelAt(self.selection[0]),
                                  0,
                                  self.getPixelAt(self.selection[1]),
                                  height,
                                  fill="#808080"
                                  )
        
        for i in xrange(width):
            newVal = self.getSampleValue(i,offset=offset)

            if lastVal is not None:
                self.create_line(self.canvasx(i-1),self.sampleToY(lastVal),self.canvasx(i),self.sampleToY(newVal),fill="white")
            lastVal=newVal
            
        self.create_line(self.canvasx(0),height/2,self.canvasx(width+4),height/2,fill="cyan")
        self.create_line(
                         self.getPixelAt(self.selectedFrame),0,
                         self.getPixelAt(self.selectedFrame),self.height,
                         fill="cyan")
        
    def updateX(self,*args):
        self.xview(*args)
        self.render()

class SoundExplorer(ttk.Frame):
    
    def __init__(self, parent,sound,channel):
        ttk.Frame.__init__(self, parent, padding = (3,3,3,3))   
        
        parent.resizable(0,0)
        
        self.parent = parent
        self.sound=duplicateSound(sound)
        self.channel = channel
        self.playing = False
        
        self.initControler()
        self.initUI()
        
    def _arangeLeftToRight(self,row,padx,*widgets):
        i=0
        for widget in widgets:
            widget.grid(row = row, column = i, padx = padx)
            i = i+1
    
    def initControler(self):
        self.zoomedOut = True
        self.indexVar = tk.StringVar()
        self.indexVar.trace_variable('w', lambda *args:self.selectedFrameChangeListener(self.indexVar))
        self.valueVar = tk.StringVar()
        self.pixelSizeVar = tk.StringVar()
        self.pixelSizeVar.trace_variable('w', lambda *args:self.pixelSizeChangeListener(self.pixelSizeVar))
        self.numericValidatorCommand = (self.register(self.validateNumericEntry), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
    
    def initUI(self):
        if self.sound.filename is not None:
            self.parent.title(self.sound.filename)
        else:
            self.parent.title("Sound Explorer")
        
        
        #Play/pause buttons on first row
        playFrame = ttk.Frame(self)
        playFrame.grid(row=0,column=0,pady=4)

        self.playEntire = ttk.Button(playFrame, text="Play Entire Sound",command=self.playEntireButtonCallback)
        self.playBefore = ttk.Button(playFrame, text="Play Before",state=tk.DISABLED,command=self.playBeforeButtonCallback)
        self.playAfter = ttk.Button(playFrame, text="Play After",command=self.playAfterButtonCallback)
        self.stop = ttk.Button(playFrame,text = "Stop",state=tk.DISABLED,command=self.stopButtonCallback)
        
        self._arangeLeftToRight(0,2,self.playEntire,self.playBefore,self.playAfter,self.stop)
        
        #Selection buttons and labels on second row
        selectFrame = ttk.Frame(self)
        selectFrame.grid(row=1,column=0,pady=4)
        
        self.playSelection = ttk.Button(selectFrame, text="Play Selection", state = tk.DISABLED, command = self.playSelectionButtonCallback)
        self.clearSelection = ttk.Button(selectFrame, text="Clear Selection", state = tk.DISABLED, command = self.clearButtonCallback)
        self.startLabel = ttk.Label(selectFrame, text="Start Index: N/A")
        self.stopLabel = ttk.Label(selectFrame, text="Stop Index: N/A")
        
        self._arangeLeftToRight(0,2,self.playSelection,self.clearSelection,self.startLabel,self.stopLabel)
        
        #canvas to show sound in
        self.scrollbar = ttk.Scrollbar(self,orient=tk.HORIZONTAL)
        self.scrollbar.grid(row=3,column=0,sticky=tk.E+tk.W)
        
        self.soundImage = SoundCanvas(self,self.sound,self.channel,width = 640, height = 196, xscrollcommand=self.scrollbar.set)
        self.soundImage.bind('<Button-1>', self.pressCallback)
        self.soundImage.bind('<ButtonRelease-1>', self.releaseCallback)
        self.soundImage.bind('<B1-Motion>', self.dragCallback)
        self.soundImage.grid(row = 2, column = 0)
        
        self.scrollbar.config(command=self.soundImage.updateX)
        
        #frame for fine sample selection
        
        fineSelectFrame = ttk.Frame(self)
        fineSelectFrame.grid(row=4,column=0,pady=4)
        
        self.imagePaths = ["endLeft.gif","leftArrow.gif","rightArrow.gif","endRight.gif"]
        self.imagePaths = map(lambda x: os.path.join("images",x),self.imagePaths)
        self.images = map(Im.open,self.imagePaths)
        self.tkImages = map(ImageTk.PhotoImage,self.images)
        
        self.rewind = ttk.Button(fineSelectFrame,image=self.tkImages[0],padding=0, command = self.rewindButtonCallback)
        self.back = ttk.Button(fineSelectFrame,image=self.tkImages[1],padding=0,command = self.backButtonCallback)
        
        currentIndexLabel = ttk.Label(fineSelectFrame, text="Current Index: ")
        self.currentIndex = ttk.Entry(fineSelectFrame,textvariable=self.indexVar,validate='key', validatecommand = self.numericValidatorCommand)
        sampleValueLabel =  ttk.Label(fineSelectFrame, text="Sample Value: ")
        
        self.sampleValue =  ttk.Entry(fineSelectFrame,textvariable=self.valueVar)
        self.sampleValue.config(state=tk.DISABLED)

        
        
        self.forward = ttk.Button(fineSelectFrame,image=self.tkImages[2],padding=0,command=self.forwardButtonCallback)
        self.fastForward = ttk.Button(fineSelectFrame,image=self.tkImages[3],padding=0,command=self.fastForwardButtonCallback)
    
        self._arangeLeftToRight(0,2,self.rewind,self.back,currentIndexLabel,self.currentIndex,sampleValueLabel,self.sampleValue,self.forward,self.fastForward)
        
        #pixel size information window
        
        sizeInfoFrame = ttk.Frame(self)
        sizeInfoFrame.grid(row=5,column=0,pady=4)
        
        pixelSizeLabel = ttk.Label(sizeInfoFrame, text = "The number of samples between pixels: ")
        
        self.samplesPerPixel = ttk.Entry(sizeInfoFrame,textvariable=self.pixelSizeVar,validate='key', validatecommand = self.numericValidatorCommand)
        
        self._arangeLeftToRight(0, 2,pixelSizeLabel,self.samplesPerPixel)
        
        #zoom button
        
        self.zoomButton = ttk.Button(self,text="Zoom In",command = self.zoomButtonCallback)
        self.zoomButton.grid(row=6,column=0)
        
        self.soundImage.render()
        self.updatePlayButtons()
        self.pack()
    
    #threading nonsense. If the tkinter thread ever blocks it causes bad things. If any tkinter
    #calls happen in another thread even worse things happen. The solution is callback hell.
    #This is used the cause sounds to play, then update the buttons once they are done playing.
    #It is designed for use with blocking methods. With a non blocking method it will
    #immediately enable the play buttons again.
    def doPlay(self,playCallback,*args,**kvargs):
        def helper():
            playCallback(*args,**kvargs)
            self.playing=False
            tkDo(self.updatePlayButtons)
        
        threading.Thread(target=helper).start()
            
    def playEntireButtonCallback(self):
        self.playing = True
        self.updatePlayButtons()
        self.doPlay(self.sound.blockingPlay)
        
    def playBeforeButtonCallback(self):
        self.playing = True
        self.updatePlayButtons()
        self.doPlay(self.sound.blockingPlayInRange,0,self.soundImage.selectedFrame)
        
    def playAfterButtonCallback(self):
        self.playing = True
        self.updatePlayButtons()
        self.doPlay(self.sound.blockingPlayInRange,self.soundImage.selectedFrame,self.sound.nframes-1)
        
    def stopButtonCallback(self):
        self.playing = False
        self.updatePlayButtons()
        self.sound.stopPlaying()
        
    def playSelectionButtonCallback(self):
        self.playing = True
        self.updatePlayButtons()
        self.doPlay(self.sound.blockingPlayInRange,self.soundImage.selection[0],self.soundImage.selection[1])
        
    def clearButtonCallback(self):
        self.soundImage.selection = None
        self.soundImage.render()
        self.playSelection.config(state=tk.DISABLED)
        self.clearSelection.config(state=tk.DISABLED)
        self.startLabel.config(text = "Start Index: N/A")
        self.stopLabel.config(text = "Stop Index: N/A")
    
    def rewindButtonCallback(self):
        self.indexVar.set(0)
        
    def fastForwardButtonCallback(self):
        self.indexVar.set(self.sound.nframes-1)
    
    def backButtonCallback(self):
        self.indexVar.set(
                          max(self.soundImage.selectedFrame-self.soundImage.framesPerPixel,0)
                          )
        
    def forwardButtonCallback(self):
        self.indexVar.set(
                          min(self.soundImage.selectedFrame+self.soundImage.framesPerPixel,self.sound.nframes-1)
                          )
        
    def zoomButtonCallback(self):
        if self.zoomedOut: #button reads zoom in
            self.zoomedOut = False
            self.soundImage.zoomToMax()
            self.zoomButton.config(text = "Zoom Out")
        else: #button reads zoom out
            self.zoomedOut = True
            self.soundImage.zoomToMin()
            self.zoomButton.config(text = "Zoom In")
            
    def validateNumericEntry(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed == '':
            return True
        if text in '0123456789':
            try:
                int(value_if_allowed)
                return True
            except:
                return False
        else:
            return False
            
    def pixelSizeChangeListener(self,stringVar):
        if hasattr(self,'soundImage'):
            try:
                self.soundImage.framesPerPixel = min(int(stringVar.get()),self.soundImage.maxFramesPerPixel)
                if self.soundImage.framesPerPixel<1:
                    self.soundImage.framesPerPixel=1
            except:
                self.soundImage.framesPerPixel = 1
            self.soundImage.updateZoom()
    
    def updatePlayButtons(self):
        if not self.playing:
            self.stop.config(state=tk.DISABLED)
            self.playEntire.config(state=tk.NORMAL)
            if(self.soundImage.selection is not None):
                self.playSelection.config(state=tk.NORMAL)
            if self.soundImage.selectedFrame == 0:
                self.playAfter.config(state=tk.NORMAL)
                self.playBefore.config(state=tk.DISABLED)
            elif self.soundImage.selectedFrame == self.sound.nframes-1:
                self.playAfter.config(state=tk.DISABLED)
                self.playBefore.config(state=tk.NORMAL)
            else:
                self.playAfter.config(state=tk.NORMAL)
                self.playBefore.config(state=tk.NORMAL)
        else:
            self.playAfter.config(state=tk.DISABLED)
            self.playBefore.config(state=tk.DISABLED)
            self.playSelection.config(state=tk.DISABLED)
            self.playEntire.config(state=tk.DISABLED)
            self.stop.config(state=tk.NORMAL)
    
    def selectedFrameChangeListener(self,stringVar):
        if hasattr(self,'soundImage'):
            try:
                self.soundImage.selectedFrame = int(stringVar.get())
            except:
                self.soundImage.selectedFrame = 0
            
            self.soundImage.selectedFrame = min(self.soundImage.selectedFrame,self.sound.nframes-1)
            
            self.updatePlayButtons()
            self.valueVar.set(self.sound.getChannelSampleValue(self.soundImage.selectedFrame,self.channel))
            self.soundImage.moveToSelectedFrame()
            
    def pressCallback(self,event):
        self.dragStartX = event.x
        
    def releaseCallback(self,event):
        if self.dragStartX == event.x:
            self.indexVar.set(self.soundImage.getFrameAt(event.x))
        
    def dragCallback(self,event):
        minX = min(event.x,self.dragStartX)
        maxX = max(event.x,self.dragStartX)
        self.soundImage.select(minX,maxX)
        if not self.playing:
            self.playSelection.config(state=tk.NORMAL)
        self.clearSelection.config(state=tk.NORMAL)
        self.startLabel.config(text = "Start Index: "+str(self.soundImage.selection[0]))
        self.stopLabel.config(text = "Stop Index: "+str(self.soundImage.selection[1]))

class PictureExplorer(ttk.Frame):
    def __init__(self,parent,picture,*args):
        ttk.Frame.__init__(self,parent,*args)
        self.picture = picture
        self.parent=parent
        self.imwidth=picture.getWidth()
        self.imheight=picture.getHeight()
        self.scales = [.25,
                       .5,
                       .75,
                       1,
                       1.5,
                       2,
                       5]
        self.zoomLevel = 3
        self.x=0
        self.y=0
        
        self.xVar = tk.StringVar()
        self.yVar = tk.StringVar()
        self.xVar.trace('w', self.varTrace)
        self.yVar.trace('w', self.varTrace)
        self.numericValidatorCommand = (self.register(self.validateNumericEntry), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        self.initUI()
    
    def _arangeLeftToRight(self,row,padx,*widgets):
        i=0
        for widget in widgets:
            widget.grid(row = row, column = i, padx = padx)
            i = i+1
    
    def initUI(self):
        if self.picture.filename is not None and self.picture.filename != '':
            self.parent.title(self.picture.filename)
        else:
            self.parent.title("Picture Explorer")
        
        
        self.menubar = tk.Menu(self.parent)
        self.zoomMenu = tk.Menu(self.menubar,tearoff=0)
        self.zoomMenu.add_command(label="25%",command = lambda: self.menuCallback(0))
        self.zoomMenu.add_command(label="50%",command = lambda: self.menuCallback(1))
        self.zoomMenu.add_command(label="75%",command = lambda: self.menuCallback(2))
        self.zoomMenu.add_command(label="100%",command = lambda: self.menuCallback(3))
        self.zoomMenu.add_command(label="150%",command = lambda: self.menuCallback(4))
        self.zoomMenu.add_command(label="200%",command = lambda: self.menuCallback(5))
        self.zoomMenu.add_command(label="500%",command = lambda: self.menuCallback(6))
        
        self.zoomMenu.entryconfig(self.zoomLevel, state=tk.DISABLED)
        
        self.menubar.add_cascade(label="Zoom",menu=self.zoomMenu)
        self.parent.config(menu = self.menubar)
        
        #first row, fine movement
        fineMovementFrame = ttk.Frame(self)
        fineMovementFrame.grid(row=0,column=0)
        
        self.imagePaths = ["leftArrow.gif","rightArrow.gif"]
        self.imagePaths = map(lambda x: os.path.join("images",x),self.imagePaths)
        self.images = map(Im.open,self.imagePaths)
        self.tkImages = map(ImageTk.PhotoImage,self.images)
        
        xLabel = ttk.Label(fineMovementFrame,text = "X:")
        self.left = ttk.Button(fineMovementFrame,image=self.tkImages[0],padding=0,command=lambda *stuf:self.buttonCallback(-1, 0))
        self.xEntry = ttk.Entry(fineMovementFrame,textvariable=self.xVar,validate='key',validatecommand=self.numericValidatorCommand)
        self.right = ttk.Button(fineMovementFrame,image=self.tkImages[1],padding=0,command=lambda *stuf:self.buttonCallback(1, 0))
        yLabel = ttk.Label(fineMovementFrame,text = "Y:")
        self.up = ttk.Button(fineMovementFrame,image=self.tkImages[0],padding=0,command=lambda *stuf:self.buttonCallback(0, -1))
        self.yEntry = ttk.Entry(fineMovementFrame,textvariable=self.yVar,validate='key',validatecommand=self.numericValidatorCommand)
        self.down = ttk.Button(fineMovementFrame,image=self.tkImages[1],padding=0,command=lambda *stuf:self.buttonCallback(0, 1))
        
        self._arangeLeftToRight(0, 2,xLabel,self.left,self.xEntry,self.right,yLabel,self.up,self.yEntry,self.down)
        
        #second row, color
        
        colorFrame = ttk.Frame(self)
        colorFrame.grid(row=1,column=0)
        
        self.colorLabel=ttk.Label(colorFrame,text="R: 0 G: 0 B: 0   Color at location: ")
        self.colorSample = tk.Canvas(colorFrame,width = 25, height = 25, background = "black")
        self._arangeLeftToRight(0, 0,self.colorLabel,self.colorSample)
        
        self.updateColor()
        
        #third row, picture
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(2,weight=1)
        self.hScrollbar = ttk.Scrollbar(self,orient=tk.HORIZONTAL)
        self.vScrollbar = ttk.Scrollbar(self,orient=tk.VERTICAL)
        imwidth,imheight=self.imwidth,self.imheight
        
        
        self.exploreCanvas = tk.Canvas(self,width=imwidth,height = imheight,
                                       xscrollcommand=self.hScrollbar.set,
                                       yscrollcommand=self.vScrollbar.set,
                                       scrollregion=(0,0,imwidth,imheight))
        self.exploreCanvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.exploreCanvas.grid(row=2,column=0,sticky=tk.N+tk.S+tk.W+tk.E)
        self.exploreCanvas.bind('<Button-1>', self.pressCallback)
        self.exploreCanvas.bind('<B1-Motion>', self.pressCallback)
        
        
        self.mipmap = map(lambda x:self.picture.getImage().resize((int(imwidth*x),int(imheight*x)),Im.NEAREST),self.scales)
        self.mipmap = map(ImageTk.PhotoImage,self.mipmap)
        
        self.exploreCanvas.mipmap = self.mipmap #not taking any chances with the gc
        self.render()
        
        self.hScrollbar.config(command=self.exploreCanvas.xview)
        self.vScrollbar.config(command=self.exploreCanvas.yview)
        
        self.hScrollbar.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.vScrollbar.grid(row=2,column=1,sticky=tk.N+tk.S)
        
        self.pack(fill=tk.BOTH,expand=tk.YES)
        
        self.parent.bind('<MouseWheel>', self.scroll)
    
    def scroll(self,event):
        direction = 0
        if event.num == 5 or event.delta == -120:
            direction = 1
        if event.num == 4 or event.delta == 120:
            direction = -1
        self.exploreCanvas.yview_scroll(direction, tk.UNITS)
    
    def menuCallback(self,index):
        self.zoomMenu.entryconfig(self.zoomLevel, state=tk.NORMAL)
        self.zoomMenu.entryconfig(index, state=tk.DISABLED)
        self.zoomLevel = index
        self.updateZoom()
    
    def render(self):
        scale = self.scales[self.zoomLevel]
        image = self.mipmap[self.zoomLevel]
        self.exploreCanvas.delete(tk.ALL)
        self.canvasImage = self.exploreCanvas.create_image(0, 0, image=image, anchor='nw')
        self.exploreCanvas.config(scrollregion=(0,0,int(self.imwidth*scale),int(self.imheight*scale)))
        x=self.x*scale
        y=self.y*scale
        self.exploreCanvas.create_rectangle(x-1,y-3,x+1,y+3,fill="black")
        self.exploreCanvas.create_rectangle(x-3,y-1,x+3,y+1,fill="black")
        self.exploreCanvas.create_line(x-3,y,x+4,y,fill="yellow")
        self.exploreCanvas.create_line(x,y-3,x,y+4,fill="yellow")
        
    def updateColor(self):
        try:
            self.x=int(self.xVar.get())
        except:
            self.x=0
        try:
            self.y=int(self.yVar.get())
        except:
            self.y=0
            
        self.x = int(numpy.clip(self.x, 0, self.imwidth-1))
        self.y = int(numpy.clip(self.y, 0, self.imheight-1))
        
        r,g,b = self.picture.getColorXY(self.x,self.y)
        self.colorLabel.config(text="R: {} G: {} B: {}   Color at location: ".format(r,g,b))
        self.colorSample.config(background = '#%02x%02x%02x' % (r,g,b))
        
    def varTrace(self,*args):
        self.updateColor()
        self.render()
        
    def pressCallback(self,event):
        scale = self.scales[self.zoomLevel]
        event.x = numpy.clip(int(self.exploreCanvas.canvasx(event.x)/scale), 0, self.imwidth-1)
        event.y = numpy.clip(int(self.exploreCanvas.canvasy(event.y)/scale), 0, self.imheight-1)
        self.xVar.set(event.x)
        self.yVar.set(event.y)
        self.render()
    
    def buttonCallback(self,dx,dy):
        if self.x+dx>=0 and self.x+dx<self.imwidth:
            self.xVar.set(self.x+dx)
        if self.y+dy>=0 and self.y+dy<self.imwidth:
            self.yVar.set(self.y+dy)
        
    def updateZoom(self):
        self.render()
        
    def validateNumericEntry(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed == '':
            return True
        if text in '0123456789':
            try:
                int(value_if_allowed)
                return True
            except:
                return False
        else:
            return False

##
## Global Explore Functions
##

def explore(media):
    if media.__class__ == Sound:
        openSoundTool(media)
    if media.__class__ == Picture:
        openPictureTool(media)

def openSoundTool(sound):
    def tkCallback():
        window = tk.Toplevel(root)
        explorer = SoundExplorer(window,sound,0)  # @UnusedVariable
    tkGet(tkCallback)
    
def openPictureTool(picture):
    def tkCallback():
        window = tk.Toplevel(root)
        explorer = PictureExplorer(window,picture) #@UnusedVariable
    tkGet(tkCallback)

def makeWorld(width=None, height=None):
    if width is None:
        width = 640
    if height is None:
        height = 480
    def tkHelper():
        canvas = tur.ScrolledCanvas(tk.Toplevel(root),width=width, height=height,canvwidth=width, canvheight=height)
        canvas.pack()
        screen = tur.TurtleScreen(canvas)
        screen.delay(0)
        return screen
    return tkGet(tkHelper)

##
## Global turtle functions
##

def makeTurtle(world):
    def tkHelper():
        theturtle = tur.RawTurtle(world)
        theturtle.setheading(90)
        theturtle.shape("turtle")
        colorList = [blue,red,green,gray,lightGray,yellow,orange,pink,magenta,cyan]
        color = random.choice(colorList)
        theturtle.fillcolor(color.makeDarker().getRGBString())
        theturtle.pencolor(color.getRGBString())
        return theturtle
    return tkGet(tkHelper)

def getTurtleList(world):
    return tkGet(world.turtles)

def turn(turtle, degrees=90):
    tkGet(turtle.right,degrees)
    
def turnRight(turtle):
    tkGet(turtle.right,90)

def turnToFace(turtle, x, y=None):
    
    def tkHelper():
        if y is not None:
            turtle.setheading(turtle.towards(
                                             -int(turtle.getscreen().screensize()[0]/2)+x, #the strange transformation is to maintain compatability with JES
                                             int(turtle.getscreen().screensize()[1]/2)-y))
        elif x.__class__ == tur.RawTurtle:
            turtle.setheading(turtle.towards(x)) 
            
    tkGet(tkHelper)
    
def turnLeft(turtle):
    tkGet(turtle.left,90)
    
def forward(turtle, pixels=100):
    tkGet(turtle.forward,pixels)
    
def backward(turtle, pixels=100):
    tkGet(turtle.backward,pixels)

def moveTo(turtle, x, y):
    tkGet(turtle.goto,
          -int(turtle.getscreen().screensize()[0]/2)+x, #the strange transformation is to maintain compatability with JES
          int(turtle.getscreen().screensize()[1]/2)-y)

def penUp(turtle):
    tkGet(turtle.penup)
    
def penDown(turtle):
    tkGet(turtle.pendown)
    
def getXPos(turtle):
    return tkGet(turtle.xcor)+int(turtle.getscreen().screensize()[0]/2) #the strange transformation is to maintain compatability with JES

def getYPos(turtle):
    return -tkGet(turtle.ycor)+int(turtle.getscreen().screensize()[1]/2) #the strange transformation is to maintain compatability with JES

def getHeading(turtle):
    return tkGet(turtle.heading)-90 #the strange transformation is to maintain compatability with JES

#TODO: this is very slow
def drop(turtle,picture):
    def tkHelper():
        image = Im.new("RGBA", (picture.getWidth(), picture.getHeight()))
        image.paste(picture.getImage(),(0,0))
        angle = turtle.heading()-90
        angle = angle % 360
        print angle
        xOffset = -picture.getHeight()*cos(radians(angle+90))
        yOffset = +picture.getHeight()*sin(radians(angle+90))
        image = image.rotate(angle,expand=True)
        if(angle>=270):
            yOffset = 0
        elif(angle>=180):
            xOffset = -image.size[0]
        elif(angle>=90):
            yOffset = -image.size[1]
            xOffset = xOffset - image.size[0]
        else:
            xOffset = 0
            yOffset = yOffset - image.size[1]
        tkImage = ImageTk.PhotoImage(image)
        canvas = turtle.getscreen().getcanvas()
        try:
            #garbage collection stuff.
            #This is the standard way to prevent
            #the tkImage from going away
            canvas.turtleImages.append(tkImage)
        except:
            canvas.turtleImages = [tkImage]
        canvas.create_image(turtle.xcor()+xOffset,-turtle.ycor()+yOffset,image=tkImage,anchor='nw')
        
    tkGet(tkHelper)
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
