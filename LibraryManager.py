import sqlite3
from AccountManager import AccountManager
from datetime import datetime, timedelta
from notifypy import Notify
class LibraryManager:


    def __init__ (self):
        self.__Conn = sqlite3.connect("Databases/LibraryData.db")
        self.__Curs = self.__Conn.cursor()
        self.__AM = AccountManager()
        self.__LogFile = open("Log.txt", "a")
        self.__OnLoanLocation = 1

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


    def RemoveAuthor(self, UAID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to remove an author: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Check if author exists
            self.__Curs.execute(
                "SELECT UAID FROM Authors WHERE UAID = ?",
                (UAID,)
            )
            Author = self.__Curs.fetchone()
            if not Author:
                return "Author not found."
            # Remove author
            self.__Curs.execute(
                "DELETE FROM Authors WHERE UAID = ?",
                (UAID,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed author {UAID}")
            return "Author removed successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove an author and encountered an error: {e}")
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


    def RemoveBook(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if book exists
            self.__Curs.execute(
                "SELECT ISBN FROM Books WHERE ISBN = ?",
                (ISBN,)
            )
            Book = self.__Curs.fetchone()
            if not Book:
                return "Book not found."
            # Remove book
            self.__Curs.execute(
                "DELETE FROM Books WHERE ISBN = ?",
                (ISBN,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed book {ISBN}")
            return "Book removed successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a book and encountered an error: {e}")
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
            #Permission check
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
        

    def RemoveLocation(self, ULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if location exists
            self.__Curs.execute(
                "SELECT ULocID FROM Locations WHERE ULocID = ?",
                (ULocID,)
            )
            Location = self.__Curs.fetchone()
            if not Location:
                return "Location not found."
            # Remove location
            self.__Curs.execute(
                "DELETE FROM Locations WHERE ULocID = ?",
                (ULocID,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed location {ULocID}")
            return "Location removed successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a location and encountered an error: {e}")
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
        

    def RemoveCopy(self, UCID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if copy exists
            self.__Curs.execute(
                "SELECT UCID FROM Copies WHERE UCID = ?",
                (UCID,)
            )
            Copy = self.__Curs.fetchone()
            if not Copy:
                return "Copy not found."
            # Remove copy
            self.__Curs.execute(
                "DELETE FROM Copies WHERE UCID = ?",
                (UCID,)
            )
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed copy {UCID}")
            return "Copy removed successfully"
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a copy and encountered an error: {e}")
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
            LoanDate = int(datetime.now().strftime("%Y%m%d"))
            DueDate = int((datetime.now() + timedelta(days = self.__AM.GetLoanPeriod())).strftime("%Y%m%d"))
            if not self.LoanStockConflictCheck(UCID, LoanDate, DueDate):
                return "Loan cannot be issued due to stock conflicts with existing reservations or loans."
            # Issue loan
            ULoanID = self.__AM.GetNextID(self.__Curs, "Loans", "ULoanID")
            self.__Curs.execute(
                "INSERT INTO Loans (ULoanID, UStuID, UStaID, UCID, LoanDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ULoanID, UStuID, self.__AM.GetCurrentUser(), UCID, LoanDate, DueDate, None)
            )
            # Update copy status
            self.__Curs.execute(
                "UPDATE Copies SET Status = 'On Loan', CurrentLocationID = 1 WHERE UCID = ?",
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
                "UPDATE Copies SET Status = 'Available', CurrentLocationID = HomeLocationID WHERE UCID = ?",
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
                """SELECT Loans.DueDate FROM Loans INNER JOIN Copies ON Loans.UCID = Copies.UCID WHERE Copies.ISBN = ? AND Loans.ReturnDate IS NULL AND Loans.DueDate BETWEEN ? AND ?""",
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
                DateObj = datetime.strptime(str(ResDate), "%Y%m%d")
                NextDay = int((DateObj + timedelta(days=1)).strftime("%Y%m%d"))

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


    def NotifyUser(self, Message):
        # Should probably change this to push email notifications in the future, but for now this will do
        notification = Notify()
        notification.title = "School Library"
        notification.message = Message
        notification.icon = "Media/library-symbol-square.jpg"
        notification.audio = "Media/NotifySound.wav"
        notification.send()


    def FindReservationStock(self, URID):
        try:
            self.__Curs.execute(
                "SELECT ISBN, Quantity FROM Reservations WHERE URID = ?",
                (URID,)
            )
            Result = self.__Curs.fetchone()
            if not Result:
                return "Reservation not found."  
            BookISBN = Result[0]
            QuantityRemaining = Result[1]
            self.__Curs.execute(
                "SELECT CurrentLocationID FROM Copies WHERE ISBN = ? AND Status = 'Available' AND CurrentLocationID != ?",
                (BookISBN, self.__OnLoanLocation)
            )
            RawCopies = self.__Curs.fetchall()
            LocationCounts = []
            for Row in RawCopies:
                ULocID = Row[0]
                Found = False
                for Entry in LocationCounts:
                    if Entry[0] == ULocID:
                        Entry[1] += 1
                        Found = True
                        break
                if not Found:
                    LocationCounts.append([ULocID, 1])
            SortedLocations = self.MergeSort(LocationCounts)
            PickList = []
            for RoomData in SortedLocations:
                if QuantityRemaining <= 0:
                    break
                RoomID = RoomData[0]
                AvailableInRoom = RoomData[1]
                self.__Curs.execute("SELECT RoomName FROM Locations WHERE ULocID = ?", (RoomID,))
                RoomNameResult = self.__Curs.fetchone()
                RoomName = RoomNameResult[0] if RoomNameResult else f"Unknown Room ({RoomID})"
                AmountToTake = min(AvailableInRoom, QuantityRemaining)
                PickList.append([RoomName, AmountToTake])
                QuantityRemaining -= AmountToTake
            if QuantityRemaining > 0:
                return f"Insufficient stock. Need {QuantityRemaining} more copies."
            return PickList
        except Exception as e:
            print(f"Error: {e}")
            return None
            

    def __MergeSort(self, UnsortedList):
        if len(UnsortedList) <= 1:
            return UnsortedList
        MiddleIndex = len(UnsortedList) // 2
        LeftHalf = self.__MergeSort(UnsortedList[:MiddleIndex])
        RightHalf = self.__MergeSort(UnsortedList[MiddleIndex:])
        return self.__Merge(LeftHalf, RightHalf)


    def __Merge(self, LeftSide, RightSide):
        MergedList = []
        LeftPointer = 0
        RightPointer = 0
        while LeftPointer < len(LeftSide) and RightPointer < len(RightSide):
            if LeftSide[LeftPointer][1] >= RightSide[RightPointer][1]:
                MergedList.append(LeftSide[LeftPointer])
                LeftPointer += 1
            else:
                MergedList.append(RightSide[RightPointer])
                RightPointer += 1
        MergedList.extend(LeftSide[LeftPointer:])
        MergedList.extend(RightSide[RightPointer:])      
        return MergedList
    
    def SearchBooks(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            Query = """
                SELECT Books.ISBN, Books.Title, Authors.Surname, Books.Genre
                FROM Books
                JOIN BooksAuthors ON Books.ISBN = BooksAuthors.ISBN
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
                WHERE Books.Title LIKE ? OR Authors.Surname LIKE ? OR Books.ISBN LIKE ?
            """
            self.__Curs.execute(Query, (Term, Term, Term))
            Results = self.__Curs.fetchall()
            return Results if Results else f"Could not find any books matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchReservations(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            Query = """
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                WHERE Books.Title LIKE ? OR CAST(Reservations.URID AS TEXT) LIKE ?
            """
            self.__Curs.execute(Query, (Term, Term))
            Results = self.__Curs.fetchall()
            return Results if Results else f"Could not find any reservations matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchCopies(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            Query = """
                SELECT Copies.UCID, Books.Title, Copies.Status, Copies.Condition
                FROM Copies
                JOIN Books ON Copies.ISBN = Books.ISBN
                WHERE CAST(Copies.UCID AS TEXT) LIKE ? OR Books.Title LIKE ?
            """
            self.__Curs.execute(Query, (Term, Term))
            Results = self.__Curs.fetchall()
            return Results if Results else f"Could not find any book copies matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchLocations(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            Query = "SELECT ULocID, ClassCode FROM Locations WHERE ClassCode LIKE ?"
            self.__Curs.execute(Query, (Term,))
            Results = self.__Curs.fetchall()
            return Results if Results else f"Could not find a location matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"
        
    


LM = LibraryManager()