import tkinter as tk
from tkinter import ttk
from Frames.CatalogueFrame import CatalogueFrame
from Frames.LoansFrame import LoansFrame
from Frames.ReservationsFrame import ReservationsFrame
from Frames.StudentsFrame import StudentsFrame
from Frames.StaffFrame import StaffFrame
from Frames.AdminFrame import AdminFrame
from Frames.SysAdminFrame import SysAdminFrame

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        Sidebar = tk.Frame(self, bg="#1e293b", width=180)
        Sidebar.grid_propagate(False)
        Sidebar.grid_columnconfigure(0, weight=1)
        Sidebar.grid(row=0, column=0, sticky="nsew")
        Sidebar.grid_rowconfigure(10, weight=1)

        # User info at top of sidebar
        self.__NameLabel = tk.Label(Sidebar, text="", font=("Arial", 12, "bold"), bg="#1e293b", fg="white", anchor="w")
        self.__NameLabel.grid(row=0, column=0, sticky="ew", padx=15, pady=(20, 2))
        self.__RoleLabel = tk.Label(Sidebar, text="", font=("Arial", 10), bg="#1e293b", fg="#94a3b8", anchor="w")
        self.__RoleLabel.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Separator
        ttk.Separator(Sidebar, orient="horizontal").grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Nav buttons - Teacher level screens
        NavButtons = [
            ("Catalogue", CatalogueFrame),
            ("Loans", LoansFrame),
            ("Reservations", ReservationsFrame),
            ("Students", StudentsFrame),
            ("Staff", StaffFrame),
            ("Admin Panel", AdminFrame),
            ("SysAdmin Panel", SysAdminFrame),
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
        ).grid(row=11, column=0, sticky="ew", padx=8, pady=(0, 10))

        # --- Content Area ---
        ContentArea = tk.Frame(self, bg="#f0f4f8")
        ContentArea.grid(row=0, column=1, sticky="nsew")
        ContentArea.grid_rowconfigure(0, weight=1)
        ContentArea.grid_columnconfigure(0, weight=1)

        # Stack all content frames in the content area
        self.__ContentFrames = {}
        for F in (CatalogueFrame, LoansFrame, ReservationsFrame, StudentsFrame, StaffFrame, AdminFrame, SysAdminFrame):
            Frame = F(ContentArea, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__ContentFrames[F] = Frame

        self.__ShowContent(CatalogueFrame)

    def __ShowContent(self, FrameClass):
        self.__ContentFrames[FrameClass].tkraise()
        if hasattr(self.__ContentFrames[FrameClass], "OnShow"):
            self.__ContentFrames[FrameClass].OnShow()

    def __HandleLogout(self):
        from Frames.LoginFrame import LoginFrame
        self.__controller.GetAM().LogOut()
        self.__controller.ShowFrame(LoginFrame)

    def OnShow(self):
        # Refresh user info when dashboard is shown after login
        self.__NameLabel.config(text=self.__controller.GetAM().GetCurrentUserName())
        self.__RoleLabel.config(text=self.__controller.GetAM().GetCurrentAccessLevel())