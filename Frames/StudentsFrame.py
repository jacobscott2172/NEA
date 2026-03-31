import tkinter as tk
from tkinter import ttk

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
        if self.__controller.GetAM().GetCurrentUser() is not None:
            if hasattr(self.__TabFrames[TabClass], "OnShow"):
                self.__TabFrames[TabClass].OnShow()

    def OnShow(self):
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

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetAM().GetAllStudents()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        Results = self.__controller.GetAM().SearchStudents(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                if len(Row) >= 7:
                    ActiveStr = "Yes" if Row[4] else "No"
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], ActiveStr, Row[5]))
                elif len(Row) == 3:
                    Details = self.__controller.GetAM().GetStudentDetails(Row[0])
                    if isinstance(Details, tuple):
                        ActiveStr = "Yes" if Details[4] else "No"
                        self.__Table.insert("", "end", values=(Details[0], Details[1], Details[2], Details[3], ActiveStr, Details[5]))
                    else:
                        self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], "", "", ""))
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        Details = self.__controller.GetAM().GetStudentDetails(Values[0])
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[6] if Details[6] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nMax Loans: {Details[3]}\nActive: {ActiveStr}\nEntry Year: {Details[5]}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)


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