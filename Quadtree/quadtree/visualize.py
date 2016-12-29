"""
     Visualize quadtree in separate window.
"""
from tkinter import Tk, Canvas, ALL, Toplevel, Button
from tkinter.font import Font

from quadtree.draw_tree import DrawTree, layoutDrawTree

class VisualizationWindow:
    def __init__(self, master):
        self.master = master
        self.frame = Toplevel(width=1024, height=512)

        self.canvas = Canvas(self.frame, width=1024, height=512)        

        self.frame.title("QuadTree Visualization")
        self.canvas.pack()
        self.font = None

    def plot(self, tree):
        """Given DrawTree information, plot the quadtree."""
        dt = DrawTree(tree)
        dt = layoutDrawTree(dt)
        self.canvas.delete(ALL)
        if self.font is None:
            self.font = Font(family='Times', size='24')
        dt.format(self.canvas, self.font, -1)