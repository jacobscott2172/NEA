import tkinter as tk
from Managers.AccountManager import AccountManager
from Managers.LibraryManager import LibraryManager
from Frames.LoginFrame import LoginFrame
from Frames.DashboardFrame import DashboardFrame

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1200x700")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.__AM = AccountManager()
        self.__LM = LibraryManager(self.__AM)

        self.__Frames = {}
        for F in (LoginFrame, DashboardFrame):
            Frame = F(self, self)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__Frames[F] = Frame

        self.ShowFrame(LoginFrame)

    def ShowFrame(self, FrameClass):
        Frame = self.__Frames[FrameClass]
        Frame.tkraise()
        if hasattr(Frame, "OnShow"):
            Frame.OnShow()

    def GetAM(self):
        return self.__AM

    def GetLM(self):
        return self.__LM

if __name__ == "__main__":
    app = Main()
    app.mainloop()