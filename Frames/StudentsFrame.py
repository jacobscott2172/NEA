import tkinter as tk
from tkinter import ttk, messagebox

class StudentsFrame(tk.Frame):
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
        for Label, Tab in [("All Students", AllStudentsTab), ("Student Loans", StudentLoansTab)]:
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
        for Label, TabClass in [("All Students", AllStudentsTab), ("Student Loans", StudentLoansTab)]:
            Frame = TabClass(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[TabClass] = Frame

        self.__ActiveTabClass = AllStudentsTab
        self.__ShowTab(AllStudentsTab, "All Students")

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
        """Called by DashboardFrame when the main Students tab is selected"""
        if self.__controller.GetAM().GetCurrentUser() is not None:
            CurrentFrame = self.__TabFrames[self.__ActiveTabClass]
            if hasattr(CurrentFrame, "OnShow"):
                CurrentFrame.OnShow()


class AllStudentsTab(tk.Frame):
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

        Columns = ("ID", "Forename", "Surname", "Max Loans", "Active", "Entry Year")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("ID", width=50)
        self.__Table.column("Forename", width=100)
        self.__Table.column("Surname", width=100)
        self.__Table.column("Max Loans", width=70)
        self.__Table.column("Active", width=50)
        self.__Table.column("Entry Year", width=80)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Student Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a student to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Student", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Student", command=self.__RemoveStudent).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Active", command=lambda: self.__SetStatus(True)).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Inactive", command=lambda: self.__SetStatus(False)).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Email", command=self.__ShowUpdateEmailForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Max Loans", command=self.__ShowUpdateMaxLoansForm).pack(side="left", padx=(0, 8))

        # --- Inline add form ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__AddForm.grid_remove()

        tk.Label(self.__AddForm, text="Add Student", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))
        tk.Label(self.__AddForm, text="Forename", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__AddForename = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AddForename.grid(row=1, column=1, padx=(0, 10))
        tk.Label(self.__AddForm, text="Surname", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__AddSurname = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AddSurname.grid(row=1, column=3, padx=(0, 10))
        tk.Label(self.__AddForm, text="Entry Year", font=("Arial", 10), bg="white").grid(row=1, column=4, sticky="e", padx=(10, 4))
        self.__AddEntryYear = ttk.Entry(self.__AddForm, width=10, font=("Arial", 10))
        self.__AddEntryYear.grid(row=1, column=5, padx=(0, 10))
        tk.Label(self.__AddForm, text="Email", font=("Arial", 10), bg="white").grid(row=1, column=6, sticky="e", padx=(10, 4))
        self.__AddEmail = ttk.Entry(self.__AddForm, width=20, font=("Arial", 10))
        self.__AddEmail.grid(row=1, column=7, padx=(0, 10))
        self.__AddFormError = tk.Label(self.__AddForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__AddFormError.grid(row=2, column=0, columnspan=8, pady=(8, 0))
        ttk.Button(self.__AddForm, text="Submit", command=self.__SubmitAdd).grid(row=3, column=0, pady=8)
        ttk.Button(self.__AddForm, text="Cancel", command=self.__HideAddForm).grid(row=3, column=1, pady=8)

        # --- Inline update email form ---
        self.__UpdateEmailForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__UpdateEmailForm.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__UpdateEmailForm.grid_remove()

        tk.Label(self.__UpdateEmailForm, text="Update Student Email", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__UpdateEmailForm, text="Student ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__UpdateEmailIDLabel = tk.Label(self.__UpdateEmailForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__UpdateEmailIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 10))
        tk.Label(self.__UpdateEmailForm, text="New Email", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__UpdateEmailEntry = ttk.Entry(self.__UpdateEmailForm, width=25, font=("Arial", 10))
        self.__UpdateEmailEntry.grid(row=1, column=3, padx=(0, 10))
        self.__UpdateEmailFormError = tk.Label(self.__UpdateEmailForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__UpdateEmailFormError.grid(row=2, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(self.__UpdateEmailForm, text="Submit", command=self.__SubmitUpdateEmail).grid(row=3, column=0, pady=8)
        ttk.Button(self.__UpdateEmailForm, text="Cancel", command=self.__HideUpdateEmailForm).grid(row=3, column=1, pady=8)

        # --- Inline update max loans form ---
        self.__UpdateMaxLoansForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__UpdateMaxLoansForm.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__UpdateMaxLoansForm.grid_remove()

        tk.Label(self.__UpdateMaxLoansForm, text="Update Max Loans", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__UpdateMaxLoansForm, text="Student ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__UpdateMaxLoansIDLabel = tk.Label(self.__UpdateMaxLoansForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__UpdateMaxLoansIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 10))
        tk.Label(self.__UpdateMaxLoansForm, text="New Max Loans", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__UpdateMaxLoansEntry = ttk.Entry(self.__UpdateMaxLoansForm, width=10, font=("Arial", 10))
        self.__UpdateMaxLoansEntry.grid(row=1, column=3, padx=(0, 10))
        self.__UpdateMaxLoansFormError = tk.Label(self.__UpdateMaxLoansForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__UpdateMaxLoansFormError.grid(row=2, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(self.__UpdateMaxLoansForm, text="Submit", command=self.__SubmitUpdateMaxLoans).grid(row=3, column=0, pady=8)
        ttk.Button(self.__UpdateMaxLoansForm, text="Cancel", command=self.__HideUpdateMaxLoansForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        # GetAllStudents returns: (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email)
        Results = self.__controller.GetAM().GetAllStudents()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        # SearchStudents returns: (UStuID, Forename, Surname)
        Results = self.__controller.GetAM().SearchStudents(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                if len(Row) >= 7:
                    # GetAllStudents format: (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email)
                    ActiveStr = "Yes" if Row[4] else "No"
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], ActiveStr, Row[5]))
                elif len(Row) == 3:
                    # SearchStudents format: (UStuID, Forename, Surname) - fetch full details for display
                    Details = self.__controller.GetAM().GetStudentDetails(Row[0])
                    if isinstance(Details, tuple):
                        ActiveStr = "Yes" if Details[4] else "No"
                        self.__Table.insert("", "end", values=(Details[0], Details[1], Details[2], Details[3], ActiveStr, Details[5]))
                    else:
                        # Fallback if details can't be retrieved
                        self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], "", "", ""))
        else:
            # String result - either error or not found message
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        StudentID = Values[0]
        # GetStudentDetails returns: (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email)
        Details = self.__controller.GetAM().GetStudentDetails(StudentID)
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[6] if Details[6] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nMax Loans: {Details[3]}\nActive: {ActiveStr}\nEntry Year: {Details[5]}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)

    # --- Helper to hide all inline forms ---
    def __HideAllForms(self):
        self.__HideAddForm()
        self.__HideUpdateEmailForm()
        self.__HideUpdateMaxLoansForm()

    # --- Add student (Admin) ---
    def __ShowAddForm(self):
        self.__HideAllForms()
        self.__AddForm.grid()

    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        self.__AddForename.delete(0, "end")
        self.__AddSurname.delete(0, "end")
        self.__AddEntryYear.delete(0, "end")
        self.__AddEmail.delete(0, "end")

    def __SubmitAdd(self):
        Forename = self.__AddForename.get().strip()
        Surname = self.__AddSurname.get().strip()
        EntryYearStr = self.__AddEntryYear.get().strip()
        Email = self.__AddEmail.get().strip() or None
        if not Forename or not Surname or not EntryYearStr:
            self.__AddFormError.config(text="Forename, Surname, and Entry Year are required.")
            return
        try:
            EntryYear = int(EntryYearStr)
        except ValueError:
            self.__AddFormError.config(text="Entry Year must be numeric.")
            return
        # AddStudent requires Admin permission
        Result = self.__controller.GetAM().AddStudent(Forename, Surname, EntryYear, Email)
        if "successfully" in str(Result):
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=str(Result))

    # --- Remove student (Admin) ---
    def __RemoveStudent(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StudentID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove student with ID {StudentID}?"):
            # RemoveStudent requires Admin permission
            Result = self.__controller.GetAM().RemoveStudent(int(StudentID))
            if "successfully" in str(Result):
                self.__ShowAll()
                self.__DetailsText.config(text="Select a student to view details.")
            else:
                messagebox.showerror("Error", str(Result))

    # --- Set active / inactive (Admin) ---
    def __SetStatus(self, MakeActive):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StudentID = self.__Table.item(Selected, "values")[0]
        StatusStr = "Active" if MakeActive else "Inactive"
        if messagebox.askyesno("Confirm", f"Set student {StudentID} to {StatusStr}?"):
            # SetAccountStatus requires Admin permission - IsStaff=False for students
            Result = self.__controller.GetAM().SetAccountStatus(int(StudentID), False, MakeActive)
            if "changed" in str(Result).lower():
                self.__ShowAll()
            else:
                messagebox.showerror("Error", str(Result))

    # --- Update email (Admin) ---
    def __ShowUpdateEmailForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a student to update email.")
            return
        Values = self.__Table.item(Selected, "values")
        self.__HideAllForms()
        self.__UpdateEmailIDLabel.config(text=str(Values[0]))
        self.__UpdateEmailForm.grid()

    def __HideUpdateEmailForm(self):
        self.__UpdateEmailForm.grid_remove()
        self.__UpdateEmailFormError.config(text="")
        self.__UpdateEmailEntry.delete(0, "end")

    def __SubmitUpdateEmail(self):
        StudentID = self.__UpdateEmailIDLabel.cget("text")
        Email = self.__UpdateEmailEntry.get().strip()
        if not Email:
            self.__UpdateEmailFormError.config(text="Email cannot be empty.")
            return
        # UpdateStudentEmail requires Admin permission
        Result = self.__controller.GetAM().UpdateStudentEmail(int(StudentID), Email)
        if "successfully" in str(Result):
            self.__HideUpdateEmailForm()
            self.__ShowAll()
        else:
            self.__UpdateEmailFormError.config(text=str(Result))

    # --- Update max loans (Admin) ---
    def __ShowUpdateMaxLoansForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a student to update max loans.")
            return
        Values = self.__Table.item(Selected, "values")
        self.__HideAllForms()
        self.__UpdateMaxLoansIDLabel.config(text=str(Values[0]))
        self.__UpdateMaxLoansForm.grid()

    def __HideUpdateMaxLoansForm(self):
        self.__UpdateMaxLoansForm.grid_remove()
        self.__UpdateMaxLoansFormError.config(text="")
        self.__UpdateMaxLoansEntry.delete(0, "end")

    def __SubmitUpdateMaxLoans(self):
        StudentID = self.__UpdateMaxLoansIDLabel.cget("text")
        try:
            MaxLoans = int(self.__UpdateMaxLoansEntry.get())
        except ValueError:
            self.__UpdateMaxLoansFormError.config(text="Max Loans must be numeric.")
            return
        if MaxLoans < 1:
            self.__UpdateMaxLoansFormError.config(text="Max Loans must be at least 1.")
            return
        # UpdateStudentMaxLoans requires Admin permission
        Result = self.__controller.GetAM().UpdateStudentMaxLoans(int(StudentID), MaxLoans)
        if "changed" in str(Result).lower() or "max loans" in str(Result).lower():
            self.__HideUpdateMaxLoansForm()
            self.__ShowAll()
        else:
            self.__UpdateMaxLoansFormError.config(text=str(Result))


class StudentLoansTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Student ID entry ---
        SearchBar = tk.Frame(self, bg="#f0f4f8")
        SearchBar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(SearchBar, text="Student ID:", font=("Arial", 11), bg="#f0f4f8").pack(side="left")
        self.__StudentIDEntry = ttk.Entry(SearchBar, width=15, font=("Arial", 11))
        self.__StudentIDEntry.pack(side="left", padx=8)
        ttk.Button(SearchBar, text="View Loans", command=self.__ViewLoans).pack(side="left")

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=1, column=0, sticky="nsew")
        TableFrame.grid_rowconfigure(0, weight=1)
        TableFrame.grid_columnconfigure(0, weight=1)

        # GetAllLoansByStudent returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStaID, UCID, Forename, Surname)
        Columns = ("Loan ID", "Title", "Copy ID", "Loan Date", "Due Date", "Return Date")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Loan ID", width=70)
        self.__Table.column("Title", width=180)
        self.__Table.column("Copy ID", width=70)
        self.__Table.column("Loan Date", width=100)
        self.__Table.column("Due Date", width=100)
        self.__Table.column("Return Date", width=100)
        self.__Table.grid(row=0, column=0, sticky="nsew")

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Info label ---
        self.__InfoLabel = tk.Label(self, text="Enter a Student ID to view their loan history.", font=("Arial", 10), bg="#f0f4f8", fg="grey")
        self.__InfoLabel.grid(row=2, column=0, sticky="w", pady=10)

    def OnShow(self):
        pass

    def __ViewLoans(self):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        try:
            StudentID = int(self.__StudentIDEntry.get())
        except ValueError:
            self.__InfoLabel.config(text="Student ID must be numeric.")
            return
        # GetAllLoansByStudent returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStaID, UCID, Forename, Surname)
        Results = self.__controller.GetLM().GetAllLoansByStudent(StudentID)
        if isinstance(Results, list):
            if len(Results) == 0:
                self.__InfoLabel.config(text=f"No loans found for student {StudentID}.")
            else:
                self.__InfoLabel.config(text=f"Showing {len(Results)} loan(s) for student {StudentID}.")
                for Row in Results:
                    ReturnDate = Row[4] if Row[4] else "Active"
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[6], Row[2], Row[3], ReturnDate))
        else:
            self.__InfoLabel.config(text=str(Results))