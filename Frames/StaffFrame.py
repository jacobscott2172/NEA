import tkinter as tk
from tkinter import ttk, messagebox

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
        ttk.Button(SearchBar, text="Show All", command=self.__ShowAll).pack(side="left", padx=8)
        ttk.Button(SearchBar, text="View My Details", command=self.__ViewOwnDetails).pack(side="left", padx=8)

        # --- Results table ---
        TableFrame = tk.Frame(self, bg="#f0f4f8")
        TableFrame.grid(row=1, column=0, sticky="nsew", padx=(20, 10))
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
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew", padx=(0, 20))
        tk.Label(self.__DetailsPanel, text="Staff Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a staff member to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        # Teacher-level actions
        ttk.Button(ActionBar, text="Update My Email", command=self.__ShowUpdateOwnEmailForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Change Password", command=self.__ShowChangePasswordForm).pack(side="left", padx=(0, 8))
        # SysAdmin-level actions
        ttk.Button(ActionBar, text="Add Staff", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Staff", command=self.__RemoveStaff).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Promote", command=self.__PromoteStaff).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Demote", command=self.__DemoteStaff).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Active", command=lambda: self.__SetStatus(True)).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Set Inactive", command=lambda: self.__SetStatus(False)).pack(side="left", padx=(0, 8))

        # --- Inline add staff form ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
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

        # --- Inline update own email form ---
        self.__UpdateOwnEmailForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__UpdateOwnEmailForm.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.__UpdateOwnEmailForm.grid_remove()

        tk.Label(self.__UpdateOwnEmailForm, text="Update My Email", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(self.__UpdateOwnEmailForm, text="New Email", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__OwnEmailEntry = ttk.Entry(self.__UpdateOwnEmailForm, width=30, font=("Arial", 10))
        self.__OwnEmailEntry.grid(row=1, column=1, padx=(0, 10))
        self.__UpdateOwnEmailFormError = tk.Label(self.__UpdateOwnEmailForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__UpdateOwnEmailFormError.grid(row=2, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(self.__UpdateOwnEmailForm, text="Submit", command=self.__SubmitUpdateOwnEmail).grid(row=3, column=0, pady=8)
        ttk.Button(self.__UpdateOwnEmailForm, text="Cancel", command=self.__HideUpdateOwnEmailForm).grid(row=3, column=1, pady=8)

        # --- Inline change password form ---
        self.__ChangePasswordForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__ChangePasswordForm.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.__ChangePasswordForm.grid_remove()

        tk.Label(self.__ChangePasswordForm, text="Change Password", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__ChangePasswordForm, text="Staff ID", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10, 4))
        self.__ChangePasswordIDLabel = tk.Label(self.__ChangePasswordForm, text="", font=("Arial", 10, "bold"), bg="white")
        self.__ChangePasswordIDLabel.grid(row=1, column=1, sticky="w", padx=(0, 10))
        tk.Label(self.__ChangePasswordForm, text="New Password", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.__NewPasswordEntry = ttk.Entry(self.__ChangePasswordForm, width=20, font=("Arial", 10), show="*")
        self.__NewPasswordEntry.grid(row=1, column=3, padx=(0, 10))
        self.__ChangePasswordFormError = tk.Label(self.__ChangePasswordForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__ChangePasswordFormError.grid(row=2, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(self.__ChangePasswordForm, text="Submit", command=self.__SubmitChangePassword).grid(row=3, column=0, pady=8)
        ttk.Button(self.__ChangePasswordForm, text="Cancel", command=self.__HideChangePasswordForm).grid(row=3, column=1, pady=8)

    def OnShow(self):
        # Show own details by default
        self.__ViewOwnDetails()

    def __ShowAll(self):
        # GetAllStaff returns: (UStaID, Forename, Surname, AccessLevel, AccountActive, Email) - requires SysAdmin
        Results = self.__controller.GetAM().GetAllStaff()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        # SearchStaff returns: (UStaID, Forename, Surname) - requires Teacher
        Results = self.__controller.GetAM().SearchStaff(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                if len(Row) >= 6:
                    # GetAllStaff format: (UStaID, Forename, Surname, AccessLevel, AccountActive, Email)
                    ActiveStr = "Yes" if Row[4] else "No"
                    EmailStr = Row[5] if Row[5] else ""
                    self.__Table.insert("", "end", values=(Row[0], Row[1], Row[2], Row[3], ActiveStr, EmailStr))
                elif len(Row) == 3:
                    # SearchStaff format: (UStaID, Forename, Surname) - try to get full details
                    Details = self.__controller.GetAM().GetStaffDetails(Row[0])
                    if isinstance(Details, tuple):
                        ActiveStr = "Yes" if Details[4] else "No"
                        EmailStr = Details[5] if Details[5] else ""
                        self.__Table.insert("", "end", values=(Details[0], Details[1], Details[2], Details[3], ActiveStr, EmailStr))
                    else:
                        # Fallback - may not have permission to see full details
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
        StaffID = Values[0]
        # GetStaffDetails returns: (UStaID, Forename, Surname, AccessLevel, AccountActive, Email)
        # Teachers can only view their own details; Admins can view any
        Details = self.__controller.GetAM().GetStaffDetails(StaffID)
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

    # --- Helper to hide all inline forms ---
    def __HideAllForms(self):
        self.__HideAddForm()
        self.__HideUpdateOwnEmailForm()
        self.__HideChangePasswordForm()

    # --- Add staff (SysAdmin) ---
    def __ShowAddForm(self):
        self.__HideAllForms()
        self.__AddForm.grid()

    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        self.__AddForename.delete(0, "end")
        self.__AddSurname.delete(0, "end")
        self.__AddPassword.delete(0, "end")
        self.__AddAccessLevel.set("Teacher")
        self.__AddEmail.delete(0, "end")

    def __SubmitAdd(self):
        Forename = self.__AddForename.get().strip()
        Surname = self.__AddSurname.get().strip()
        Password = self.__AddPassword.get()
        AccessLevel = self.__AddAccessLevel.get()
        Email = self.__AddEmail.get().strip() or None
        if not Forename or not Surname or not Password:
            self.__AddFormError.config(text="Forename, Surname, and Password are required.")
            return
        # AddStaff requires SysAdmin permission
        Result = self.__controller.GetAM().AddStaff(Password, Forename, Surname, AccessLevel, Email)
        if "successfully" in str(Result):
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=str(Result))

    # --- Remove staff (SysAdmin) ---
    def __RemoveStaff(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StaffID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove staff member with ID {StaffID}?"):
            # RemoveStaff requires SysAdmin permission
            Result = self.__controller.GetAM().RemoveStaff(int(StaffID))
            if "successfully" in str(Result):
                self.__ShowAll()
                self.__DetailsText.config(text="Select a staff member to view details.")
            else:
                messagebox.showerror("Error", str(Result))

    # --- Promote / Demote (SysAdmin) ---
    def __PromoteStaff(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StaffID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Promote staff member {StaffID}?"):
            Result = self.__controller.GetAM().PromoteStaff(int(StaffID))
            if "successfully" in str(Result).lower() or "promoted" in str(Result).lower():
                self.__ShowAll()
            else:
                messagebox.showerror("Error", str(Result))

    def __DemoteStaff(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StaffID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Demote staff member {StaffID}?"):
            Result = self.__controller.GetAM().DemoteStaff(int(StaffID))
            if "successfully" in str(Result).lower() or "demoted" in str(Result).lower():
                self.__ShowAll()
            else:
                messagebox.showerror("Error", str(Result))

    # --- Set active / inactive (Admin) ---
    def __SetStatus(self, MakeActive):
        Selected = self.__Table.focus()
        if not Selected:
            return
        StaffID = self.__Table.item(Selected, "values")[0]
        StatusStr = "Active" if MakeActive else "Inactive"
        if messagebox.askyesno("Confirm", f"Set staff member {StaffID} to {StatusStr}?"):
            # SetAccountStatus requires Admin permission - IsStaff=True for staff
            Result = self.__controller.GetAM().SetAccountStatus(int(StaffID), True, MakeActive)
            if "changed" in str(Result).lower():
                self.__ShowAll()
            else:
                messagebox.showerror("Error", str(Result))

    # --- Update own email (Teacher - can update own) ---
    def __ShowUpdateOwnEmailForm(self):
        self.__HideAllForms()
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

    # --- Change password (Admin) ---
    def __ShowChangePasswordForm(self):
        # Default to own ID, but Admin+ can change for any selected staff member
        Selected = self.__Table.focus()
        if Selected:
            StaffID = self.__Table.item(Selected, "values")[0]
        else:
            StaffID = self.__controller.GetAM().GetCurrentUser()
        self.__HideAllForms()
        self.__ChangePasswordIDLabel.config(text=str(StaffID))
        self.__ChangePasswordForm.grid()

    def __HideChangePasswordForm(self):
        self.__ChangePasswordForm.grid_remove()
        self.__ChangePasswordFormError.config(text="")
        self.__NewPasswordEntry.delete(0, "end")

    def __SubmitChangePassword(self):
        StaffID = self.__ChangePasswordIDLabel.cget("text")
        NewPassword = self.__NewPasswordEntry.get()
        if not NewPassword:
            self.__ChangePasswordFormError.config(text="Password cannot be empty.")
            return
        # ChangePassword requires Admin permission
        Result = self.__controller.GetAM().ChangePassword(int(StaffID), NewPassword)
        if "changed" in str(Result).lower():
            self.__HideChangePasswordForm()
            messagebox.showinfo("Success", "Password changed successfully.")
        else:
            self.__ChangePasswordFormError.config(text=str(Result))