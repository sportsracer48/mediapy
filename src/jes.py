# This is not really what I expect jes to look like,
# but tkinter needs a root node, and it needs for everything else
# to be run after the root is set up. Specifically,
# in order for a new window to be created, it needs to be
# created from within a tkinter thread. Here we get into a tkinter
# thread using the Tk.after function, which allows a callback
# to be immediately inserted into a tkinter thread.

from Tkinter import Tk
from ttk import Style
import runpy
import mymedia
import threading
import os
import sys

def program():
    userThread = threading.Thread(target = runpy.run_path, args = [os.path.join("src","test.py")])
    userThread.start()


root = Tk()
root.title("JES no longer stands for anything")
root.style = Style()

#feel free to select a better theme on your system than default
if sys.platform == 'win32':
    root.style.theme_use("xpnative")
else:
    root.style.theme_use("default")


#style things to make it look a bit more like JES
root.style = Style()
root.style.configure("TButton", padding = (0,3,0,3),
                     font = ('Default',10))
root.style.configure("TLabel", font = ('Default', 10))
root.iconbitmap(default=os.path.join("images","jesicon.ico"))


mymedia.setRoot(root)
root.after(0, program)
root.mainloop()
os._exit(0)