import tkinter as tk
from tkinter import ttk, messagebox

class LoansFrame(tk.Frame):
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
        for Label, Tab in [("Active Loans", ActiveLoansTab), ("All Loans", AllLoansTab), ("Overdue Loans", OverdueLoansTab)]:
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
        for Label, TabClass in [("Active Loans", ActiveLoansTab), ("All Loans", AllLoansTab), ("Overdue Loans", OverdueLoansTab)]:
            Frame = TabClass(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[TabClass] = Frame

        self.__ActiveTabClass = ActiveLoansTab
        self.__ShowTab(ActiveLoansTab, "Active Loans")

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
        """Called by DashboardFrame when the main Loans tab is selected"""
        if self.__controller.GetAM().GetCurrentUser() is not None:
            CurrentFrame = self.__TabFrames[self.__ActiveTabClass]
            if hasattr(CurrentFrame, "OnShow"):
                CurrentFrame.OnShow()


class ActiveLoansTab(tk.Frame):
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

        Columns = ("Loan ID", "Book Title", "Copy ID", "Student", "Due Date")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Loan ID", width=70)
        self.__Table.column("Book Title", width=180)
        self.__Table.column("Copy ID", width=70)
        self.__Table.column("Student", width=150)
        self.__Table.column("Due Date", width=100)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Loan Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a loan to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Issue Loan", command=self.__ShowIssueForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Return Loan", command=self.__ReturnLoan).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Extend Loan", command=self.__ShowExtendForm).pack(side="left", padx=(0, 8))

        # --- Inline issue form ---
        self.__IssueForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__IssueForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__IssueForm.grid_remove()

        tk.Label(self.__IssueForm, text="Issue Loan", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__IssueForm, text="Copy ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__IssueCopyID = ttk.Entry(self.__IssueForm, width=15, font=("Arial", 10))
        self.__IssueCopyID.grid(row=1, column=1, padx=(0, 10))
        tk.Label(self.__IssueForm, text="Student ID", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__IssueStudentID = ttk.Entry(self.__IssueForm, width=15, font=("Arial", 10))
        self.__IssueStudentID.grid(row=1, column=3, padx=(0, 10))
        self.__IssueFormError = tk.Label(self.__IssueForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__IssueFormError.grid(row=2, column=0, columnspan=4)
        ttk.Button(self.__IssueForm, text="Submit", command=self.__SubmitIssue).grid(row=3, column=0, pady=8)
        ttk.Button(self.__IssueForm, text="Cancel", command=self.__HideIssueForm).grid(row=3, column=1, pady=8)

        # --- Inline extend form ---
        self.__ExtendForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__ExtendForm.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__ExtendForm.grid_remove()

        tk.Label(self.__ExtendForm, text="Extend Loan", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        tk.Label(self.__ExtendForm, text="Loan ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__ExtendLoanIDLabel = tk.Label(self.__ExtendForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__ExtendLoanIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 10))
        tk.Label(self.__ExtendForm, text="New Due Date", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__ExtendDateEntry = ttk.Entry(self.__ExtendForm, width=15, font=("Arial", 10))
        self.__ExtendDateEntry.grid(row=1, column=3, padx=(0, 10))
        tk.Label(self.__ExtendForm, text="(YYYYMMDD)", font=("Arial", 9), bg="white", fg="grey").grid(row=1, column=4, sticky="w")
        self.__ExtendFormError = tk.Label(self.__ExtendForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__ExtendFormError.grid(row=2, column=0, columnspan=6)
        ttk.Button(self.__ExtendForm, text="Submit", command=self.__SubmitExtend).grid(row=3, column=0, pady=8)
        ttk.Button(self.__ExtendForm, text="Cancel", command=self.__HideExtendForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        # GetAllActiveLoans returns: (ULoanID, Title, LoanDate, DueDate, UStuID, UStaID, UCID, Forename, Surname)
        Results = self.__controller.GetLM().GetAllActiveLoans()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        # SearchLoans returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStuID, UStaID, UCID, Forename, Surname)
        Results = self.__controller.GetLM().SearchLoans(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                if len(Row) == 10:
                    # SearchLoans format - filter to active only (ReturnDate at index 4 is None)
                    if Row[4] is not None:
                        continue
                    StudentName = f"{Row[8]} {Row[9]}"
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[7], StudentName, Row[3]))
                elif len(Row) == 9:
                    # GetAllActiveLoans format
                    StudentName = f"{Row[7]} {Row[8]}"
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[6], StudentName, Row[3]))
        else:
            # Display the error (like 'Access Denied') in the details text instead of crashing
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        # GetLoanDetails returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStuID, UStaID, UCID, Forename, Surname)
        Details = self.__controller.GetLM().GetLoanDetails(Values[0])
        if Details:
            Text = f"Loan ID: {Details[0]}\nTitle: {Details[1]}\nCopy ID: {Details[7]}\nStudent: {Details[8]} {Details[9]} (ID: {Details[5]})\nStaff ID: {Details[6]}\nLoan Date: {Details[2]}\nDue Date: {Details[3]}"
            self.__DetailsText.config(text=Text)

    # --- Helper to hide all inline forms ---
    def __HideAllForms(self):
        self.__HideIssueForm()
        self.__HideExtendForm()

    # --- Issue loan ---
    def __ShowIssueForm(self):
        self.__HideAllForms()
        self.__IssueForm.grid()

    def __HideIssueForm(self):
        self.__IssueForm.grid_remove()
        self.__IssueFormError.config(text="")
        self.__IssueCopyID.delete(0, "end")
        self.__IssueStudentID.delete(0, "end")

    def __SubmitIssue(self):
        try:
            CopyID = int(self.__IssueCopyID.get())
            StudentID = int(self.__IssueStudentID.get())
        except ValueError:
            self.__IssueFormError.config(text="IDs must be numeric.")
            return
        Result = self.__controller.GetLM().IssueLoan(CopyID, StudentID)
        if "successfully" in Result.lower():
            self.__HideIssueForm()
            self.__ShowAll()
        elif "loan limit" in Result.lower():
            # Student is at their MaxActiveLoans - prompt the teacher to override
            if messagebox.askyesno("Loan Limit Reached", f"{Result}\n\nDo you want to override and issue the loan anyway?"):
                # Override by calling IssueLoan with override flag
                OverrideResult = self.__controller.GetLM().IssueLoan(CopyID, StudentID, Override=True)
                if "successfully" in OverrideResult.lower():
                    self.__HideIssueForm()
                    self.__ShowAll()
                else:
                    self.__IssueFormError.config(text=OverrideResult)
        else:
            self.__IssueFormError.config(text=Result)

    # --- Return loan ---
    def __ReturnLoan(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        LoanID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Return Loan {LoanID}?"):
            Result = self.__controller.GetLM().ReturnLoan(int(LoanID))
            self.__ShowAll()
            messagebox.showinfo("Result", Result)

    # --- Extend loan ---
    def __ShowExtendForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a loan to extend.")
            return
        Values = self.__Table.item(Selected, "values")
        self.__HideAllForms()
        self.__ExtendLoanIDLabel.config(text=str(Values[0]))
        self.__ExtendForm.grid()

    def __HideExtendForm(self):
        self.__ExtendForm.grid_remove()
        self.__ExtendFormError.config(text="")
        self.__ExtendDateEntry.delete(0, "end")

    def __SubmitExtend(self):
        try:
            LoanID = int(self.__ExtendLoanIDLabel.cget("text"))
            NewDueDate = int(self.__ExtendDateEntry.get())
        except ValueError:
            self.__ExtendFormError.config(text="New due date must be numeric (YYYYMMDD).")
            return
        # Validate date format: must be 8 digits
        if len(str(NewDueDate)) != 8:
            self.__ExtendFormError.config(text="Date must be 8 digits (YYYYMMDD).")
            return
        Result = self.__controller.GetLM().ExtendLoan(LoanID, NewDueDate)
        if "extended" in Result.lower():
            self.__HideExtendForm()
            self.__ShowAll()
        else:
            self.__ExtendFormError.config(text=Result)


class AllLoansTab(tk.Frame):
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

        Columns = ("Loan ID", "Title", "Student", "Loan Date", "Due Date", "Return Date")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Loan ID", width=70)
        self.__Table.column("Title", width=160)
        self.__Table.column("Student", width=130)
        self.__Table.column("Loan Date", width=90)
        self.__Table.column("Due Date", width=90)
        self.__Table.column("Return Date", width=90)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Loan Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a loan to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        # GetAllLoans returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStuID, UStaID, UCID, Forename, Surname)
        Results = self.__controller.GetLM().GetAllLoans()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        # SearchLoans returns same 10-element format
        Results = self.__controller.GetLM().SearchLoans(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                # Both GetAllLoans and SearchLoans return 10-element tuples
                StudentName = f"{Row[8]} {Row[9]}"
                ReturnDate = Row[4] if Row[4] else "Active"
                self.__Table.insert("", "end", values=(Row[0], Row[1], StudentName, Row[2], Row[3], ReturnDate))
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        # GetLoanDetails returns: (ULoanID, Title, LoanDate, DueDate, ReturnDate, UStuID, UStaID, UCID, Forename, Surname)
        Details = self.__controller.GetLM().GetLoanDetails(Values[0])
        if Details:
            ReturnStr = Details[4] if Details[4] else "Active"
            Text = f"Loan ID: {Details[0]}\nTitle: {Details[1]}\nCopy ID: {Details[7]}\nStudent: {Details[8]} {Details[9]} (ID: {Details[5]})\nStaff ID: {Details[6]}\nLoan Date: {Details[2]}\nDue Date: {Details[3]}\nReturn Date: {ReturnStr}"
            self.__DetailsText.config(text=Text)


class OverdueLoansTab(tk.Frame):
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

        Columns = ("Loan ID", "Title", "Due Date", "Student", "Student ID")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("Loan ID", width=70)
        self.__Table.column("Title", width=180)
        self.__Table.column("Due Date", width=100)
        self.__Table.column("Student", width=150)
        self.__Table.column("Student ID", width=80)
        self.__Table.grid(row=0, column=0, sticky="nsew")

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=0, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Overdue Loans", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__InfoText = tk.Label(self.__DetailsPanel, text="Loans past their due date are shown here.\n\nOverdue notifications are sent automatically at login via the StartUp routine.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__InfoText.pack(anchor="w")

    def OnShow(self):
        self.__Refresh()

    def __Refresh(self):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        # GetOverdueLoans returns: (ULoanID, Title, DueDate, UStuID, Forename, Surname, Email) or a string
        Results = self.__controller.GetLM().GetOverdueLoans()
        if isinstance(Results, list):
            for Row in Results:
                StudentName = f"{Row[4]} {Row[5]}"
                self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], StudentName, Row[3]))
            self.__InfoText.config(text=f"{len(Results)} overdue loan(s) found.\n\nOverdue notifications are sent automatically at login via the StartUp routine.")
        else:
            # String result means either no overdue loans or an error
            self.__InfoText.config(text=str(Results))