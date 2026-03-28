import tkinter as tk
from AccountManager import AccountManager
from LibraryManager import LibraryManager

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.__controller = controller
        tk.Label(self, text="ID").grid(row=0, column=0, padx=10, pady=5)
        self.__IDEntry = tk.Entry(self)
        self.__IDEntry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self, text="Password").grid(row=1, column=0, padx=10, pady=5)
        self.__PasswordEntry = tk.Entry(self, show="*")
        self.__PasswordEntry.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(self, text="Log In", command=self.__HandleLogin).grid(row=2, column=0, columnspan=2, pady=10)

        self.__ErrorLabel = tk.Label(self, text="", fg="red")
        self.__ErrorLabel.grid(row=3, column=0, columnspan=2)

    def __HandleLogin(self):
        ID = self.__IDEntry.get()
        Password = self.__PasswordEntry.get()
        Result = self.__controller.GetAM().LogIn(ID, Password)
        if "successfully" in Result:
            self.__controller.ShowFrame(FrameB)
        else:
            self.__ErrorLabel.config(text=Result)

class FrameB(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="blue")
        self.__controller = controller
        tk.Label(self, text="This is Frame B").pack()
        self.__AccessLabel = tk.Label(self, text="")
        self.__AccessLabel.pack()
        tk.Button(self, text="Go to A", command=lambda: controller.ShowFrame(LoginFrame)).pack()
    
    def OnShow(self):
        self.__AccessLabel.config(text=self.__controller.GetAM().GetCurrentAccessLevel())

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.__AM = AccountManager()
        self.__LM = LibraryManager(self.__AM)

        self.__Frames = {}
        for F in (LoginFrame, FrameB):
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