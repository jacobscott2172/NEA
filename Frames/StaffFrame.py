import tkinter as tk
from tkinter import ttk

class StaffFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # --- Search bar ---
        SearchBar = tk.Frame(self, bg="#f0f4f8")
        SearchBar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        tk.Label(SearchBar, text="Search:", font=("Arial", 11), bg="#f0f4f8").pack(side="left")
        self.__SearchEntry = ttk.Entry(SearchBar, width=30, font=("Arial", 11))
        self.__SearchEntry.pack(side="left", padx=8)
        ttk.Button(SearchBar, text="Search", command=self.__Search).pack(side="left")
        ttk.Button(SearchBar, text="View My Details", command=self.__ViewOwnDetails).pack(side="left", padx=8)

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=1, column=0, sticky="nsew", padx=(20, 10))
        TableFrame.grid_rowconfigure(0, weight=1)
        TableFrame.grid_columnconfigure(0, weight=1)

        Columns = ("ID", "Forename", "Surname")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("ID", width=50)
        self.__Table.column("Forename", width=120)
        self.__Table.column("Surname", width=120)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew", padx=(0, 20))
        tk.Label(self.__DetailsPanel, text="Staff Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Use search to find staff, or click View My Details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons (Teacher level only) ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        ttk.Button(ActionBar, text="Update My Email", command=self.__ShowUpdateOwnEmailForm).pack(side="left", padx=(0, 8))

        # --- Inline update own email form ---
        self.__UpdateOwnEmailForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__UpdateOwnEmailForm.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.__UpdateOwnEmailForm.grid_remove()

        tk.Label(self.__UpdateOwnEmailForm, text="Update My Email", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(self.__UpdateOwnEmailForm, text="New Email", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__OwnEmailEntry = ttk.Entry(self.__UpdateOwnEmailForm, width=30, font=("Arial", 10))
        self.__OwnEmailEntry.grid(row=1, column=1, padx=(0, 10))
        self.__UpdateOwnEmailFormError = tk.Label(self.__UpdateOwnEmailForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__UpdateOwnEmailFormError.grid(row=2, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(self.__UpdateOwnEmailForm, text="Submit", command=self.__SubmitUpdateOwnEmail).grid(row=3, column=0, pady=8)
        ttk.Button(self.__UpdateOwnEmailForm, text="Cancel", command=self.__HideUpdateOwnEmailForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ViewOwnDetails()

    def __Search(self):
        Term = self.__SearchEntry.get()
        # SearchStaff returns: (UStaID, Forename, Surname) - requires Teacher
        Results = self.__controller.GetAM().SearchStaff(Term)
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2]))
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        # GetStaffDetails - Teachers can only view their own; Admins can view any
        Details = self.__controller.GetAM().GetStaffDetails(Values[0])
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[5] if Details[5] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nAccess Level: {Details[3]}\nActive: {ActiveStr}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)

    def __ViewOwnDetails(self):
        CurrentID = self.__controller.GetAM().GetCurrentUser()
        if CurrentID is None:
            return
        Details = self.__controller.GetAM().GetStaffDetails(CurrentID)
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[5] if Details[5] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nAccess Level: {Details[3]}\nActive: {ActiveStr}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)

    # --- Update own email (Teacher - can update own) ---
    def __ShowUpdateOwnEmailForm(self):
        self.__UpdateOwnEmailForm.grid()

    def __HideUpdateOwnEmailForm(self):
        self.__UpdateOwnEmailForm.grid_remove()
        self.__UpdateOwnEmailFormError.config(text="")
        self.__OwnEmailEntry.delete(0, "end")

    def __SubmitUpdateOwnEmail(self):
        Email = self.__OwnEmailEntry.get().strip()
        if not Email:
            self.__UpdateOwnEmailFormError.config(text="Email cannot be empty.")
            return
        CurrentID = self.__controller.GetAM().GetCurrentUser()
        # UpdateStaffEmail allows Teachers to update their own email
        Result = self.__controller.GetAM().UpdateStaffEmail(CurrentID, Email)
        if "successfully" in str(Result):
            self.__HideUpdateOwnEmailForm()
            self.__ViewOwnDetails()
        else:
            self.__UpdateOwnEmailFormError.config(text=str(Result))