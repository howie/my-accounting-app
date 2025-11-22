import tkinter as tk
from tkinter import ttk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Accounting Book")
        self.geometry("800x600")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')
