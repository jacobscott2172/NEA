import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class AdminFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Sub-navigation tabs ---
        TabBar = tk.Frame(self, bg="#f0f4f8")
        TabBar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self.__Tabs = {}
        for Label, Tab in [("Student Mgmt", StudentMgmtTab), ("Account Mgmt", AccountMgmtTab), ("Library Admin", LibraryAdminTab), ("Settings", SettingsTab)]:
            Btn = tk.Button(
                TabBar, text=Label, font=("Arial", 11),
                bg="#f0f4f8", fg="#1e293b", bd=0,
                activebackground="#1e293b", activeforeground="white",
                padx=15, pady=6,
                command=lambda T=Tab, B=Label: self.__ShowTab(T, B)
            )
            Btn.pack(side="left", padx=(0, 4))
            self.__Tabs[Label] = (Btn, Tab)

        self.__TabContainer = tk.Frame(self, bg="#f0f4f8")
        self.__TabContainer.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.__TabContainer.grid_rowconfigure(0, weight=1)
        self.__TabContainer.grid_columnconfigure(0, weight=1)

        self.__TabFrames = {}
        for Label, TabClass in [("Student Mgmt", StudentMgmtTab), ("Account Mgmt", AccountMgmtTab), ("Library Admin", LibraryAdminTab), ("Settings", SettingsTab)]:
            Frame = TabClass(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[TabClass] = Frame

        self.__ActiveTabClass = StudentMgmtTab
        self.__ShowTab(StudentMgmtTab, "Student Mgmt")

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


# --- Student Management Tab (Admin) ---
# Add, Remove, Set Active/Inactive, Update Email, Update Max Loans, Batch Import, Purge by Entry Year
class StudentMgmtTab(tk.Frame):
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
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a student.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Student", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Student", command=self.__RemoveStudent).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Active", command=lambda: self.__SetStatus(True)).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Inactive", command=lambda: self.__SetStatus(False)).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Email", command=self.__ShowUpdateEmailForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Max Loans", command=self.__ShowMaxLoansForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Batch Import", command=self.__BatchImport).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Purge by Year", command=self.__ShowPurgeForm).pack(side="left", padx=(0, 8))

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

        # --- Inline max loans form ---
        self.__MaxLoansForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__MaxLoansForm.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__MaxLoansForm.grid_remove()
        tk.Label(self.__MaxLoansForm, text="Update Max Loans", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__MaxLoansForm, text="Student ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__MaxLoansIDLabel = tk.Label(self.__MaxLoansForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__MaxLoansIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 10))
        tk.Label(self.__MaxLoansForm, text="New Max Loans", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__MaxLoansEntry = ttk.Entry(self.__MaxLoansForm, width=10, font=("Arial", 10))
        self.__MaxLoansEntry.grid(row=1, column=3, padx=(0, 10))
        self.__MaxLoansFormError = tk.Label(self.__MaxLoansForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__MaxLoansFormError.grid(row=2, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(self.__MaxLoansForm, text="Submit", command=self.__SubmitMaxLoans).grid(row=3, column=0, pady=8)
        ttk.Button(self.__MaxLoansForm, text="Cancel", command=self.__HideMaxLoansForm).grid(row=3, column=1, pady=8)

        # --- Inline purge by entry year form ---
        self.__PurgeForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__PurgeForm.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__PurgeForm.grid_remove()
        tk.Label(self.__PurgeForm, text="Purge Inactive Students by Entry Year", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(self.__PurgeForm, text="Entry Year", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__PurgeYearEntry = ttk.Entry(self.__PurgeForm, width=10, font=("Arial", 10))
        self.__PurgeYearEntry.grid(row=1, column=1, padx=(0, 10))
        self.__PurgeFormError = tk.Label(self.__PurgeForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__PurgeFormError.grid(row=2, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(self.__PurgeForm, text="Purge", command=self.__SubmitPurge).grid(row=3, column=0, pady=8)
        ttk.Button(self.__PurgeForm, text="Cancel", command=self.__HidePurgeForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetAM().GetAllStudents()
        self.__PopulateTable(Results)

    def __Search(self):
        Results = self.__controller.GetAM().SearchStudents(self.__SearchEntry.get())
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
        if not Selected: return
        Values = self.__Table.item(Selected, "values")
        if not Values: return
        Details = self.__controller.GetAM().GetStudentDetails(Values[0])
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[6] if Details[6] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nMax Loans: {Details[3]}\nActive: {ActiveStr}\nEntry Year: {Details[5]}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)

    def __HideAllForms(self):
        self.__HideAddForm()
        self.__HideUpdateEmailForm()
        self.__HideMaxLoansForm()
        self.__HidePurgeForm()

    # --- Add student ---
    def __ShowAddForm(self):
        self.__HideAllForms()
        self.__AddForm.grid()
    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        for E in (self.__AddForename, self.__AddSurname, self.__AddEntryYear, self.__AddEmail):
            E.delete(0, "end")
    def __SubmitAdd(self):
        Forename = self.__AddForename.get().strip()
        Surname = self.__AddSurname.get().strip()
        YearStr = self.__AddEntryYear.get().strip()
        Email = self.__AddEmail.get().strip() or None
        if not Forename or not Surname or not YearStr:
            self.__AddFormError.config(text="Forename, Surname, and Entry Year are required.")
            return
        try: EntryYear = int(YearStr)
        except ValueError:
            self.__AddFormError.config(text="Entry Year must be numeric.")
            return
        Result = self.__controller.GetAM().AddStudent(Forename, Surname, EntryYear, Email)
        if "successfully" in str(Result):
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=str(Result))

    # --- Remove student ---
    def __RemoveStudent(self):
        Selected = self.__Table.focus()
        if not Selected: return
        ID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove student {ID}?"):
            Result = self.__controller.GetAM().RemoveStudent(int(ID))
            if "successfully" in str(Result):
                self.__ShowAll()
                self.__DetailsText.config(text="Select a student.")
            else: messagebox.showerror("Error", str(Result))

    # --- Set active / inactive ---
    def __SetStatus(self, MakeActive):
        Selected = self.__Table.focus()
        if not Selected: return
        ID = self.__Table.item(Selected, "values")[0]
        StatusStr = "Active" if MakeActive else "Inactive"
        if messagebox.askyesno("Confirm", f"Set student {ID} to {StatusStr}?"):
            Result = self.__controller.GetAM().SetAccountStatus(int(ID), False, MakeActive)
            if "changed" in str(Result).lower():
                self.__ShowAll()
            else: messagebox.showerror("Error", str(Result))

    # --- Update email ---
    def __ShowUpdateEmailForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a student to update email.")
            return
        self.__HideAllForms()
        self.__UpdateEmailIDLabel.config(text=str(self.__Table.item(Selected, "values")[0]))
        self.__UpdateEmailForm.grid()
    def __HideUpdateEmailForm(self):
        self.__UpdateEmailForm.grid_remove()
        self.__UpdateEmailFormError.config(text="")
        self.__UpdateEmailEntry.delete(0, "end")
    def __SubmitUpdateEmail(self):
        Email = self.__UpdateEmailEntry.get().strip()
        if not Email:
            self.__UpdateEmailFormError.config(text="Email cannot be empty.")
            return
        Result = self.__controller.GetAM().UpdateStudentEmail(int(self.__UpdateEmailIDLabel.cget("text")), Email)
        if "successfully" in str(Result):
            self.__HideUpdateEmailForm()
            self.__ShowAll()
        else: self.__UpdateEmailFormError.config(text=str(Result))

    # --- Update max loans ---
    def __ShowMaxLoansForm(self):
        Selected = self.__Table.focus()
        if not Selected:
            messagebox.showinfo("Info", "Select a student to update max loans.")
            return
        self.__HideAllForms()
        self.__MaxLoansIDLabel.config(text=str(self.__Table.item(Selected, "values")[0]))
        self.__MaxLoansForm.grid()
    def __HideMaxLoansForm(self):
        self.__MaxLoansForm.grid_remove()
        self.__MaxLoansFormError.config(text="")
        self.__MaxLoansEntry.delete(0, "end")
    def __SubmitMaxLoans(self):
        try: MaxLoans = int(self.__MaxLoansEntry.get())
        except ValueError:
            self.__MaxLoansFormError.config(text="Must be numeric.")
            return
        if MaxLoans < 1:
            self.__MaxLoansFormError.config(text="Must be at least 1.")
            return
        Result = self.__controller.GetAM().UpdateStudentMaxLoans(int(self.__MaxLoansIDLabel.cget("text")), MaxLoans)
        if "changed" in str(Result).lower() or "max loans" in str(Result).lower():
            self.__HideMaxLoansForm()
            self.__ShowAll()
        else: self.__MaxLoansFormError.config(text=str(Result))

    # --- Batch import ---
    def __BatchImport(self):
        FilePath = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")])
        if not FilePath: return
        Result = self.__controller.GetAM().BatchImportStudents(FilePath)
        messagebox.showinfo("Batch Import", str(Result))
        self.__ShowAll()

    # --- Purge by entry year ---
    def __ShowPurgeForm(self):
        self.__HideAllForms()
        self.__PurgeForm.grid()
    def __HidePurgeForm(self):
        self.__PurgeForm.grid_remove()
        self.__PurgeFormError.config(text="")
        self.__PurgeYearEntry.delete(0, "end")
    def __SubmitPurge(self):
        try: Year = int(self.__PurgeYearEntry.get())
        except ValueError:
            self.__PurgeFormError.config(text="Entry Year must be numeric.")
            return
        if messagebox.askyesno("Confirm", f"Purge all inactive students from entry year {Year}?\nStudents with outstanding loans will be protected."):
            Result = self.__controller.GetAM().PurgeStudentsByEntryYear(Year)
            messagebox.showinfo("Purge", str(Result))
            self.__HidePurgeForm()
            self.__ShowAll()


# --- Account Management Tab (Admin) ---
# Change Password, Set Staff Active/Inactive, Purge Old Accounts
class AccountMgmtTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ContentFrame = tk.Frame(self, bg="#f0f4f8")
        ContentFrame.grid(row=0, column=0, sticky="nsew")

        # --- Change Password section ---
        PasswordFrame = tk.LabelFrame(ContentFrame, text="Change Staff Password", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        PasswordFrame.pack(fill="x", pady=(0, 15))
        tk.Label(PasswordFrame, text="Staff ID", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__PasswordIDEntry = ttk.Entry(PasswordFrame, width=10, font=("Arial", 10))
        self.__PasswordIDEntry.grid(row=0, column=1, padx=(0, 10), pady=4)
        tk.Label(PasswordFrame, text="New Password", font=("Arial", 10), bg="white").grid(row=0, column=2, sticky="e", padx=(10, 4), pady=4)
        self.__NewPasswordEntry = ttk.Entry(PasswordFrame, width=20, font=("Arial", 10), show="*")
        self.__NewPasswordEntry.grid(row=0, column=3, padx=(0, 10), pady=4)
        ttk.Button(PasswordFrame, text="Change Password", command=self.__ChangePassword).grid(row=0, column=4, padx=10, pady=4)
        self.__PasswordError = tk.Label(PasswordFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__PasswordError.grid(row=1, column=0, columnspan=5)

        # --- Set Staff Active/Inactive section ---
        StatusFrame = tk.LabelFrame(ContentFrame, text="Set Staff Account Status", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        StatusFrame.pack(fill="x", pady=(0, 15))
        tk.Label(StatusFrame, text="Staff ID", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__StatusIDEntry = ttk.Entry(StatusFrame, width=10, font=("Arial", 10))
        self.__StatusIDEntry.grid(row=0, column=1, padx=(0, 10), pady=4)
        ttk.Button(StatusFrame, text="Set Active", command=lambda: self.__SetStaffStatus(True)).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(StatusFrame, text="Set Inactive", command=lambda: self.__SetStaffStatus(False)).grid(row=0, column=3, padx=4, pady=4)
        self.__StatusError = tk.Label(StatusFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__StatusError.grid(row=1, column=0, columnspan=4)

        # --- Purge Old Accounts section ---
        PurgeFrame = tk.LabelFrame(ContentFrame, text="Purge Old Accounts", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        PurgeFrame.pack(fill="x", pady=(0, 15))
        tk.Label(PurgeFrame, text="Purges all inactive staff and student accounts older than the retention period.\nStudents with outstanding loans are protected.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Button(PurgeFrame, text="Purge Old Accounts", command=self.__PurgeOldAccounts).grid(row=1, column=0, pady=4)

    def OnShow(self):
        pass

    def __ChangePassword(self):
        IDStr = self.__PasswordIDEntry.get().strip()
        Password = self.__NewPasswordEntry.get()
        if not IDStr or not Password:
            self.__PasswordError.config(text="Both fields are required.")
            return
        try: ID = int(IDStr)
        except ValueError:
            self.__PasswordError.config(text="Staff ID must be numeric.")
            return
        Result = self.__controller.GetAM().ChangePassword(ID, Password)
        if "changed" in str(Result).lower():
            self.__PasswordError.config(text="")
            self.__PasswordIDEntry.delete(0, "end")
            self.__NewPasswordEntry.delete(0, "end")
            messagebox.showinfo("Success", "Password changed successfully.")
        else: self.__PasswordError.config(text=str(Result))

    def __SetStaffStatus(self, MakeActive):
        IDStr = self.__StatusIDEntry.get().strip()
        if not IDStr:
            self.__StatusError.config(text="Staff ID is required.")
            return
        try: ID = int(IDStr)
        except ValueError:
            self.__StatusError.config(text="Staff ID must be numeric.")
            return
        StatusStr = "Active" if MakeActive else "Inactive"
        if messagebox.askyesno("Confirm", f"Set staff member {ID} to {StatusStr}?"):
            Result = self.__controller.GetAM().SetAccountStatus(ID, True, MakeActive)
            if "changed" in str(Result).lower():
                self.__StatusError.config(text="")
                messagebox.showinfo("Success", f"Staff member {ID} set to {StatusStr}.")
            else: self.__StatusError.config(text=str(Result))

    def __PurgeOldAccounts(self):
        if messagebox.askyesno("Confirm", "Purge all inactive accounts older than the retention period?\nStudents with outstanding loans will be protected."):
            Result = self.__controller.GetAM().PurgeOldAccounts()
            messagebox.showinfo("Purge", str(Result))


# --- Library Admin Tab (Admin) ---
# Delete Loan, Clear Old Loans, Clear Old Reservations, Add/Remove Locations
class LibraryAdminTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ContentFrame = tk.Frame(self, bg="#f0f4f8")
        ContentFrame.grid(row=0, column=0, sticky="nsew")

        # --- Delete Loan section ---
        LoanFrame = tk.LabelFrame(ContentFrame, text="Delete Loan Record", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        LoanFrame.pack(fill="x", pady=(0, 15))
        tk.Label(LoanFrame, text="If the loan is still active, the copy location is reset to its home.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(LoanFrame, text="Loan ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__DeleteLoanIDEntry = ttk.Entry(LoanFrame, width=10, font=("Arial", 10))
        self.__DeleteLoanIDEntry.grid(row=1, column=1, padx=(0, 10), pady=4)
        ttk.Button(LoanFrame, text="Delete Loan", command=self.__DeleteLoan).grid(row=1, column=2, padx=10, pady=4)
        self.__DeleteLoanError = tk.Label(LoanFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__DeleteLoanError.grid(row=2, column=0, columnspan=3)

        # --- Clear Old Records section ---
        ClearFrame = tk.LabelFrame(ContentFrame, text="Clear Old Records", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        ClearFrame.pack(fill="x", pady=(0, 15))
        tk.Label(ClearFrame, text="Removes returned loans and past reservations older than the retention period.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Button(ClearFrame, text="Clear Old Loans", command=self.__ClearOldLoans).grid(row=1, column=0, padx=(0, 8), pady=4)
        ttk.Button(ClearFrame, text="Clear Old Reservations", command=self.__ClearOldReservations).grid(row=1, column=1, padx=(0, 8), pady=4)

        # --- Add/Remove Locations section ---
        LocFrame = tk.LabelFrame(ContentFrame, text="Manage Locations", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        LocFrame.pack(fill="x", pady=(0, 15))
        tk.Label(LocFrame, text="Add Location - Class Code", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__AddLocEntry = ttk.Entry(LocFrame, width=15, font=("Arial", 10))
        self.__AddLocEntry.grid(row=0, column=1, padx=(0, 10), pady=4)
        ttk.Button(LocFrame, text="Add", command=self.__AddLocation).grid(row=0, column=2, padx=4, pady=4)
        tk.Label(LocFrame, text="Remove Location - ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__RemoveLocEntry = ttk.Entry(LocFrame, width=10, font=("Arial", 10))
        self.__RemoveLocEntry.grid(row=1, column=1, padx=(0, 10), pady=4)
        ttk.Button(LocFrame, text="Remove", command=self.__RemoveLocation).grid(row=1, column=2, padx=4, pady=4)
        self.__LocError = tk.Label(LocFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__LocError.grid(row=2, column=0, columnspan=3)

    def OnShow(self):
        pass

    def __DeleteLoan(self):
        IDStr = self.__DeleteLoanIDEntry.get().strip()
        if not IDStr:
            self.__DeleteLoanError.config(text="Loan ID is required.")
            return
        try: ID = int(IDStr)
        except ValueError:
            self.__DeleteLoanError.config(text="Loan ID must be numeric.")
            return
        if messagebox.askyesno("Confirm", f"Delete loan record {ID}?"):
            Result = self.__controller.GetLM().DeleteLoan(ID)
            if "successfully" in str(Result):
                self.__DeleteLoanError.config(text="")
                self.__DeleteLoanIDEntry.delete(0, "end")
                messagebox.showinfo("Success", str(Result))
            else: self.__DeleteLoanError.config(text=str(Result))

    def __ClearOldLoans(self):
        if messagebox.askyesno("Confirm", "Clear all returned loans older than the retention period?"):
            Result = self.__controller.GetLM().ClearOldLoans()
            messagebox.showinfo("Result", str(Result))

    def __ClearOldReservations(self):
        if messagebox.askyesno("Confirm", "Clear all reservations older than the retention period?"):
            Result = self.__controller.GetLM().ClearOldReservations()
            messagebox.showinfo("Result", str(Result))

    def __AddLocation(self):
        ClassCode = self.__AddLocEntry.get().strip()
        if not ClassCode:
            self.__LocError.config(text="Class code cannot be empty.")
            return
        Result = self.__controller.GetLM().AddLocation(ClassCode)
        if "successfully" in str(Result):
            self.__LocError.config(text="")
            self.__AddLocEntry.delete(0, "end")
            messagebox.showinfo("Success", str(Result))
        else: self.__LocError.config(text=str(Result))

    def __RemoveLocation(self):
        IDStr = self.__RemoveLocEntry.get().strip()
        if not IDStr:
            self.__LocError.config(text="Location ID is required.")
            return
        try: ID = int(IDStr)
        except ValueError:
            self.__LocError.config(text="Location ID must be numeric.")
            return
        if messagebox.askyesno("Confirm", f"Remove location {ID}?"):
            Result = self.__controller.GetLM().RemoveLocation(ID)
            if "successfully" in str(Result):
                self.__LocError.config(text="")
                self.__RemoveLocEntry.delete(0, "end")
                messagebox.showinfo("Success", str(Result))
            else: self.__LocError.config(text=str(Result))


# --- Settings Tab (Admin) ---
# Update Default Max Loans, Update Default Loan Period
class SettingsTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ContentFrame = tk.Frame(self, bg="#f0f4f8")
        ContentFrame.grid(row=0, column=0, sticky="nsew")

        # --- Default Max Loans ---
        MaxLoansFrame = tk.LabelFrame(ContentFrame, text="Default Max Loans", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        MaxLoansFrame.pack(fill="x", pady=(0, 15))
        tk.Label(MaxLoansFrame, text="Sets the default maximum number of active loans for newly created student accounts.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(MaxLoansFrame, text="New Default", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__DefaultMaxLoansEntry = ttk.Entry(MaxLoansFrame, width=10, font=("Arial", 10))
        self.__DefaultMaxLoansEntry.grid(row=1, column=1, padx=(0, 10), pady=4)
        ttk.Button(MaxLoansFrame, text="Update", command=self.__UpdateDefaultMaxLoans).grid(row=1, column=2, padx=10, pady=4)
        self.__MaxLoansError = tk.Label(MaxLoansFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__MaxLoansError.grid(row=2, column=0, columnspan=3)

        # --- Default Loan Period ---
        LoanPeriodFrame = tk.LabelFrame(ContentFrame, text="Default Loan Period (Days)", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        LoanPeriodFrame.pack(fill="x", pady=(0, 15))
        tk.Label(LoanPeriodFrame, text="Sets the default number of days for new loans.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(LoanPeriodFrame, text="New Default (days)", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__DefaultLoanPeriodEntry = ttk.Entry(LoanPeriodFrame, width=10, font=("Arial", 10))
        self.__DefaultLoanPeriodEntry.grid(row=1, column=1, padx=(0, 10), pady=4)
        ttk.Button(LoanPeriodFrame, text="Update", command=self.__UpdateDefaultLoanPeriod).grid(row=1, column=2, padx=10, pady=4)
        self.__LoanPeriodError = tk.Label(LoanPeriodFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__LoanPeriodError.grid(row=2, column=0, columnspan=3)

    def OnShow(self):
        pass

    def __UpdateDefaultMaxLoans(self):
        try: Value = int(self.__DefaultMaxLoansEntry.get())
        except ValueError:
            self.__MaxLoansError.config(text="Must be numeric.")
            return
        if Value < 1:
            self.__MaxLoansError.config(text="Must be at least 1.")
            return
        Result = self.__controller.GetAM().UpdateDefaultMaxLoans(Value)
        if "changed" in str(Result).lower():
            self.__MaxLoansError.config(text="")
            self.__DefaultMaxLoansEntry.delete(0, "end")
            messagebox.showinfo("Success", str(Result))
        else: self.__MaxLoansError.config(text=str(Result))

    def __UpdateDefaultLoanPeriod(self):
        try: Value = int(self.__DefaultLoanPeriodEntry.get())
        except ValueError:
            self.__LoanPeriodError.config(text="Must be numeric.")
            return
        if Value < 1:
            self.__LoanPeriodError.config(text="Must be at least 1.")
            return
        Result = self.__controller.GetAM().UpdateDefaultLoanPeriod(Value)
        if "changed" in str(Result).lower():
            self.__LoanPeriodError.config(text="")
            self.__DefaultLoanPeriodEntry.delete(0, "end")
            messagebox.showinfo("Success", str(Result))
        else: self.__LoanPeriodError.config(text=str(Result))