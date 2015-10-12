from mymedia import *


class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

import sys
sys.stdout = Unbuffered(sys.stdout)

picture = makeEmptyPicture(600,600)

show(picture)
addText(picture,100,100,"test")
repaint(picture)
path = "C:/Users/Henry/Documents/LiClipse Workspace/jes/tests/test-sounds/moondog.Bird_sLament.wav"
sound = makeSound(path)
explore(sound)
explore(picture)
showInformation("info")
showWarning("warning")
showError("error")
print pickAFile()
print pickAFolder()
print pickASaveFile()
print requestString("string")
print requestNumber("number")
print requestInteger("integer")
print requestIntegerInRange("range 1,12",1,12)

