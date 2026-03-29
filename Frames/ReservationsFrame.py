import tkinter as tk
from tkinter import ttk

class ReservationsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        tk.Label(self, text="ReservationsFrame", font=("Arial", 20, "bold"), bg="#f0f4f8").pack(pady=20)