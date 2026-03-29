import tkinter as tk
from tkinter import ttk, messagebox

class CatalogueFrame(tk.Frame):
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
        self.__ActiveTab = None
        for Label, Tab in [("Books", BooksTab), ("Authors", AuthorsTab), ("Copies", CopiesTab)]:
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
        for _, Tab in [("Books", BooksTab), ("Authors", AuthorsTab), ("Copies", CopiesTab)]:
            Frame = Tab(self.__TabContainer, controller)
            Frame.grid(row=0, column=0, sticky="nsew")
            self.__TabFrames[Tab] = Frame

        self.__ShowTab(BooksTab, "Books")

    def __ShowTab(self, TabClass, Label):
        # Reset all tab button styles
        for L, (Btn, _) in self.__Tabs.items():
            if L == Label:
                Btn.config(bg="#1e293b", fg="white")
            else:
                Btn.config(bg="#f0f4f8", fg="#1e293b")
        self.__TabFrames[TabClass].tkraise()
        if hasattr(self.__TabFrames[TabClass], "OnShow"):
            self.__TabFrames[TabClass].OnShow()


class BooksTab(tk.Frame):
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

        Columns = ("ISBN", "Title", "Author", "Genre", "Subject")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("ISBN", width=130)
        self.__Table.column("Title", width=180)
        self.__Table.column("Author", width=120)
        self.__Table.column("Genre", width=100)
        self.__Table.column("Subject", width=120)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Book Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a book to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Book", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Book", command=self.__RemoveBook).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Update Details", command=self.__ShowUpdateForm).pack(side="left")

        # --- Inline add form (hidden by default) ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__AddForm.grid_remove()

        tk.Label(self.__AddForm, text="Add Book", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        fields = [("ISBN", 0), ("Title", 1), ("Genre", 2), ("Subject", 3)]
        self.__AddEntries = {}
        for i, (Field, col) in enumerate(fields):
            tk.Label(self.__AddForm, text=Field, font=("Arial", 10), bg="white").grid(row=1, column=col*2, sticky="e", padx=(10,4))
            Entry = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
            Entry.grid(row=1, column=col*2+1, padx=(0, 10))
            self.__AddEntries[Field] = Entry

        tk.Label(self.__AddForm, text="Author Forename", font=("Arial", 10), bg="white").grid(row=2, column=0, sticky="e", padx=(10,4), pady=(8,0))
        self.__AuthorForename = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AuthorForename.grid(row=2, column=1, padx=(0,10), pady=(8,0))
        tk.Label(self.__AddForm, text="Author Surname", font=("Arial", 10), bg="white").grid(row=2, column=2, sticky="e", padx=(10,4), pady=(8,0))
        self.__AuthorSurname = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AuthorSurname.grid(row=2, column=3, padx=(0,10), pady=(8,0))

        self.__AddFormError = tk.Label(self.__AddForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__AddFormError.grid(row=3, column=0, columnspan=4, pady=(8,0))
        ttk.Button(self.__AddForm, text="Submit", command=self.__SubmitAdd).grid(row=4, column=0, pady=8)
        ttk.Button(self.__AddForm, text="Cancel", command=self.__HideAddForm).grid(row=4, column=1, pady=8)

        self.__ShowAll()

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetLM().GetAllBooks()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        Results = self.__controller.GetLM().SearchBooks(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            # Results format: (ISBN, Title, Forename, Middlenames, Surname, Genre, Subject)
            # Deduplicate by ISBN since multi-author books appear multiple times
            Seen = set()
            for Row in Results:
                ISBN = Row[0]
                if ISBN in Seen:
                    continue
                Seen.add(ISBN)
                MiddleName = f" {Row[3]}" if Row[3] else ""
                Author = f"{Row[2]}{MiddleName} {Row[4]}"
                self.__Table.insert("", "end", values=(ISBN, Row[1], Author, Row[5], Row[6]))
        else:
            self.__DetailsText.config(text=Results)

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        ISBN = Values[0]
        Details = self.__controller.GetLM().GetBookDetails(ISBN)
        if isinstance(Details, list) and Details:
            Authors = ", ".join(f"{R[2]} {R[4]}" for R in Details)
            D = Details[0]
            Text = f"ISBN: {D[0]}\nTitle: {D[1]}\nAuthor(s): {Authors}\nGenre: {D[5]}\nSubject: {D[6]}"
            self.__DetailsText.config(text=Text)

    def __ShowAddForm(self):
        self.__AddForm.grid()

    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        for Entry in self.__AddEntries.values():
            Entry.delete(0, "end")
        self.__AuthorForename.delete(0, "end")
        self.__AuthorSurname.delete(0, "end")

    def __SubmitAdd(self):
        ISBN = self.__AddEntries["ISBN"].get()
        Title = self.__AddEntries["Title"].get()
        Genre = self.__AddEntries["Genre"].get()
        Subject = self.__AddEntries["Subject"].get()
        Forename = self.__AuthorForename.get()
        Surname = self.__AuthorSurname.get()
        Result = self.__controller.GetLM().StreamlinedAddBook(
            int(ISBN), Title, Genre, Subject, [Forename], [None], [Surname]
        )
        if "successfully" in str(Result):
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=str(Result))

    def __RemoveBook(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        ISBN = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove book with ISBN {ISBN}?"):
            Result = self.__controller.GetLM().RemoveBook(ISBN)
            if "successfully" in Result:
                self.__ShowAll()
                self.__DetailsText.config(text="Select a book to view details.")
            else:
                messagebox.showerror("Error", Result)

    def __ShowUpdateForm(self):
        messagebox.showinfo("Update", "Update form coming soon.")


class AuthorsTab(tk.Frame):
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

        Columns = ("ID", "Forename", "Middlenames", "Surname")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("ID", width=50)
        self.__Table.column("Forename", width=120)
        self.__Table.column("Middlenames", width=120)
        self.__Table.column("Surname", width=120)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Author Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select an author to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Author", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Author", command=self.__RemoveAuthor).pack(side="left")

        # --- Inline add form ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__AddForm.grid_remove()

        tk.Label(self.__AddForm, text="Add Author", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        for i, Field in enumerate(["Forename", "Middlename", "Surname"]):
            tk.Label(self.__AddForm, text=Field, font=("Arial", 10), bg="white").grid(row=1, column=i*2, sticky="e", padx=(10,4))
            Entry = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
            Entry.grid(row=1, column=i*2+1, padx=(0, 10))
            setattr(self, f"__{Field}Entry", Entry)

        self.__AddFormError = tk.Label(self.__AddForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__AddFormError.grid(row=2, column=0, columnspan=6, pady=(8,0))
        ttk.Button(self.__AddForm, text="Submit", command=self.__SubmitAdd).grid(row=3, column=0, pady=8)
        ttk.Button(self.__AddForm, text="Cancel", command=self.__HideAddForm).grid(row=3, column=1, pady=8)

        self.__ShowAll()

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetLM().GetAllAuthors()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        Results = self.__controller.GetLM().SearchAuthors(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                self.__Table.insert("", "end", values=Row)

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        UAID = Values[0]
        Details = self.__controller.GetLM().GetAuthorDetails(UAID)
        if Details:
            Books = self.__controller.GetLM().GetAllBooksAuthored(UAID)
            BookList = ", ".join(R[1] for R in Books) if isinstance(Books, list) and Books else "None"
            Text = f"ID: {Details[0]}\nForename: {Details[1]}\nMiddlenames: {Details[2] or 'N/A'}\nSurname: {Details[3]}\n\nBooks:\n{BookList}"
            self.__DetailsText.config(text=Text)

    def __ShowAddForm(self):
        self.__AddForm.grid()

    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        self.__ForenameEntry.delete(0, "end")
        self.__MiddlenameEntry.delete(0, "end")
        self.__SurnameEntry.delete(0, "end")

    def __SubmitAdd(self):
        Forename = self.__ForenameEntry.get()
        Middlename = self.__MiddlenameEntry.get() or None
        Surname = self.__SurnameEntry.get()
        Result = self.__controller.GetLM().AddAuthor(Forename, Middlename, Surname)
        if isinstance(Result, int):
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=str(Result))

    def __RemoveAuthor(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        UAID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove author with ID {UAID}?"):
            Result = self.__controller.GetLM().RemoveAuthor(UAID)
            if "successfully" in Result:
                self.__ShowAll()
                self.__DetailsText.config(text="Select an author to view details.")
            else:
                messagebox.showerror("Error", Result)


class CopiesTab(tk.Frame):
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

        Columns = ("UCID", "Title", "ISBN", "Current Location", "Home Location")
        self.__Table = ttk.Treeview(TableFrame, columns=Columns, show="headings")
        for Col in Columns:
            self.__Table.heading(Col, text=Col)
        self.__Table.column("UCID", width=50)
        self.__Table.column("Title", width=180)
        self.__Table.column("ISBN", width=130)
        self.__Table.column("Current Location", width=120)
        self.__Table.column("Home Location", width=120)
        self.__Table.grid(row=0, column=0, sticky="nsew")
        self.__Table.bind("<<TreeviewSelect>>", self.__OnSelect)

        Scroll = ttk.Scrollbar(TableFrame, orient="vertical", command=self.__Table.yview)
        Scroll.grid(row=0, column=1, sticky="ns")
        self.__Table.configure(yscrollcommand=Scroll.set)

        # --- Details panel ---
        self.__DetailsPanel = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__DetailsPanel.grid(row=1, column=1, sticky="nsew")
        tk.Label(self.__DetailsPanel, text="Copy Details", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        ttk.Separator(self.__DetailsPanel, orient="horizontal").pack(fill="x", pady=8)
        self.__DetailsText = tk.Label(self.__DetailsPanel, text="Select a copy to view details.", font=("Arial", 10), bg="white", justify="left", wraplength=220)
        self.__DetailsText.pack(anchor="w")

        # --- Action buttons ---
        ActionBar = tk.Frame(self, bg="#f0f4f8")
        ActionBar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(ActionBar, text="Add Copy", command=self.__ShowAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Bulk Add Copies", command=self.__ShowBulkAddForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Move Copy", command=self.__ShowMoveForm).pack(side="left", padx=(0, 8))
        ttk.Button(ActionBar, text="Remove Copy", command=self.__RemoveCopy).pack(side="left")

        # --- Inline add form ---
        self.__AddForm = tk.Frame(self, bg="white", padx=15, pady=15)
        self.__AddForm.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.__AddForm.grid_remove()

        tk.Label(self.__AddForm, text="Add Copy", font=("Arial", 11, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        tk.Label(self.__AddForm, text="ISBN", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", padx=(10,4))
        self.__AddISBN = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AddISBN.grid(row=1, column=1, padx=(0,10))
        tk.Label(self.__AddForm, text="Location ID", font=("Arial", 10), bg="white").grid(row=1, column=2, sticky="e", padx=(10,4))
        self.__AddLocID = ttk.Entry(self.__AddForm, width=15, font=("Arial", 10))
        self.__AddLocID.grid(row=1, column=3, padx=(0,10))
        self.__AddFormError = tk.Label(self.__AddForm, text="", fg="red", font=("Arial", 10), bg="white")
        self.__AddFormError.grid(row=2, column=0, columnspan=4, pady=(8,0))
        ttk.Button(self.__AddForm, text="Submit", command=self.__SubmitAdd).grid(row=3, column=0, pady=8)
        ttk.Button(self.__AddForm, text="Cancel", command=self.__HideAddForm).grid(row=3, column=1, pady=8)

        self.__ShowAll()

    def OnShow(self):
        self.__ShowAll()

    def __ShowAll(self):
        Results = self.__controller.GetLM().GetAllCopies()
        self.__PopulateTable(Results)

    def __Search(self):
        Term = self.__SearchEntry.get()
        Results = self.__controller.GetLM().SearchCopies(Term)
        self.__PopulateTable(Results)

    def __PopulateTable(self, Results):
        for Row in self.__Table.get_children():
            self.__Table.delete(Row)
        if isinstance(Results, list):
            for Row in Results:
                self.__Table.insert("", "end", values=Row)

    def __OnSelect(self, event):
        Selected = self.__Table.focus()
        if not Selected:
            return
        Values = self.__Table.item(Selected, "values")
        if not Values:
            return
        UCID = Values[0]
        Details = self.__controller.GetLM().GetCopyDetails(UCID)
        if Details:
            Text = f"Copy ID: {Details[0]}\nTitle: {Details[1]}\nISBN: {Details[2]}\nCurrent Location: {Details[3]}\nHome Location: {Details[4]}"
            self.__DetailsText.config(text=Text)

    def __ShowAddForm(self):
        self.__AddForm.grid()

    def __HideAddForm(self):
        self.__AddForm.grid_remove()
        self.__AddFormError.config(text="")
        self.__AddISBN.delete(0, "end")
        self.__AddLocID.delete(0, "end")

    def __SubmitAdd(self):
        ISBN = self.__AddISBN.get()
        LocID = self.__AddLocID.get()
        Result = self.__controller.GetLM().AddCopy(int(ISBN), int(LocID))
        if "successfully" in Result:
            self.__HideAddForm()
            self.__ShowAll()
        else:
            self.__AddFormError.config(text=Result)

    def __ShowBulkAddForm(self):
        messagebox.showinfo("Bulk Add", "Bulk add form coming soon.")

    def __ShowMoveForm(self):
        messagebox.showinfo("Move", "Move form coming soon.")

    def __RemoveCopy(self):
        Selected = self.__Table.focus()
        if not Selected:
            return
        UCID = self.__Table.item(Selected, "values")[0]
        if messagebox.askyesno("Confirm", f"Remove copy with ID {UCID}?"):
            Result = self.__controller.GetLM().RemoveCopy(UCID)
            if "successfully" in Result:
                self.__ShowAll()
                self.__DetailsText.config(text="Select a copy to view details.")
            else:
                messagebox.showerror("Error", Result)