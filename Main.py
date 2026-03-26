import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
# dunno whats going on here, see notes in LM init method
from AccountManager import AccountManager
from LibraryManager import LibraryManager

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.__AM = AccountManager()
        self.__LM = LibraryManager(self.__AM)
        self.title("Library Management System")
        self.geometry("1920x1080")
        # Additional GUI setup can be done here
        self.label = ttk.Label(self, text='Hello, Tkinter!')
        self.label.pack()
        exitbutton = ttk.Button(self, text='Exit', command=self.promptexit)
        exitbutton.pack()
        
    def promptexit(self):
        if messagebox.askokcancel("Exit", "Do you really want to exit?"):
            self.__LM.exit()
            self.__AM.exit()
            self.destroy()
            
if __name__ == "__main__":
    app = Main()
    app.mainloop()