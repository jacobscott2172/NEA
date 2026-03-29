import tkinter as tk
from tkinter import ttk

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
        from Frames.DashboardFrame import DashboardFrame
        ID = self.__IDEntry.get()
        Password = self.__PasswordEntry.get()
        Result = self.__controller.GetAM().LogIn(ID, Password)
        if "successfully" in Result:
            self.__controller.GetLM().StartUp()
            self.__controller.ShowFrame(DashboardFrame)
        else:
            self.__ErrorLabel.config(text=Result)