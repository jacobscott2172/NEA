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

        # Nav buttons with minimum access level required for visibility
        NavButtons = [
            ("Catalogue", CatalogueFrame, "Teacher"),
            ("Loans", LoansFrame, "Teacher"),
            ("Reservations", ReservationsFrame, "Teacher"),
            ("Students", StudentsFrame, "Teacher"),
            ("Staff", StaffFrame, "Teacher"),
            ("Admin Panel", AdminFrame, "Admin"),
            ("SysAdmin Panel", SysAdminFrame, "SysAdmin"),
        ]
        self.__NavButtons = {}
        for i, (Label, Frame, MinLevel) in enumerate(NavButtons):
            Btn = tk.Button(
                Sidebar, text=Label, font=("Arial", 11),
                bg="#1e293b", fg="white", bd=0, activebackground="#334155",
                activeforeground="white", anchor="w", padx=15, pady=8,
                relief="groove", borderwidth=1,
                command=lambda F=Frame: self.__ShowContent(F)
            )
            Btn.grid(row=i+3, column=0, sticky="ew", padx=8, pady=2)
            # Store button reference, its grid row, and the minimum access level required
            self.__NavButtons[Label] = (Btn, i+3, MinLevel)

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
        CurrentLevel = self.__controller.GetAM().GetCurrentAccessLevel()
        self.__RoleLabel.config(text=CurrentLevel)

        # Role hierarchy used to determine which buttons to show
        RoleHierarchy = {"None": 0, "Teacher": 1, "Admin": 2, "SysAdmin": 3}
        CurrentValue = RoleHierarchy.get(CurrentLevel, 0)

        # Show or hide nav buttons based on the logged-in user's access level
        for Label, (Btn, Row, MinLevel) in self.__NavButtons.items():
            RequiredValue = RoleHierarchy.get(MinLevel, 0)
            if CurrentValue >= RequiredValue:
                Btn.grid(row=Row, column=0, sticky="ew", padx=8, pady=2)
            else:
                Btn.grid_remove()

        # Reset to Catalogue view on each login to prevent a Teacher seeing
        # an Admin panel that was left open from a previous higher-level session
        self.__ShowContent(CatalogueFrame)