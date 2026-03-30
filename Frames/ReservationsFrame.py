import tkinter as tk
from tkinter import ttk, messagebox

class ReservationsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        # Configure grid - content fills frame
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Sub-navigation tabs ---
        TabBar = tk.Frame(self, bg="#f0f4f8")
        TabBar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self.__Tabs = {}
        for Label, Tab in [("All Reservations", AllReservationsTab), ("Today's Reservations", TodaysReservationsTab), ("My Reservations", MyReservationsTab)]:
            Btn = tk.Button(
                TabBar, text=Label, font=("Arial", 11),
                bg="#f0f4f8", fg="#1e293b", bd=0,
                activebackground="#1e293b", activeforeground="white",
                padx=15, pady=6,
                command=lambda T=Tab, B=Label: self.__ShowTab(T, B)
            )
            Btn.pack(side="left", padx=(0, 4))
            self.__Tabs[Label] = (Btn, Tab)

        # --- Tab content area ---
        self.__TabContainer = tk.Frame(self, bg="#f0f4f8")
        self.__TabContainer.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.__TabContainer.grid_rowconfigure(0, weight=1)
        self.__TabContainer.grid_columnconfigure(0, weight=1)

        self.__TabFrames = {}
        for Label, TabClass in [("All Reservations", AllReservationsTab), ("Today's Reservations", TodaysReservationsTab), ("My Reservations", MyReservationsTab)]:
            Frame = TabClass(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[TabClass] = Frame

        self.__ActiveTabClass = AllReservationsTab
        self.__ShowTab(AllReservationsTab, "All Reservations")

    def __ShowTab(self, TabClass, Label):
        for L, (Btn, _) in self.__Tabs.items():
            if L == Label:
                Btn.config(bg="#1e293b", fg="white")
            else:
                Btn.config(bg="#f0f4f8", fg="#1e293b")

        self.__ActiveTabClass = TabClass
        self.__TabFrames[TabClass].tkraise()
        # Only refresh if we have a user logged in
        if self.__controller.GetAM().GetCurrentUser() is not None:
            if hasattr(self.__TabFrames[TabClass], "OnShow"):
                self.__TabFrames[TabClass].OnShow()

    def OnShow(self):
        """Called by DashboardFrame when the main Reservations tab is selected"""
        if self.__controller.GetAM().GetCurrentUser() is not None:
            CurrentFrame = self.__TabFrames[self.__ActiveTabClass]
            if hasattr(CurrentFrame, "OnShow"):
                CurrentFrame.OnShow()


class AllReservationsTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # --- Search bar ---
        SearchBar = tk.Frame(self, bg="#f0f4f8")
        SearchBar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(SearchBar, text="Search:", font=("Arial", 11), bg="#f0f4f8").pack(side="left")
        self.__SearchEntry = ttk.Entry(SearchBar, width=30, font=("Arial", 11))
        self.__SearchEntry.pack(side="left", padx=8)
        ttk.Button(SearchBar, text="Search", command=self.__Search).pack(side="left")
        ttk.Button(SearchBar, text="Show All", command=self.__ShowAll).pack(side="left", padx=8)

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        TableFrame.grid_rowconfigure(0, weight=1)
        TableFrame.grid_columnconfigure(0, weight=1)

        # GetAllReservations returns: (URID, Title, ReservationDate, Quantity, UStaID, Forename, Surname, ClassCode)
        Columns = ("Res. ID", "Book Title", "Date", "Qty", "Staff", "Location")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Res. ID", width=60)
        self.__Table.column("Book Title", width=160)
        self.__Table.column("Date", width=90)
        self.__Table.column("Qty", width=40)
        self.__Table.column("Staff", width=120)
        self.__Table.column("Location", width=90)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Reservation Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a reservation to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Create Reservation", command=self.__ShowCreateForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Reservation", command=self.__ShowUpdateForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Delete Reservation", command=self.__DeleteReservation).pack(side="left", padx=(0, 8))

        # --- Inline create form ---
        self.__CreateForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__CreateForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__CreateForm.grid_remove()

        tk.Label(self.__CreateForm, text="Create Reservation", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=10, sticky="w", pady=(0, 8))
        tk.Label(self.__CreateForm, text="ISBN", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__CreateISBN = ttk.Entry(self.__CreateForm, width=15, font=("Arial", 10))
        self.__CreateISBN.grid(row=1, column=1, padx=(0, 8))
        tk.Label(self.__CreateForm, text="Location ID", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(8, 4))
        self.__CreateLocID = ttk.Entry(self.__CreateForm, width=10, font=("Arial", 10))
        self.__CreateLocID.grid(row=1, column=3, padx=(0, 8))
        tk.Label(self.__CreateForm, text="Date", font=("Arial", 10), bg="white").grid(row=1, column=4, sticky="e", padx=(8, 4))
        self.__CreateDate = ttk.Entry(self.__CreateForm, width=10, font=("Arial", 10))
        self.__CreateDate.grid(row=1, column=5, padx=(0, 4))
        tk.Label(self.__CreateForm, text="(YYYYMMDD)", font=("Arial", 9), bg="white", fg="grey").grid(row=1, column=6, sticky="w")
        tk.Label(self.__CreateForm, text="Quantity", font=("Arial", 10), bg="white").grid(row=1, column=7, sticky="e", padx=(8, 4))
        self.__CreateQuantity = ttk.Entry(self.__CreateForm, width=6, font=("Arial", 10))
        self.__CreateQuantity.grid(row=1, column=8, padx=(0, 10))
        self.__CreateFormError = tk.Label(self.__CreateForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__CreateFormError.grid(row=2, column=0, columnspan=10, pady=(8, 0))
        ttk.Button(self.__CreateForm, text="Submit", command=self.__SubmitCreate).grid(row=3, column=0, pady=8)
        ttk.Button(self.__CreateForm, text="Cancel", command=self.__HideCreateForm).grid(row=3, column=1, pady=8)

        # --- Inline update form ---
        self.__UpdateForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__UpdateForm.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__UpdateForm.grid_remove()

        tk.Label(self.__UpdateForm, text="Update Reservation", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))
        tk.Label(self.__UpdateForm, text="Res. ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__UpdateIDLabel = tk.Label(self.__UpdateForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__UpdateIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 8))
        tk.Label(self.__UpdateForm, text="Location ID", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(8, 4))
        self.__UpdateLocID = ttk.Entry(self.__UpdateForm, width=10, font=("Arial", 10))
        self.__UpdateLocID.grid(row=1, column=3, padx=(0, 8))
        tk.Label(self.__UpdateForm, text="Date", font=("Arial", 10), bg="white").grid(row=1, column=4, sticky="e", padx=(8, 4))
        self.__UpdateDate = ttk.Entry(self.__UpdateForm, width=10, font=("Arial", 10))
        self.__UpdateDate.grid(row=1, column=5, padx=(0, 4))
        tk.Label(self.__UpdateForm, text="Quantity", font=("Arial", 10), bg="white").grid(row=1, column=6, sticky="e", padx=(8, 4))
        self.__UpdateQuantity = ttk.Entry(self.__UpdateForm, width=6, font=("Arial", 10))
        self.__UpdateQuantity.grid(row=1, column=7, padx=(0, 10))
        self.__UpdateFormError = tk.Label(self.__UpdateForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__UpdateFormError.grid(row=2, column=0, columnspan=8, pady=(8, 0))
        ttk.Button(self.__UpdateForm, text="Submit", command=self.__SubmitUpdate).grid(row=3, column=0, pady=8)
        ttk.Button(self.__UpdateForm, text="Cancel", command=self.__HideUpdateForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetLM().GetAllReservations()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        Results = self.__controller.GetLM().SearchReservations(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            # Format: (URID, Title, ReservationDate, Quantity, UStaID, Forename, Surname, ClassCode)
            for Row in Results:
                StaffName = f"{Row[5]} {Row[6]}"
                self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], StaffName, Row[7]))
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        URID = Values[0]
        # GetReservationDetails returns: (URID, Title, ReservationDate, Quantity, UStaID, Forename, Surname, ClassCode)
        Details = self.__controller.GetLM().GetReservationDetails(URID)
        if isinstance(Details, tuple):
            Text = f"Reservation ID: {Details[0]}\nBook: {Details[1]}\nDate: {Details[2]}\nQuantity: {Details[3]}\nStaff: {Details[5]} {Details[6]} (ID: {Details[4]})\nLocation: {Details[7]}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)

    # --- Helper to hide all inline forms ---
    def __HideAllForms(self):
        self.__HideCreateForm()
        self.__HideUpdateForm()

    # --- Create reservation ---
    def __ShowCreateForm(self):
        self.__HideAllForms()
        self.__CreateForm.grid()

    def __HideCreateForm(self):
        self.__CreateForm.grid_remove()
        self.__CreateFormError.config(text="")
        self.__CreateISBN.delete(0, "end")
        self.__CreateLocID.delete(0, "end")
        self.__CreateDate.delete(0, "end")
        self.__CreateQuantity.delete(0, "end")

    def __SubmitCreate(self):
        try:
            ISBN = int(self.__CreateISBN.get())
            ULocID = int(self.__CreateLocID.get())
            ReservationDate = int(self.__CreateDate.get())
            Quantity = int(self.__CreateQuantity.get())
        except ValueError:
            self.__CreateFormError.config(text="All fields must be numeric. Date format: YYYYMMDD.")
            return
        if len(str(ReservationDate)) != 8:
            self.__CreateFormError.config(text="Date must be 8 digits (YYYYMMDD).")
            return
        if Quantity < 1:
            self.__CreateFormError.config(text="Quantity must be at least 1.")
            return
        # IssueReservation(ULocID, ReservationDate, ISBN, UStaID, Quantity)
        CurrentUser = self.__controller.GetAM().GetCurrentUser()
        Result = self.__controller.GetLM().IssueReservation(ULocID, ReservationDate, ISBN, CurrentUser, Quantity)
        if "successfully" in str(Result):
            self.__HideCreateForm()
            self.__ShowAll()
        else:
            self.__CreateFormError.config(text=str(Result))

    # --- Update reservation ---
    def __ShowUpdateForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a reservation to update.")
            return
        Values = self.__Table.item(Selected, "values")
        self.__HideAllForms()
        self.__UpdateIDLabel.config(text=str(Values[0]))
        # Pre-fill current values - Values = (Res. ID, Book Title, Date, Qty, Staff, Location)
        self.__UpdateDate.delete(0, "end")
        self.__UpdateDate.insert(0, str(Values[2]))
        self.__UpdateQuantity.delete(0, "end")
        self.__UpdateQuantity.insert(0, str(Values[3]))
        self.__UpdateForm.grid()

    def __HideUpdateForm(self):
        self.__UpdateForm.grid_remove()
        self.__UpdateFormError.config(text="")
        self.__UpdateLocID.delete(0, "end")
        self.__UpdateDate.delete(0, "end")
        self.__UpdateQuantity.delete(0, "end")

    def __SubmitUpdate(self):
        try:
            URID = int(self.__UpdateIDLabel.cget("text"))
            ULocID = int(self.__UpdateLocID.get())
            ReservationDate = int(self.__UpdateDate.get())
            Quantity = int(self.__UpdateQuantity.get())
        except ValueError:
            self.__UpdateFormError.config(text="All fields must be numeric. Date format: YYYYMMDD.")
            return
        if len(str(ReservationDate)) != 8:
            self.__UpdateFormError.config(text="Date must be 8 digits (YYYYMMDD).")
            return
        if Quantity < 1:
            self.__UpdateFormError.config(text="Quantity must be at least 1.")
            return
        # UpdateReservation(URID, ULocID, ReservationDate, Quantity)
        # Teachers can only update their own; Admins can update any
        Result = self.__controller.GetLM().UpdateReservation(URID, ULocID, ReservationDate, Quantity)
        if "successfully" in str(Result):
            self.__HideUpdateForm()
            self.__ShowAll()
        else:
            self.__UpdateFormError.config(text=str(Result))

    # --- Delete reservation ---
    def __DeleteReservation(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        URID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Delete reservation {URID}?"):
            # DeleteReservation - Teachers can only delete their own; Admins can delete any
            Result = self.__controller.GetLM().DeleteReservation(int(URID))
            if "successfully" in str(Result):
                self.__ShowAll()
                self.__DetailsText.config(text="Select a reservation to view details.")
            else:
                messagebox.showerror("Error", str(Result))


class TodaysReservationsTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        TableFrame.grid_rowconfigure(0, weight=1)
        TableFrame.grid_columnconfigure(0, weight=1)

        Columns = ("Res. ID", "Book Title", "Qty", "Staff", "Location")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Res. ID", width=60)
        self.__Table.column("Book Title", width=180)
        self.__Table.column("Qty", width=40)
        self.__Table.column("Staff", width=130)
        self.__Table.column("Location", width=100)
        self.__Table.grid(row=0, column=0, sticky="nsew")

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Info panel ---
        self.__InfoPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__InfoPanel.grid(row=0, column=1, sticky="nsew")
        tk.Label(self.__InfoPanel, text="Today's Reservations", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__InfoPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__InfoText = tk.Label(self.__InfoPanel, text="Reservations for today are shown here.\n\nCopy allocation and notification emails are processed automatically at login via the StartUp routine.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__InfoText.pack(anchor="w")

    def OnShow(self):
        self.__Refresh()

    def __Refresh(self):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        # GetAllReservationsToday returns: (URID, Title, ReservationDate, Quantity, UStaID, Forename, Surname, ClassCode)
        Results = self.__controller.GetLM().GetAllReservationsToday()
        if isinstance(Results, list):
            for Row in Results:
                StaffName = f"{Row[5]} {Row[6]}"
                self.__Table.insert("", "end", values=(Row[0], Row[1], Row[3], StaffName, Row[7]))
            self.__InfoText.config(text=f"{len(Results)} reservation(s) for today.\n\nCopy allocation and notification emails are processed automatically at login via the StartUp routine.")
        else:
            self.__InfoText.config(text=str(Results))


class MyReservationsTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        TableFrame.grid_rowconfigure(0, weight=1)
        TableFrame.grid_columnconfigure(0, weight=1)

        Columns = ("Res. ID", "Book Title", "Date", "Qty", "Location")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Res. ID", width=60)
        self.__Table.column("Book Title", width=180)
        self.__Table.column("Date", width=100)
        self.__Table.column("Qty", width=40)
        self.__Table.column("Location", width=100)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=0, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="My Reservations", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Your reservations are shown here.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

    def OnShow(self):
        self.__Refresh()

    def __Refresh(self):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        CurrentUser = self.__controller.GetAM().GetCurrentUser()
        if CurrentUser is None:
            return
        # GetAllReservationsByStaff returns: (URID, Title, ReservationDate, Quantity, UStaID, Forename, Surname, ClassCode)
        Results = self.__controller.GetLM().GetAllReservationsByStaff(CurrentUser)
        if isinstance(Results, list):
            for Row in Results:
                self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], Row[7]))
            self.__DetailsText.config(text=f"You have {len(Results)} reservation(s).")
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        URID = Values[0]
        Details = self.__controller.GetLM().GetReservationDetails(URID)
        if isinstance(Details, tuple):
            Text = f"Reservation ID: {Details[0]}\nBook: {Details[1]}\nDate: {Details[2]}\nQuantity: {Details[3]}\nLocation: {Details[7]}"
            self.__DetailsText.config(text=Text)