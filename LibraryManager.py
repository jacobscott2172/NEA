import sqlite3
from AccountManager import AccountManager
from datetime import datetime, timedelta

class LibraryManager:

    def __init__ (self):
        # Establishes class variables for relevant connections and cursors
        self.__Conn = sqlite3.connect("Databases/LibraryData.db")
        self.__Curs = self.__Conn.cursor()
        self.__AM = AccountManager()
        self.__LogFile = open("Log.txt", "a")

    def __del__(self):
        self.__Conn.commit()
        self.__Conn.close()
        self.__LogFile.flush()
        self.__LogFile.close()

    def AddAuthor(self, Forename, Middlename, Surname):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add an author: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Duplicate check
            self.__Curs.execute(
                "SELECT UAID FROM Authors WHERE Forename = ? AND Middlename = ? AND Surname = ?",
                (Forename, Middlename, Surname)
            )
            ExistingAuthor = self.__Curs.fetchone()
            if ExistingAuthor:
                # Author already exists, return their UAID
                return int(ExistingAuthor[0])
            # Finds next ID
            ID = self.__AM.GetNextID(self.__Curs, "Authors", "UAID")
            # Inserts author
            self.__Curs.execute(
                "INSERT INTO Authors (UAID, Forename, Middlename, Surname) VALUES (?, ?, ?, ?)",
                (ID, Forename, Middlename, Surname)
            )
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added author {ID}")
            return ID
        # Error handling amd logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add an author and encountered an error: {e}")
            return f"System error: {e}"

    def ValidateISBN(self, ISBN):
            ISBN = str(ISBN)
            if len(ISBN) != 13:
                return (False, "Invalid length ISBN. Only 13 digit format accepted")
            ISBN12 = ISBN[:12]
            OldCheckDigit = ISBN[-1]
            Total = 0
            for i, Digit in enumerate(ISBN12):
                # Alternating weights: 1, 3, 1, 3...
                weight = 1 if i % 2 == 0 else 3
                Total += int(Digit) * weight
            # Find if the user inputted ISBN matches the calculated check digit
            CheckDigit = (10 - (Total % 10)) % 10
            if CheckDigit != int(OldCheckDigit):
                return (False, "Invalid check digit. Check you inputted the ISBN correctly")
            else:
                return (True, "Valid ISBN")

    def AddBook(self, ISBN, Title, Genre, Subject, LearnerLevel, YearGroup):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # No ID to be generated as ISBNs are unique
            isValid, message = self.ValidateISBN(ISBN)
            if not isValid:
                return message # Returns the error message string
            # Duplicate check
            self.__Curs.execute(
                "SELECT ISBN FROM Books WHERE ISBN = ?",
                (ISBN,)
            )
            ExistingBook = self.__Curs.fetchone()
            if ExistingBook:
                # Book already exists, return their ISBN
                return ExistingBook[0]
            # Inserts book
            self.__Curs.execute(
                "INSERT INTO Books (ISBN, Title, Genre, Subject, LearnerLevel, YearGroup) VALUES (?, ?, ?, ?, ?, ?)",
                (ISBN, Title, Genre, Subject, LearnerLevel, YearGroup)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added book {ISBN}")
            return ISBN
        # Error handling amd logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a book and encountered an error: {e}")
            return f"System error: {e}"

    def LinkBookAuthors(self, ISBN, UAIDList):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            for ID in UAIDList:
                self.__Curs.execute(
                    "INSERT INTO BooksAuthors (ISBN, UAID) VALUES (?, ?)",
                    (ISBN, ID)
                )
                self.__AM.Log(f"User {self.__AM.GetCurrentUser()} Linked an author (ID: {ID}) to book (ISBN: {ISBN})")
            self.__Conn.commit()
        # Error handling amd logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add an author and encountered an error: {e}")
            return f"System error: {e}"

    def StreamlinedAddBook(self, ISBN, Title, Genre, Subject, LearnerLevel, YearGroup, ForenameList, MiddlenameList, SurnameList):
        try:
            UAIDList = []
            for x in range(len(ForenameList)):
                Forename = ForenameList[x]
                Middlename = MiddlenameList[x]
                Surname = SurnameList[x]
                AuthorID = self.AddAuthor(Forename, Middlename, Surname)
                if isinstance(AuthorID, str):
                    return AuthorID  # Return error message if AddAuthor failed
                else:
                    UAIDList.append(AuthorID)
            BookID = self.AddBook(ISBN, Title, Genre, Subject, LearnerLevel, YearGroup)
            if isinstance(BookID, str):
                return BookID  # Return error message if AddBook failed
            self.LinkBookAuthors(BookID, UAIDList)
            return f"Book {BookID} added successfully with authors."
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a book and encountered an error: {e}")
            return f"System error: {e}"

    def AddLocation(self, ClassCode):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                return "Access Denied: Insufficient Permissions."
            ULocID = self.__AM.GetNextID(self.__Curs, "Locations", "ULocID")
            self.__Curs.execute(
                "INSERT INTO Locations (ULocID, ClassCode) VALUES (?, ?)",
                (ULocID, ClassCode)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added location {ULocID}")
            return "Location added successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a location and encountered an error: {e}")
            return f"System error: {e}"
        
    def AddCopy(self, ISBN, ULocID, Condition):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            UCID = self.__AM.GetNextID(self.__Curs, "Copies", "UCID")
            self.__Curs.execute(
                "INSERT INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID, Status, Condition) VALUES (?, ?, ?, ?, ?, ?)",
                (UCID, ISBN, ULocID, ULocID, "Available", Condition)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added copy {UCID} of book {ISBN}")
            return "Copy added successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a copy and encountered an error: {e}")
            return f"System error: {e}"
        
    def IssueLoan(self, UCID, UStuID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if copy is available
            self.__Curs.execute(
                "SELECT Status FROM Copies WHERE UCID = ?",
                (UCID,)
            )
            Status = self.__Curs.fetchone()
            if not Status or Status[0] != "Available":
                return "Copy is not available for loan."
            # Get dates
            LoanDate = Date = int(datetime.now().strftime("%Y%m%d"))
            DueDate = int((datetime.now() + timedelta(days = self.__AM.GetLoanPeriod())).strftime("%Y%m%d"))
            # Issue loan
            ULoanID = self.__AM.GetNextID(self.__Curs, "Loans", "ULoanID")
            self.__Curs.execute(
                "INSERT INTO Loans (ULoanID, UStuID, UStaID, UCID, LoanDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ULoanID, UStuID, self.__AM.GetCurrentUser(), UCID, LoanDate, DueDate, None)
            )
            # Update copy status
            self.__Curs.execute(
                "UPDATE Copies SET Status = 'On Loan' WHERE UCID = ?",
                (UCID,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} issued loan {ULoanID} of copy {UCID} to student {UStuID}")
            return "Loan issued successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to issue a loan and encountered an error: {e}")
            return f"System error: {e}"
        
    def ReturnLoan(self, ULoanID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if loan exists and is not already returned
            self.__Curs.execute(
                "SELECT UCID, ReturnDate FROM Loans WHERE ULoanID = ?",
                (ULoanID,)
            )
            Loan = self.__Curs.fetchone()
            if not Loan:
                return "Loan not found."
            UCID, ReturnDate = Loan
            if ReturnDate is not None:
                return "Loan has already been returned."
            # Update loan return date
            ReturnDateValue = int(datetime.now().strftime("%Y%m%d"))
            self.__Curs.execute(
                "UPDATE Loans SET ReturnDate = ? WHERE ULoanID = ?",
                (ReturnDateValue, ULoanID)
            )
            # Update copy status
            self.__Curs.execute(
                "UPDATE Copies SET Status = 'Available' WHERE UCID = ?",
                (UCID,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} processed return of loan {ULoanID} for copy {UCID}")
            return "Loan returned successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to return a loan and encountered an error: {e}")
            return f"System error: {e}"
        
    def IssueReservation(self, ULocID, ReservationDate, ISBN, UStaID, Quantity):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Get reservation date
            CreationDate = int(datetime.now().strftime("%Y%m%d"))
            # Issue reservation
            URID = self.__AM.GetNextID(self.__Curs, "Reservations", "URID")
            self.__Curs.execute(
                "INSERT INTO Reservations (URID, ULocID, CreationDate, ReservationDate, ISBN, UStaID, Quantity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (URID, ULocID, CreationDate, ReservationDate, ISBN, UStaID, Quantity)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} issued reservation {URID} for book {ISBN}")
            return "Reservation issued successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to issue a reservation and encountered an error: {e}")
            return f"System error: {e}"
        
    def LoanStockConflictCheck(self, UCID, LoanDate, DueDate):
        try:
            self.__Curs.execute("SELECT ISBN FROM Copies WHERE UCID = ?", (UCID,))
            result = self.__Curs.fetchone()
            if not result:
                return "Error: Book not found"
            ISBN = result[0]
            self.__Curs.execute(
                "SELECT COUNT(*) FROM Copies WHERE ISBN = ? AND Status IN ('Available', 'Reserved')", 
                (ISBN,)
            )
            StartingStock = self.__Curs.fetchone()[0]
            Timeline = []
            self.__Curs.execute(
                "SELECT DueDate FROM Loans WHERE ISBN = ? AND Status = 'Active' AND DueDate BETWEEN ? AND ?",
                (ISBN, LoanDate, DueDate)
            )
            for row in self.__Curs.fetchall():
                ReturnDate = int(row[0]) 
                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == ReturnDate:
                        Timeline[Mid][1] += 1
                        Found = True
                        break 
                    elif Timeline[Mid][0] < ReturnDate:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    Timeline.insert(Left, [ReturnDate, 1])
            self.__Curs.execute(
                "SELECT ReservationDate, Quantity FROM Reservations WHERE ISBN = ? AND ReservationDate BETWEEN ? AND ?",
                (ISBN, LoanDate, DueDate)
            )
            for row in self.__Curs.fetchall():
                ResDate = int(row[0])
                Qty = row[1]
                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == ResDate:
                        Timeline[Mid][1] -= Qty
                        Found = True
                        break 
                    elif Timeline[Mid][0] < ResDate:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    Timeline.insert(Left, [ResDate, -Qty])
                DateObj = datetime.datetime.strptime(str(ResDate), "%Y%m%d")
                NextDay = int((DateObj + datetime.timedelta(days=1)).strftime("%Y%m%d"))

                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == NextDay:
                        Timeline[Mid][1] += Qty
                        Found = True
                        break 
                    elif Timeline[Mid][0] < NextDay:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    Timeline.insert(Left, [NextDay, Qty])
            RunningBalance = StartingStock - 1
            if RunningBalance < 0:
                return False
            for Event in Timeline:
                RunningBalance += Event[1]
                if RunningBalance < 0:
                    return False
            return True
        except Exception as e:
            self.__AM.Log(f"Conflict Check Error: {e}")
            return f"System error: {e}"
# Needed:
# Getter methods
# Search methods
# Update methods
# delete methods
# double bullshit reservation stock finder
# return methods
# overdue methods
# bulk book input
# reservation cleanup
# loan cleanup