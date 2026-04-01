import tkinter as tk
from tkinter import ttk, messagebox

class SysAdminFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Sub-navigation tabs ---
        TabBar = tk.Frame(self, bg="#f0f4f8")
        TabBar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self.__Tabs = {}
        for Label, Tab in [("Staff Management", StaffMgmtTab), ("Email Config", EmailConfigTab)]:
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
        for Label, TabClass in [("Staff Management", StaffMgmtTab), ("Email Config", EmailConfigTab)]:
            Frame = TabClass(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[TabClass] = Frame

        self.__ActiveTabClass = StaffMgmtTab
        self.__ShowTab(StaffMgmtTab, "Staff Management")

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


# --- Staff Management Tab (SysAdmin) ---
# View All, Add, Remove, Promote, Demote
class StaffMgmtTab(tk.Frame):
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

        Columns = ("ID", "Forename", "Surname", "Access Level", "Active", "Email")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("ID", width=50)
        self.__Table.column("Forename", width=100)
        self.__Table.column("Surname", width=100)
        self.__Table.column("Access Level", width=90)
        self.__Table.column("Active", width=50)
        self.__Table.column("Email", width=160)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Staff Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a staff member.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Staff", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Staff", command=self.__RemoveStaff).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Promote", command=self.__PromoteStaff).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Demote", command=self.__DemoteStaff).pack(side="left", padx=(0, 8))

        # --- Inline add staff form ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__AddForm.grid_remove()
        tk.Label(self.__AddForm, text="Add Staff", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=10, sticky="w", pady=(0, 8))
        tk.Label(self.__AddForm, text="Forename", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__AddForename = ttk.Entry(self.__AddForm, width=12, font=("Arial", 10))
        self.__AddForename.grid(row=1, column=1, padx=(0, 8))
        tk.Label(self.__AddForm, text="Surname", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(8, 4))
        self.__AddSurname = ttk.Entry(self.__AddForm, width=12, font=("Arial", 10))
        self.__AddSurname.grid(row=1, column=3, padx=(0, 8))
        tk.Label(self.__AddForm, text="Password", font=("Arial", 10), bg="white").grid(row=1, column=4, sticky="e", padx=(8, 4))
        self.__AddPassword = ttk.Entry(self.__AddForm, width=12, font=("Arial", 10), show="*")
        self.__AddPassword.grid(row=1, column=5, padx=(0, 8))
        tk.Label(self.__AddForm, text="Access Level", font=("Arial", 10), bg="white").grid(row=1, column=6, sticky="e", padx=(8, 4))
        self.__AddAccessLevel = ttk.Combobox(self.__AddForm, values=["Teacher", "Admin", "SysAdmin"], width=10, font=("Arial", 10), state="readonly")
        self.__AddAccessLevel.set("Teacher")
        self.__AddAccessLevel.grid(row=1, column=7, padx=(0, 8))
        tk.Label(self.__AddForm, text="Email", font=("Arial", 10), bg="white").grid(row=1, column=8, sticky="e", padx=(8, 4))
        self.__AddEmail = ttk.Entry(self.__AddForm, width=18, font=("Arial", 10))
        self.__AddEmail.grid(row=1, column=9, padx=(0, 10))
        self.__AddFormError = tk.Label(self.__AddForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__AddFormError.grid(row=2, column=0, columnspan=10, pady=(8, 0))
        ttk.Button(self.__AddForm, text="Submit", command=self.__SubmitAdd).grid(row=3, column=0, pady=8)
        ttk.Button(self.__AddForm, text="Cancel", command=self.__HideAddForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        # GetAllStaff requires SysAdmin
        Results = self.__controller.GetAM().GetAllStaff()
        self.__PopulateTable(Results)

    def __Search(self):
        Results = self.__controller.GetAM().SearchStaff(self.__SearchEntry.get())
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                if len(Row) >= 6:
                    ActiveStr = "Yes" if Row[4] else "No"
                    EmailStr = Row[5] if Row[5] else ""
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], ActiveStr, EmailStr))
                elif len(Row) == 3:
                    Details = self.__controller.GetAM().GetStaffDetails(Row[0])
                    if isinstance(Details, tuple):
                        ActiveStr = "Yes" if Details[4] else "No"
                        EmailStr = Details[5] if Details[5] else ""
                        self.__Table.insert("", "end", values=(Details[0], Details[1], Details[2], Details[3], ActiveStr, EmailStr))
                    else:
                        self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], "", "", ""))
        else:
            self.__DetailsText.config(text=str(Results))

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected: return
        Values = self.__Table.item(Selected, "values")
        if not Values: return
        Details = self.__controller.GetAM().GetStaffDetails(Values[0])
        if isinstance(Details, tuple):
            ActiveStr = "Yes" if Details[4] else "No"
            EmailStr = Details[5] if Details[5] else "Not set"
            Text = f"ID: {Details[0]}\nName: {Details[1]} {Details[2]}\nAccess Level: {Details[3]}\nActive: {ActiveStr}\nEmail: {EmailStr}"
            self.__DetailsText.config(text=Text)
        elif isinstance(Details, str):
            self.__DetailsText.config(text=Details)

    # --- Add staff ---
    def __ShowAddForm(self):
        self.__AddForm.grid()
    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        for E in (self.__AddForename, self.__AddSurname, self.__AddPassword, self.__AddEmail):
            E.delete(0, "end")
        self.__AddAccessLevel.set("Teacher")
    def __SubmitAdd(self):
        Forename = self.__AddForename.get().strip()
        Surname = self.__AddSurname.get().strip()
        Password = self.__AddPassword.get()
        AccessLevel = self.__AddAccessLevel.get()
        Email = self.__AddEmail.get().strip() or None
        if not Forename or not Surname or not Password:
            self.__AddFormError.config(text="Forename, Surname, and Password are required.")
            return
        Result = self.__controller.GetAM().AddStaff(Password, Forename, Surname, AccessLevel, Email)
        if "successfully" in str(Result):
            self.__HideAddForm()
            self.__ShowAll()
        else: self.__AddFormError.config(text=str(Result))

    # --- Remove staff ---
    def __RemoveStaff(self):
        Selected = self.__Table.focus()
        if not Selected: return
        ID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove staff member {ID}?"):
            Result = self.__controller.GetAM().RemoveStaff(int(ID))
            if "successfully" in str(Result):
                self.__ShowAll()
                self.__DetailsText.config(text="Select a staff member.")
            else: messagebox.showerror("Error", str(Result))

    # --- Promote / Demote ---
    def __PromoteStaff(self):
        Selected = self.__Table.focus()
        if not Selected: return
        ID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Promote staff member {ID}?"):
            Result = self.__controller.GetAM().PromoteStaff(int(ID))
            if "successfully" in str(Result).lower() or "promoted" in str(Result).lower():
                self.__ShowAll()
            else: messagebox.showerror("Error", str(Result))

    def __DemoteStaff(self):
        Selected = self.__Table.focus()
        if not Selected: return
        ID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Demote staff member {ID}?"):
            Result = self.__controller.GetAM().DemoteStaff(int(ID))
            if "successfully" in str(Result).lower() or "demoted" in str(Result).lower():
                self.__ShowAll()
            else: messagebox.showerror("Error", str(Result))


# --- Email Config Tab (SysAdmin) ---
# Update SMTP Settings, Update Any Staff Email
class EmailConfigTab(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.__controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ContentFrame = tk.Frame(self, bg="#f0f4f8")
        ContentFrame.grid(row=0, column=0, sticky="nsew")

        # --- SMTP Settings section ---
        SMTPFrame = tk.LabelFrame(ContentFrame, text="SMTP Email Settings", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        SMTPFrame.pack(fill="x", pady=(0, 15))
        tk.Label(SMTPFrame, text="Configure the SMTP server used for sending email notifications.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        SMTPFields = [("Host", 1, 0), ("Port", 1, 2), ("Username", 2, 0), ("Password", 2, 2), ("Sender Address", 3, 0)]
        self.__SMTPEntries = {}
        for Field, Row, Col in SMTPFields:
            tk.Label(SMTPFrame, text=Field, font=("Arial", 10), bg="white").grid(row=Row, column=Col, sticky="e", padx=(10, 4), pady=4)
            ShowChar = "*" if Field == "Password" else None
            Entry = ttk.Entry(SMTPFrame, width=25, font=("Arial", 10), show=ShowChar if ShowChar else "")
            Entry.grid(row=Row, column=Col + 1, padx=(0, 10), pady=4)
            self.__SMTPEntries[Field] = Entry

        self.__SMTPError = tk.Label(SMTPFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__SMTPError.grid(row=4, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(SMTPFrame, text="Save SMTP Settings", command=self.__SaveSMTP).grid(row=5, column=0, pady=8)

        # --- Update Staff Email section ---
        EmailFrame = tk.LabelFrame(ContentFrame, text="Update Staff Email", font=("Arial", 11, "bold"), bg="white", padx=15, pady=10)
        EmailFrame.pack(fill="x", pady=(0, 15))
        tk.Label(EmailFrame, text="SysAdmins can update any staff member's email address.", font=("Arial", 10), bg="white", justify="left").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(EmailFrame, text="Staff ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4), pady=4)
        self.__StaffEmailIDEntry = ttk.Entry(EmailFrame, width=10, font=("Arial", 10))
        self.__StaffEmailIDEntry.grid(row=1, column=1, padx=(0, 10), pady=4)
        tk.Label(EmailFrame, text="New Email", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4), pady=4)
        self.__StaffEmailEntry = ttk.Entry(EmailFrame, width=25, font=("Arial", 10))
        self.__StaffEmailEntry.grid(row=1, column=3, padx=(0, 10), pady=4)
        ttk.Button(EmailFrame, text="Update Email", command=self.__UpdateStaffEmail).grid(row=2, column=0, pady=8)
        self.__StaffEmailError = tk.Label(EmailFrame, text="", fg="red", font=("Arial", 10), bg="white")
        self.__StaffEmailError.grid(row=2, column=1, columnspan=3, sticky="w")

    def OnShow(self):
        pass

    def __SaveSMTP(self):
        Host = self.__SMTPEntries["Host"].get().strip()
        Port = self.__SMTPEntries["Port"].get().strip()
        User = self.__SMTPEntries["Username"].get().strip()
        Password = self.__SMTPEntries["Password"].get()
        Sender = self.__SMTPEntries["Sender Address"].get().strip()
        if not Host or not Port:
            self.__SMTPError.config(text="Host and Port are required at minimum.")
            return
        Result = self.__controller.GetAM().UpdateSMTPSettings(Host, Port, User, Password, Sender)
        if "successfully" in str(Result):
            self.__SMTPError.config(text="")
            messagebox.showinfo("Success", str(Result))
        else:
            self.__SMTPError.config(text=str(Result))

    def __UpdateStaffEmail(self):
        IDStr = self.__StaffEmailIDEntry.get().strip()
        Email = self.__StaffEmailEntry.get().strip()
        if not IDStr or not Email:
            self.__StaffEmailError.config(text="Both fields are required.")
            return
        try: ID = int(IDStr)
        except ValueError:
            self.__StaffEmailError.config(text="Staff ID must be numeric.")
            return
        Result = self.__controller.GetAM().UpdateStaffEmail(ID, Email)
        if "successfully" in str(Result):
            self.__StaffEmailError.config(text="")
            self.__StaffEmailIDEntry.delete(0, "end")
            self.__StaffEmailEntry.delete(0, "end")
            messagebox.showinfo("Success", str(Result))
        else:
            self.__StaffEmailError.config(text=str(Result))