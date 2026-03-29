import tkinter as tk
from tkinter import ttk, messagebox
from AccountManager import AccountManager
from LibraryManager import LibraryManager
from CatalogueFrame import CatalogueFrame

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        # Card frame centred in the window
        Card = tk.Frame(self, bg="white", padx=40, pady=40)
        Card.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(Card, text="Library Management System", font=("Arial", 20, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=(0, 4))
        tk.Label(Card, text="Staff Login", font=("Arial", 11), bg="white", fg="grey").grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Separator
        ttk.Separator(Card, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # ID field
        tk.Label(Card, text="ID", font=("Arial", 11), bg="white").grid(row=3, column=0, padx=(0, 10), pady=8, sticky="e")
        self.__IDEntry = ttk.Entry(Card, width=25, font=("Arial", 11))
        self.__IDEntry.grid(row=3, column=1, pady=8)

        # Password field
        tk.Label(Card, text="Password", font=("Arial", 11), bg="white").grid(row=4, column=0, padx=(0, 10), pady=8, sticky="e")
        self.__PasswordEntry = ttk.Entry(Card, width=25, show="*", font=("Arial", 11))
        self.__PasswordEntry.grid(row=4, column=1, pady=8)

        # Login button
        ttk.Button(Card, text="Log In", command=self.__HandleLogin).grid(row=5, column=0, columnspan=2, pady=(20, 4), ipadx=20, ipady=6)

        # Error label
        self.__ErrorLabel = tk.Label(Card, text="", fg="red", font=("Arial", 10), bg="white")
        self.__ErrorLabel.grid(row=6, column=0, columnspan=2)

    def __HandleLogin(self):
        ID = self.__IDEntry.get()
        Password = self.__PasswordEntry.get()
        Result = self.__controller.GetAM().LogIn(ID, Password)
        if "successfully" in Result:
            self.__controller.GetLM().StartUp()
            self.__controller.ShowFrame(Dashboard)
        else:
            self.__ErrorLabel.config(text=Result)


class Dashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        # Sidebar column takes 1 part, content area takes 4 parts
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        Sidebar = tk.Frame(self, bg="#1e293b", width=180)
        Sidebar.grid_propagate(False)
        Sidebar.grid_columnconfigure(0, weight=1)
        Sidebar.grid(row=0, column=0, sticky="nsew")
        Sidebar.grid_rowconfigure(8, weight=1)  # pushes logout to the bottom

        # User info at top of sidebar
        self.__NameLabel = tk.Label(Sidebar, text="", font=("Arial", 12, "bold"), bg="#1e293b", fg="white", anchor="w")
        self.__NameLabel.grid(row=0, column=0, sticky="ew", padx=15, pady=(20, 2))
        self.__RoleLabel = tk.Label(Sidebar, text="", font=("Arial", 10), bg="#1e293b", fg="#94a3b8", anchor="w")
        self.__RoleLabel.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Separator
        ttk.Separator(Sidebar, orient="horizontal").grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Nav buttons
        NavButtons = [
            ("Catalogue", CatalogueFrame),
            ("Loans", LoansFrame),
            ("Reservations", ReservationsFrame),
            ("Students", StudentsFrame),
            ("Staff", StaffFrame),
        ]
        for i, (Label, Frame) in enumerate(NavButtons):
            tk.Button(
                Sidebar, text=Label, font=("Arial", 11),
                bg="#1e293b", fg="white", bd=0, activebackground="#334155",
                activeforeground="white", anchor="w", padx=15, pady=8,
                relief="groove", borderwidth=1,
                command=lambda F=Frame: self.__ShowContent(F)
            ).grid(row=i+3, column=0, sticky="ew", padx=8, pady=2)

        # Logout button pinned to bottom
        tk.Button(
            Sidebar, text="Log Out", font=("Arial", 11),
            bg="#1e293b", fg="#f87171", bd=0, activebackground="#334155",
            activeforeground="#f87171", anchor="w", padx=15, pady=8,
            relief="groove", borderwidth=1,
            command=self.__HandleLogout
        ).grid(row=9, column=0, sticky="ew", padx=8, pady=(0, 10))

        # --- Content Area ---
        ContentArea = tk.Frame(self, bg="#f0f4f8")
        ContentArea.grid(row=0, column=1, sticky="nsew")
        ContentArea.grid_rowconfigure(0, weight=1)
        ContentArea.grid_columnconfigure(0, weight=1)

        # Stack all content frames in the content area
        self.__ContentFrames = {}
        for F in (CatalogueFrame, LoansFrame, ReservationsFrame, StudentsFrame, StaffFrame):
            Frame = F(ContentArea, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__ContentFrames[F] = Frame

        # Show catalogue by default
        self.__ShowContent(CatalogueFrame)

    def __ShowContent(self, FrameClass):
        self.__ContentFrames[FrameClass].tkraise()

    def __HandleLogout(self):
        self.__controller.GetAM().LogOut()
        self.__controller.ShowFrame(LoginFrame)
        self.__controller.DestroyDashboard()

    def OnShow(self):
        # Refresh user info when dashboard is shown after login
        self.__NameLabel.config(text=self.__controller.GetAM().GetCurrentUserName())
        self.__RoleLabel.config(text=self.__controller.GetAM().GetCurrentAccessLevel())


# --- Placeholder content frames ---
class LoansFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        tk.Label(self, text="Loans", font=("Arial", 20, "bold"), bg="#f0f4f8").pack(pady=20)

class ReservationsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        tk.Label(self, text="Reservations", font=("Arial", 20, "bold"), bg="#f0f4f8").pack(pady=20)

class StudentsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        tk.Label(self, text="Students", font=("Arial", 20, "bold"), bg="#f0f4f8").pack(pady=20)

class StaffFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        tk.Label(self, text="Staff", font=("Arial", 20, "bold"), bg="#f0f4f8").pack(pady=20)


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
        # Only load the LoginFrame at startup to prevent unauthorized API calls
        Login = LoginFrame(self, self)
        Login.grid(row=0, column=0, sticky="nsew")
        self.__Frames[LoginFrame] = Login

        self.ShowFrame(LoginFrame)

    def ShowFrame(self, FrameClass):
        # Lazy-load frames: create them only when requested
        if FrameClass not in self.__Frames:
            Frame = FrameClass(self, self)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__Frames[FrameClass] = Frame
            
        Frame = self.__Frames[FrameClass]
        Frame.tkraise()
        if hasattr(Frame, "OnShow"):
            Frame.OnShow()

    def DestroyDashboard(self):
        # Security measure: Wipe the dashboard from memory on logout
        if Dashboard in self.__Frames:
            self.__Frames[Dashboard].destroy()
            del self.__Frames[Dashboard]

    def GetAM(self):
        return self.__AM

    def GetLM(self):
        return self.__LM

if __name__ == "__main__":
    app = Main()
    app.mainloop()