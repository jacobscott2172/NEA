import sqlite3
from AccountManager import AccountManager
from datetime import datetime, timedelta
class LibraryManager:


    def __init__ (self, AM):
        self.__Conn = sqlite3.connect("Databases/LibraryData.db")
        self.__Curs = self.__Conn.cursor()
        # Attaches SystemConfig.db so Staff details can be joined in reservation queries
        self.__Conn.execute("ATTACH DATABASE 'Databases/SystemConfig.db' AS sysconfig")
        self.__AM = AM
        self.__OnLoanLocation = 1


    def __del__(self):
        try:
            self.__Conn.commit()
            self.__Conn.close()
        # Suppresses errors if __init__ failed before attributes were assigned
        except AttributeError:
            pass

# --- Adding / Removing Authors ---
    def AddAuthor(self, Forename, Middlename, Surname):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add an author: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Duplicate check
            self.__Curs.execute("""
                SELECT UAID
                FROM Authors
                WHERE Forename = ? AND Middlenames = ? AND Surname = ?
            """,(Forename, Middlename, Surname))
            ExistingAuthor = self.__Curs.fetchone()
            if ExistingAuthor:
                # Author already exists, return their UAID
                return int(ExistingAuthor[0])
            # Finds next ID
            ID = self.__AM.GetNextID(self.__Curs, "Authors", "UAID")
            # Inserts author
            self.__Curs.execute("""
                INSERT INTO Authors (UAID, Forename, Middlenames, Surname)
                VALUES (?, ?, ?, ?)
            """,(ID, Forename, Middlename, Surname))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added author {ID}")
            return ID
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add an author and encountered an error: {e}")
            return f"System error: {e}"

    def RemoveAuthor(self, UAID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to remove an author: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            self.__Curs.execute("""
                SELECT UAID
                FROM Authors
                WHERE UAID = ?
            """,(UAID,))
            Author = self.__Curs.fetchone()
            if not Author:
                return "Author not found."
            # Removes author
            self.__Curs.execute("""
                DELETE FROM Authors
                WHERE UAID = ?
            """,(UAID,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed author {UAID}")
            return "Author removed successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove an author and encountered an error: {e}")
            return f"System error: {e}"

# --- Adding / Removing Books and Linking Authors ---
    def AddBook(self, ISBN, Title, Genre, Subject):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add a book: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # No ID to be generated as ISBNs are unique
            isValid, message = self.__ValidateISBN(ISBN)
            if not isValid:
                return message # Returns the error message string
            # Duplicate check
            self.__Curs.execute("""
                SELECT ISBN
                FROM Books
                WHERE ISBN = ?
            """,(ISBN,))
            ExistingBook = self.__Curs.fetchone()
            if ExistingBook:
                # Book already exists, return their ISBN
                return ExistingBook[0]
            # Inserts book
            self.__Curs.execute("""
                INSERT INTO Books (ISBN, Title, Genre, Subject)
                VALUES (?, ?, ?, ?)
            """,(ISBN, Title, Genre, Subject))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added book {ISBN}")
            return ISBN
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a book and encountered an error: {e}")
            return f"System error: {e}"

    def StreamlinedAddBook(self, ISBN, Title, Genre, Subject, ForenameList, MiddlenameList, SurnameList):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add a book with authors: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Adds each author from the supplied lists, collecting their UAIDs
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
            # Adds book, then links all authors to it
            BookID = self.AddBook(ISBN, Title, Genre, Subject)
            if isinstance(BookID, str):
                return BookID  # Return error message if AddBook failed
            self.LinkBookAuthors(BookID, UAIDList)
            # Returns confirmation
            return f"Book {BookID} added successfully with authors."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a book and encountered an error: {e}")
            return f"System error: {e}"

    def RemoveBook(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to remove a book: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            self.__Curs.execute("""
                SELECT ISBN
                FROM Books
                WHERE ISBN = ?
            """,(ISBN,))
            Book = self.__Curs.fetchone()
            if not Book:
                return "Book not found."
            # Removes book
            self.__Curs.execute("""
                DELETE FROM Books
                WHERE ISBN = ?
            """,(ISBN,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed book {ISBN}")
            return "Book removed successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a book and encountered an error: {e}")
            return f"System error: {e}"

    def LinkBookAuthors(self, ISBN, UAIDList):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Inserts a BooksAuthors row for each UAID in the list
            for ID in UAIDList:
                self.__Curs.execute("""
                    INSERT INTO BooksAuthors (ISBN, UAID)
                    VALUES (?, ?)
                """,(ISBN, ID))
                self.__AM.Log(f"User {self.__AM.GetCurrentUser()} Linked an author (ID: {ID}) to book (ISBN: {ISBN})")
            # Commits after all authors are linked
            self.__Conn.commit()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add an author and encountered an error: {e}")
            return f"System error: {e}"

    def UnlinkBookAuthors(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Removes all author links for the given book
            self.__Curs.execute("""
                DELETE FROM BooksAuthors
                WHERE ISBN = ?
            """,(ISBN,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} unlinked all authors from book (ISBN: {ISBN})")
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to unlink authors and encountered an error: {e}")
            return f"System error: {e}"

# --- Adding / Removing Locations ---
    def AddLocation(self, ClassCode):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add a location: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Finds next free ID
            ULocID = self.__AM.GetNextID(self.__Curs, "Locations", "ULocID")
            # Inserts location
            self.__Curs.execute("""
                INSERT INTO Locations (ULocID, ClassCode)
                VALUES (?, ?)
            """,(ULocID, ClassCode))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added location {ULocID}")
            return "Location added successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a location and encountered an error: {e}")
            return f"System error: {e}"
        
    def RemoveLocation(self, ULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to remove a location: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            self.__Curs.execute("""
                SELECT ULocID
                FROM Locations
                WHERE ULocID = ?
            """,(ULocID,))
            Location = self.__Curs.fetchone()
            if not Location:
                return "Location not found."
            # Removes location
            self.__Curs.execute("""
                DELETE FROM Locations
                WHERE ULocID = ?
            """,(ULocID,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed location {ULocID}")
            return "Location removed successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a location and encountered an error: {e}")
            return f"System error: {e}"

# --- Adding / Removing / Moving Copies ---
    def AddCopy(self, ISBN, ULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add a copy: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Finds next free ID
            UCID = self.__AM.GetNextID(self.__Curs, "Copies", "UCID")
            # HomeLocationID and CurrentLocationID both start as the supplied location
            self.__Curs.execute("""
                INSERT INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID)
                VALUES (?, ?, ?, ?)
            """,(UCID, ISBN, ULocID, ULocID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} added copy {UCID} of book {ISBN}")
            return "Copy added successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to add a copy and encountered an error: {e}")
            return f"System error: {e}"

    def BulkAddCopies(self, ISBN, ULocID, Quantity):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to bulk add copies: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Inserts each copy individually to ensure unique IDs are assigned
            for n in range(Quantity):
                UCID = self.__AM.GetNextID(self.__Curs, "Copies", "UCID")
                self.__Curs.execute("""
                    INSERT INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID)
                    VALUES (?, ?, ?, ?)
                """,(UCID, ISBN, ULocID, ULocID))
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} added copy {UCID} of book {ISBN}")
            # Commits once after all inserts
            self.__Conn.commit()
            return f"{Quantity} copies added successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to bulk add copies and encountered an error: {e}")
            return f"System error: {e}"

    def MoveCopy(self, UCID, NewULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Updates current location only, home location is unchanged
            self.__Curs.execute("""
                UPDATE Copies
                SET CurrentLocationID = ?
                WHERE UCID = ?
            """,(NewULocID, UCID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} moved copy {UCID} to location {NewULocID}")
            return "Copy moved successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to move a copy and encountered an error: {e}")
            return f"System error: {e}"

    def ChangeCopyHomeLocation(self, UCID, NewULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Updates home location only, current location is unchanged
            self.__Curs.execute("""
                UPDATE Copies
                SET HomeLocationID = ?
                WHERE UCID = ?
            """,(NewULocID, UCID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} changed home location of copy {UCID} to {NewULocID}")
            return "Copy home location changed successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to change the home location of a copy and encountered an error: {e}")
            return f"System error: {e}"

    def RemoveCopy(self, UCID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Typo check
            self.__Curs.execute("""
                SELECT UCID
                FROM Copies
                WHERE UCID = ?
            """,(UCID,))
            Copy = self.__Curs.fetchone()
            if not Copy:
                return "Copy not found."
            # Removes copy
            self.__Curs.execute("""
                DELETE FROM Copies
                WHERE UCID = ?
            """,(UCID,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} removed copy {UCID}")
            return "Copy removed successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to remove a copy and encountered an error: {e}")
            return f"System error: {e}"

# --- Issuing, returning, and deleting loans ---
    def IssueLoan(self, UCID, UStuID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.__AM.CheckIDExists(self.__Curs, "Students", "UStuID", UStuID):
                return "Error: Student ID does not exist."
            # Inactive account check
            if not self.__AM.IsAccountActive(self.__Curs, "Students", "UStuID", UStuID):
                return "Error: Student account is inactive."
            # Loan limit check
            self.__Curs.execute(
                "SELECT MaxActiveLoans FROM Students WHERE UStuID = ?", (UStuID,)
            )
            MaxLoans = self.__Curs.fetchone()[0]
            self.__Curs.execute(
                "SELECT COUNT(*) FROM Loans WHERE UStuID = ? AND ReturnDate IS NULL", (UStuID,)
            )
            ActiveLoans = self.__Curs.fetchone()[0]
            if ActiveLoans >= MaxLoans:
                return "Loan limit reached."
            # Get dates
            LoanDate = int(datetime.now().strftime("%Y%m%d"))
            DueDate = int((datetime.now() + timedelta(days = self.__AM.GetLoanPeriod())).strftime("%Y%m%d"))
            # Check if copy is available: not on active loan and at its home location
            # CurrentLocationID = HomeLocationID ensures we don't loan a copy that
            # has already been physically allocated to a reservation by FindReservationStock
            self.__Curs.execute("""
                SELECT COUNT(*)
                FROM Copies
                WHERE UCID = ?
                AND UCID NOT IN (SELECT UCID FROM Loans WHERE ReturnDate IS NULL)
                AND CurrentLocationID = HomeLocationID
            """,(UCID,))
            CopyCheck = self.__Curs.fetchone()
            if not CopyCheck or CopyCheck[0] == 0:
                return "Copy is not available for loan."
            # Stock conflict check against all active loans and upcoming reservations
            if not self.__LoanStockConflictCheck(UCID, LoanDate, DueDate):
                return "Loan cannot be issued due to stock conflicts with existing reservations or loans."
            # Finds next free ID and issues loan
            ULoanID = self.__AM.GetNextID(self.__Curs, "Loans", "ULoanID")
            self.__Curs.execute("""
                INSERT INTO Loans (ULoanID, UStuID, UStaID, UCID, LoanDate, DueDate, ReturnDate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,(ULoanID, UStuID, self.__AM.GetCurrentUser(), UCID, LoanDate, DueDate, None))
            # Sets CurrentLocationID to the OnLoan location
            self.__Curs.execute("""
                UPDATE Copies
                SET CurrentLocationID = ?
                WHERE UCID = ?
            """,(self.__OnLoanLocation, UCID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} issued loan {ULoanID} of copy {UCID} to student {UStuID}")
            return "Loan issued successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to issue a loan and encountered an error: {e}")
            return f"System error: {e}"

    def ReturnLoan(self, ULoanID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Check if loan exists and is active
            self.__Curs.execute("""
                SELECT UCID, ReturnDate
                FROM Loans
                WHERE ULoanID = ?
            """,(ULoanID,))
            Loan = self.__Curs.fetchone()
            if not Loan:
                return "Loan not found."
            UCID, ReturnDate = Loan
            if ReturnDate is not None:
                return "Loan has already been returned."
            # Update loan return date
            ReturnDateValue = int(datetime.now().strftime("%Y%m%d"))
            self.__Curs.execute("""
                UPDATE Loans
                SET ReturnDate = ?
                WHERE ULoanID = ?
            """,(ReturnDateValue, ULoanID))
            # Resets CurrentLocationID to HomeLocationID
            self.__Curs.execute("""
                UPDATE Copies
                SET CurrentLocationID = HomeLocationID
                WHERE UCID = ?
            """,(UCID,))
            # Retrieve book title and student name for confirmation message
            self.__Curs.execute("""
                SELECT Books.Title, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.ULoanID = ?
            """,(ULoanID,))
            LoanInfo = self.__Curs.fetchone()
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} processed return of loan {ULoanID} for copy {UCID}")
            if LoanInfo:
                return f"Loan returned successfully: '{LoanInfo[0]}' from {LoanInfo[1]} {LoanInfo[2]}."
            return "Loan returned successfully."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to return a loan and encountered an error: {e}")
            return f"System error: {e}"

    def ExtendLoan(self, ULoanID, NewDueDate):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to extend loan {ULoanID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Check if loan exists and is active
            self.__Curs.execute("""
                SELECT UCID, DueDate, ReturnDate, Loans.UStuID
                FROM Loans
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE ULoanID = ?
            """, (ULoanID,))
            Loan = self.__Curs.fetchone()
            if not Loan:
                return "Loan not found."
            UCID, CurrentDueDate, ReturnDate, UStuID = Loan
            if ReturnDate is not None:
                return "Loan has already been returned."
            if NewDueDate <= CurrentDueDate:
                return "New due date must be later than the current due date."
            # Check the extension does not conflict with existing reservations or loans
            LoanDate = int(datetime.now().strftime("%Y%m%d"))
            if not self.__LoanStockConflictCheck(UCID, LoanDate, NewDueDate):
                return "Loan cannot be extended due to stock conflicts with existing reservations."
            # Update due date
            self.__Curs.execute("""
                UPDATE Loans
                SET DueDate = ?
                WHERE ULoanID = ?
            """, (NewDueDate, ULoanID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} extended loan {ULoanID} to {NewDueDate}")
            return f"Loan extended to {NewDueDate}."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to extend loan {ULoanID} and encountered an error: {e}")
            return f"System error: {e}"


    def ClearOldLoans(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to clear old loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves retention period from settings
            MonthsToKeep = self.__AM.GetRetentionMonths()
            # Generates current date for calculation
            Now = datetime.now()
            Year = Now.year
            Month = Now.month
            # While not day-accurate, this avoids a "February 31st" issue
            Day = 1
            # Subtracts months from current date to find cut off date
            for m in range(int(MonthsToKeep)):
                Month -= 1
                # Year rollover
                if Month == 0:
                    Month = 12
                    Year -= 1
            # Formats Date to ISO 8601
            CutOffDate = int(f"{Year}{Month:02d}{Day:02d}")
            # Deletes all returned loans older than the cut off date in one operation
            self.__Curs.execute("""
                DELETE FROM Loans
                WHERE ReturnDate IS NOT NULL AND ReturnDate < ?
            """,(CutOffDate,))
            # Counts deleted loans
            LoansDeleted = self.__Curs.rowcount
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} cleared {LoansDeleted} old loans with return date before {CutOffDate}")
            return f"Cleared {LoansDeleted} old loans."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to clear old loans and encountered an error: {e}")
            return f"System error: {e}"


# --- Issuing and deleting reservations ---
    def ClearOldReservations(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to clear old reservations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves retention period from settings
            MonthsToKeep = self.__AM.GetRetentionMonths()
            # Generates current date for calculation
            Now = datetime.now()
            Year = Now.year
            Month = Now.month
            # While not day-accurate, this avoids a "February 31st" issue
            Day = 1
            # Subtracts months from current date to find cut off date
            for m in range(int(MonthsToKeep)):
                Month -= 1
                # Year rollover
                if Month == 0:
                    Month = 12
                    Year -= 1
            # Formats Date to ISO 8601
            CutOffDate = int(f"{Year}{Month:02d}{Day:02d}")
            # Deletes all reservations older than the cut off date in one operation
            self.__Curs.execute("""
                DELETE FROM Reservations
                WHERE ReservationDate < ?
            """,(CutOffDate,))
            # Counts deleted reservations
            ReservationsDeleted = self.__Curs.rowcount
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} cleared {ReservationsDeleted} old reservations with date before {CutOffDate}")
            return f"Cleared {ReservationsDeleted} old reservations."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to clear old reservations and encountered an error: {e}")
            return f"System error: {e}"
 
    def IssueReservation(self, ULocID, ReservationDate, ISBN, UStaID, Quantity):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # CreationDate is today, used for first-reserved first-served ordering
            CreationDate = int(datetime.now().strftime("%Y%m%d"))
            # Finds next free ID and inserts reservation
            URID = self.__AM.GetNextID(self.__Curs, "Reservations", "URID")
            self.__Curs.execute("""
                INSERT INTO Reservations (URID, ULocID, CreationDate, ReservationDate, ISBN, UStaID, Quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,(URID, ULocID, CreationDate, ReservationDate, ISBN, UStaID, Quantity))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} issued reservation {URID} for book {ISBN}")
            return "Reservation issued successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to issue a reservation and encountered an error: {e}")
            return f"System error: {e}"
            
# --- Update methods ---
    def UpdateBookDetails(self, ISBN, Title, Genre, Subject):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to update book {ISBN}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.__AM.CheckIDExists(self.__Curs, "Books", "ISBN", ISBN):
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to update book {ISBN}: ISBN does not exist")
                return "Error: ISBN does not exist"
            # Updates book details
            self.__Curs.execute("""
                UPDATE Books
                SET Title = ?, Genre = ?, Subject = ?
                WHERE ISBN = ?
            """, (Title, Genre, Subject, ISBN))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} updated details for book {ISBN}")
            return "Book details updated successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to update book {ISBN} and encountered an error: {e}")
            return f"System error: {e}"

    def UpdateReservation(self, URID, ULocID, ReservationDate, Quantity):
        try:
            # Retrieve the reservation to check ownership
            self.__Curs.execute("""
                SELECT UStaID
                FROM Reservations
                WHERE URID = ?
            """, (URID,))
            Result = self.__Curs.fetchone()
            if not Result:
                return "Error: Reservation does not exist"
            Owner = Result[0]
            # Permission check: Teachers can only update their own reservations; Admins can update any
            IsOwner = self.__AM.GetCurrentUser() == Owner
            IsAdmin = self.__AM.CheckPermission("Admin") == True
            if not IsOwner and not IsAdmin:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to update reservation {URID}: Insufficient permissions")
                return "Access Denied: You can only update your own reservations."
            # Updates reservation details
            self.__Curs.execute("""
                UPDATE Reservations
                SET ULocID = ?, ReservationDate = ?, Quantity = ?
                WHERE URID = ?
            """, (ULocID, ReservationDate, Quantity, URID))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} updated reservation {URID}")
            return "Reservation updated successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to update reservation {URID} and encountered an error: {e}")
            return f"System error: {e}"

    def DeleteReservation(self, URID):
        try:
            # Retrieve the reservation to check ownership
            self.__Curs.execute("""
                SELECT UStaID
                FROM Reservations
                WHERE URID = ?
            """, (URID,))
            Result = self.__Curs.fetchone()
            if not Result:
                return "Error: Reservation does not exist"
            Owner = Result[0]
            # Permission check: Teachers can only delete their own reservations; Admins can delete any
            IsOwner = self.__AM.GetCurrentUser() == Owner
            IsAdmin = self.__AM.CheckPermission("Admin") == True
            if not IsOwner and not IsAdmin:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to delete reservation {URID}: Insufficient permissions")
                return "Access Denied: You can only delete your own reservations."
            # Deletes the reservation
            self.__Curs.execute("""
                DELETE FROM Reservations
                WHERE URID = ?
            """, (URID,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} deleted reservation {URID}")
            return "Reservation deleted successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to delete reservation {URID} and encountered an error: {e}")
            return f"System error: {e}"

    def DeleteLoan(self, ULoanID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to delete loan {ULoanID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves loan to check if it is still active
            self.__Curs.execute("""
                SELECT UCID, ReturnDate
                FROM Loans
                WHERE ULoanID = ?
            """, (ULoanID,))
            Result = self.__Curs.fetchone()
            if not Result:
                return "Error: Loan does not exist"
            UCID, ReturnDate = Result
            # If the loan is still active, reset the copy location before deleting
            if ReturnDate is None:
                self.__Curs.execute("""
                    UPDATE Copies
                    SET CurrentLocationID = HomeLocationID
                    WHERE UCID = ?
                """, (UCID,))
            # Deletes the loan
            self.__Curs.execute("""
                DELETE FROM Loans
                WHERE ULoanID = ?
            """, (ULoanID,))
            # Commits, Logs, Returns confirmation
            self.__Conn.commit()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} deleted loan {ULoanID}")
            return "Loan deleted successfully"
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to delete loan {ULoanID} and encountered an error: {e}")
            return f"System error: {e}"


# --- Search Methods ---
    def SearchBooks(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search books: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT Books.ISBN, Books.Title, Authors.Surname, Books.Genre, Books.Subject
                FROM Books
                JOIN BooksAuthors ON Books.ISBN = BooksAuthors.ISBN
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
                WHERE Books.Title LIKE ? OR Authors.Surname LIKE ? OR Books.ISBN LIKE ? OR Books.Genre LIKE ? OR Books.Subject LIKE ?
            """, (Term, Term, Term, Term, Term))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find any books matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchReservations(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search reservations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity, Reservations.UStaID, Staff.Forename, Staff.Surname, Locations.ClassCode
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                JOIN Locations ON Reservations.ULocID = Locations.ULocID
                WHERE Books.Title LIKE ? OR CAST(Books.ISBN AS TEXT) LIKE ? OR CAST(Reservations.URID AS TEXT) LIKE ? OR Staff.Forename LIKE ? OR Staff.Surname LIKE ? OR CAST(Reservations.UStaID AS TEXT) LIKE ?
            """, (Term, Term, Term, Term, Term, Term))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find any reservations matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchCopies(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search copies: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT Copies.UCID, Books.Title, Books.ISBN, CurrentLoc.ClassCode, HomeLoc.ClassCode
                FROM Copies
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Locations AS CurrentLoc ON Copies.CurrentLocationID = CurrentLoc.ULocID
                JOIN Locations AS HomeLoc ON Copies.HomeLocationID = HomeLoc.ULocID
                WHERE CAST(Copies.UCID AS TEXT) LIKE ? OR Books.Title LIKE ? OR Books.ISBN LIKE ? OR CurrentLoc.ClassCode LIKE ? OR HomeLoc.ClassCode LIKE ?
            """, (Term, Term, Term, Term, Term))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find any book copies matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}" 

    def SearchLocations(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search locations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT ULocID, ClassCode
                FROM Locations
                WHERE ClassCode LIKE ?
            """, (Term,))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find a location matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchAuthors(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search authors: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT UAID, Forename, Middlenames, Surname
                FROM Authors
                WHERE Forename LIKE ? OR Middlenames LIKE ? OR Surname LIKE ?
            """, (Term, Term, Term))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find an author matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"
        
    def SearchLoans(self, SearchTerm):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to search loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.LoanDate, Loans.DueDate, Loans.ReturnDate, Loans.UStuID, Loans.UStaID, Copies.UCID, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE CAST(Loans.ULoanID AS TEXT) LIKE ? OR Books.Title LIKE ? OR Students.Forename LIKE ? OR Students.Surname LIKE ? OR CAST(Loans.UStuID AS TEXT) LIKE ? OR CAST(Loans.UStaID AS TEXT) LIKE ? OR CAST(Copies.UCID AS TEXT) LIKE ?
            """, (Term, Term, Term, Term, Term, Term, Term))
            Results = self.__Curs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find a loan matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"

# --- Notification Methods ---
    def GetOverdueLoans(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Generates today's date for comparison
            Today = int(datetime.now().strftime("%Y%m%d"))
            # Retrieves all active loans past their due date, including student contact details
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.DueDate, Loans.UStuID, Students.Forename, Students.Surname, Students.Email
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.ReturnDate IS NULL AND Loans.DueDate < ?
            """, (Today,))
            Results = self.__Curs.fetchall()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved {len(Results)} overdue loans")
            # Returns results or a not found message
            return Results if Results else "No overdue loans found."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve overdue loans and encountered an error: {e}")
            return f"System error: {e}"

    def GetLoansDueTomorrow(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # timedelta handles all date edge cases including year boundaries and leap years
            Tomorrow = int((datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
            # Retrieves all active loans due tomorrow, including student contact details
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.DueDate, Loans.UStuID, Students.Forename, Students.Surname, Students.Email
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.ReturnDate IS NULL AND Loans.DueDate = ?
            """, (Tomorrow,))
            Results = self.__Curs.fetchall()
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved {len(Results)} loans due tomorrow")
            # Returns results or a not found message
            return Results if Results else "No loans due tomorrow."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve loans due tomorrow and encountered an error: {e}")
            return f"System error: {e}"

    def SendOverdueNotifications(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Retrieves all overdue loans
            OverdueLoans = self.GetOverdueLoans()
            if isinstance(OverdueLoans, str):
                # Either no results or an error
                return OverdueLoans
            Sent = 0
            # Sends an email to each student with an overdue book
            for Loan in OverdueLoans:
                ULoanID, Title, DueDate, UStuID, Forename, Surname, Email = Loan
                if not Email:
                    self.__AM.Log(f"Overdue notification skipped for student {UStuID}: no email address on record")
                    continue
                # Builds and sends email
                Subject = "Overdue Library Book"
                Body = f"Dear {Forename} {Surname},\n\nThe following book is overdue:\n"
                Body += f"  Title: {Title}\n  Loan ID: {ULoanID}\n  Due date: {DueDate}\n\n"
                Body += "Please return it to the library as soon as possible."
                Result = self.__AM.SendEmail(Email, Subject, Body)
                if Result == True:
                    Sent += 1
                else:
                    self.__AM.Log(f"Failed to send overdue notification to student {UStuID}")
            # Logs and returns confirmation
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} sent {Sent} overdue notifications")
            return f"Sent {Sent} overdue notifications."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} encountered an error sending overdue notifications: {e}")
            return f"System error: {e}"

    def SendDueTomorrowNotifications(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Retrieves all loans due tomorrow
            DueTomorrow = self.GetLoansDueTomorrow()
            if isinstance(DueTomorrow, str):
                # Either no results or an error
                return DueTomorrow
            Sent = 0
            # Sends a reminder email to each student with a book due tomorrow
            for Loan in DueTomorrow:
                ULoanID, Title, DueDate, UStuID, Forename, Surname, Email = Loan
                if not Email:
                    self.__AM.Log(f"Due tomorrow notification skipped for student {UStuID}: no email address on record")
                    continue
                # Builds and sends email
                Subject = "Library Book Due Tomorrow"
                Body = f"Dear {Forename} {Surname},\n\nThe following book is due back tomorrow:\n"
                Body += f"  Title: {Title}\n  Loan ID: {ULoanID}\n  Due date: {DueDate}\n\n"
                Body += "Please remember to return it to the library."
                Result = self.__AM.SendEmail(Email, Subject, Body)
                if Result == True:
                    Sent += 1
                else:
                    self.__AM.Log(f"Failed to send due tomorrow notification to student {UStuID}")
            # Logs and returns confirmation
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} sent {Sent} due tomorrow notifications")
            return f"Sent {Sent} due tomorrow notifications."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} encountered an error sending due tomorrow notifications: {e}")
            return f"System error: {e}"

# --- StartUp ---
    def StartUp(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Emails students whose loans are due back tomorrow
            DueTomorrowResult = self.SendDueTomorrowNotifications()
            self.__AM.Log(f"StartUp: SendDueTomorrowNotifications - {DueTomorrowResult}")
            # Emails students whose loans are already overdue
            OverdueResult = self.SendOverdueNotifications()
            self.__AM.Log(f"StartUp: SendOverdueNotifications - {OverdueResult}")
            # Finds all reservations for today and emails the respective teacher for each
            Today = int(datetime.now().strftime("%Y%m%d"))
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.Quantity, Reservations.UStaID, Staff.Email, Staff.Forename, Staff.Surname
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                WHERE Reservations.ReservationDate = ?
            """, (Today,))
            TodaysReservations = self.__Curs.fetchall()
            ReservationsSent = 0
            for Reservation in TodaysReservations:
                URID, Title, Quantity, UStaID, Email, Forename, Surname = Reservation
                if not Email:
                    self.__AM.Log(f"StartUp: Reservation {URID} notification skipped for staff {UStaID}: no email address on record")
                    continue
                # Finds which copies to collect and from where, also updates their CurrentLocationID
                PickList = self.__FindReservationStock(URID)
                if isinstance(PickList, str) or PickList is None:
                    self.__AM.Log(f"StartUp: Could not find stock for reservation {URID}: {PickList}")
                    continue
                # Builds email body from picklist
                Body = f"Dear {Forename} {Surname},\n\nYour reservation for today is ready to collect:\n"
                Body += f"  Title: {Title}, Quantity: {Quantity}\n\nCopies to collect:\n"
                for Entry in PickList:
                    RoomName = Entry[-1]
                    CopyIDs = Entry[:-1]
                    Body += f"  Room {RoomName}: copies {', '.join(str(c) for c in CopyIDs)}\n"
                Result = self.__AM.SendEmail(Email, "Library Reservation Ready", Body)
                if Result == True:
                    ReservationsSent += 1
                else:
                    self.__AM.Log(f"StartUp: Failed to send reservation notification for {URID} to staff {UStaID}")
            self.__AM.Log(f"StartUp: Sent {ReservationsSent} of {len(TodaysReservations)} reservation notifications")
            return f"StartUp complete. Due tomorrow: {DueTomorrowResult}. Overdue: {OverdueResult}. Reservation notifications: {ReservationsSent}/{len(TodaysReservations)}."
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"StartUp encountered an error: {e}")
            return f"System error: {e}"


# --- Internal helper methods ---
    def __ValidateISBN(self, ISBN):
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

    def __MergeSort(self, UnsortedList):
        # Base case: a list of 0 or 1 is already sorted
        if len(UnsortedList) <= 1:
            return UnsortedList
        # Splits list in half and recursively sorts each half
        MiddleIndex = len(UnsortedList) // 2
        LeftHalf = self.__MergeSort(UnsortedList[:MiddleIndex])
        RightHalf = self.__MergeSort(UnsortedList[MiddleIndex:])
        return self.__Merge(LeftHalf, RightHalf)

    def __Merge(self, LeftSide, RightSide):
        # Merges two sorted halves into one, sorted descending by the second element (copy count per location)
        MergedList = []
        LeftPointer = 0
        RightPointer = 0
        while LeftPointer < len(LeftSide) and RightPointer < len(RightSide):
            # Descending order: higher count comes first
            if LeftSide[LeftPointer][1] >= RightSide[RightPointer][1]:
                MergedList.append(LeftSide[LeftPointer])
                LeftPointer += 1
            else:
                MergedList.append(RightSide[RightPointer])
                RightPointer += 1
        # Appends any remaining elements from either half
        MergedList.extend(LeftSide[LeftPointer:])
        MergedList.extend(RightSide[RightPointer:])      
        return MergedList

    def __FindReservationStock(self, URID):
        try:
            # Retrieves reservation details needed for stock allocation
            self.__Curs.execute("""
                SELECT ISBN, Quantity, ULocID, ReservationDate
                FROM Reservations
                WHERE URID = ?
            """,(URID,))
            Result = self.__Curs.fetchone()
            if not Result:
                return "Reservation not found."  
            BookISBN = Result[0]
            QuantityRemaining = Result[1]
            ReservationLocID = Result[2]
            # Finds all available copies: not on active loan and at home location
            # CurrentLocationID = HomeLocationID prevents allocating copies already
            # moved by a previous FindReservationStock call earlier in the same StartUp
            self.__Curs.execute("""
                SELECT UCID, CurrentLocationID
                FROM Copies
                WHERE ISBN = ?
                AND CurrentLocationID = HomeLocationID
                AND UCID NOT IN (SELECT UCID FROM Loans WHERE ReturnDate IS NULL)
            """,(BookISBN,))
            RawCopies = self.__Curs.fetchall()
            # Builds a count of copies per location and a dict mapping each location to its copy IDs
            LocationCounts = []
            CopyIDsByLocation = {}
            for Row in RawCopies:
                RowUCID = Row[0]
                ULocID = Row[1]
                Found = False
                for Entry in LocationCounts:
                    if Entry[0] == ULocID:
                        Entry[1] += 1
                        Found = True
                        break
                if not Found:
                    LocationCounts.append([ULocID, 1])
                if ULocID not in CopyIDsByLocation:
                    CopyIDsByLocation[ULocID] = []
                CopyIDsByLocation[ULocID].append(RowUCID)
            # Sorts locations descending by copy count, preferring rooms with more copies for easier collection
            SortedLocations = self.__MergeSort(LocationCounts)
            PickList = []
            ReservedUCIDs = []
            # Takes copies from each room starting with the most stocked, until the required quantity is met
            for RoomData in SortedLocations:
                if QuantityRemaining <= 0:
                    break
                RoomID = RoomData[0]
                AvailableInRoom = RoomData[1]
                self.__Curs.execute("""
                    SELECT ClassCode
                    FROM Locations
                    WHERE ULocID = ?
                """, (RoomID,))
                RoomNameResult = self.__Curs.fetchone()
                RoomName = RoomNameResult[0] if RoomNameResult else f"Unknown Room ({RoomID})"
                AmountToTake = min(AvailableInRoom, QuantityRemaining)
                TakenUCIDs = CopyIDsByLocation[RoomID][:AmountToTake]
                # Each picklist entry is a list of UCIDs followed by the room name
                PickList.append(TakenUCIDs + [RoomName])
                ReservedUCIDs.extend(TakenUCIDs)
                QuantityRemaining -= AmountToTake
            if QuantityRemaining > 0:
                return f"Insufficient stock. Need {QuantityRemaining} more copies."
            # Updates CurrentLocationID of all allocated copies to the reservation's target location
            for ReservedUCID in ReservedUCIDs:
                self.__Curs.execute("""
                    UPDATE Copies
                    SET CurrentLocationID = ?
                    WHERE UCID = ?
                """, (ReservationLocID, ReservedUCID))
            # Commits, Returns picklist
            self.__Conn.commit()
            return PickList
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} encountered an error in FindReservationStock: {e}")
            return None

    def __LoanStockConflictCheck(self, UCID, LoanDate, DueDate):
        try:
            # The check works at ISBN level, not copy level - all copies of the same book are interchangeable
            # So we find the ISBN first, then count and track stock across all copies of that book
            self.__Curs.execute("""
                SELECT ISBN FROM Copies WHERE UCID = ?
            """, (UCID,))
            result = self.__Curs.fetchone()
            # If the copy doesn't exist, reject immediately
            if not result:
                return False
            ISBN = result[0]
            # Starting stock = number of copies of this book not currently on an active loan
            # We do not need to track loans being issued during the window - any loan that will be issued
            # in the future does not exist yet, so it cannot be counted. When it is eventually issued,
            # it will run this same check at that point. Only already-committed events (active loans
            # returning, and existing reservations) need to be modelled in the timeline
            self.__Curs.execute("""
                SELECT COUNT(*)
                FROM Copies
                WHERE ISBN = ?
                AND UCID NOT IN (SELECT UCID FROM Loans WHERE ReturnDate IS NULL)
            """, (ISBN,))
            StartingStock = self.__Curs.fetchone()[0]
            # The Timeline is a sorted list of [date, delta] pairs representing every day within the
            # loan window on which the available stock changes, and by how much (+ve = stock increases,
            # -ve = stock decreases). Binary search keeps it sorted as events are inserted or merged
            Timeline = []
            # Phase 1: loan return events
            # Each active loan for this book that is due back within the window will return a copy,
            # increasing available stock by 1 on its due date
            # Loans issued after today but before DueDate are not included - they do not exist yet
            self.__Curs.execute("""
                SELECT Loans.DueDate
                FROM Loans
                INNER JOIN Copies ON Loans.UCID = Copies.UCID
                WHERE Copies.ISBN = ?
                AND Loans.ReturnDate IS NULL AND Loans.DueDate BETWEEN ? AND ?
            """,(ISBN, LoanDate, DueDate))
            for row in self.__Curs.fetchall():
                ReturnDate = int(row[0])
                # Binary search: find the position of this date in the sorted Timeline
                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == ReturnDate:
                        # This date already has an event - merge by incrementing the delta
                        Timeline[Mid][1] += 1
                        Found = True
                        break 
                    elif Timeline[Mid][0] < ReturnDate:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    # New date - insert at the position Left now points to, maintaining sort order
                    Timeline.insert(Left, [ReturnDate, 1])
            # Phase 2: reservation events
            # Each reservation reduces stock by its Quantity on the reservation date, and restores it
            # the following day. This models a reservation as a one-day commitment - the books are needed
            # that day only, and are free again afterwards
            self.__Curs.execute("""
                SELECT ReservationDate, Quantity
                FROM Reservations
                WHERE ISBN = ? AND ReservationDate BETWEEN ? AND ?
            """,(ISBN, LoanDate, DueDate))
            for row in self.__Curs.fetchall():
                ResDate = int(row[0])
                Qty = row[1]
                # Binary search: insert or merge a stock reduction on the reservation date
                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == ResDate:
                        # Merge: subtract the reserved quantity from any existing event on this date
                        Timeline[Mid][1] -= Qty
                        Found = True
                        break 
                    elif Timeline[Mid][0] < ResDate:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    Timeline.insert(Left, [ResDate, -Qty])
                # timedelta is used here rather than simple integer arithmetic because dates are stored
                # as integers in YYYYMMDD format - adding 1 would break at month and year boundaries
                DateObj = datetime.strptime(str(ResDate), "%Y%m%d")
                NextDay = int((DateObj + timedelta(days=1)).strftime("%Y%m%d"))
                # Binary search: insert or merge the stock restoration on the day after the reservation
                Left = 0
                Right = len(Timeline) - 1
                Found = False
                while Left <= Right:
                    Mid = (Left + Right) // 2
                    if Timeline[Mid][0] == NextDay:
                        # Merge: restore the quantity into any existing event on this date
                        Timeline[Mid][1] += Qty
                        Found = True
                        break 
                    elif Timeline[Mid][0] < NextDay:
                        Left = Mid + 1
                    else:
                        Right = Mid - 1
                if not Found:
                    Timeline.insert(Left, [NextDay, Qty])
            # Phase 3: simulate the running balance
            # Subtract 1 from starting stock to account for the new loan being proposed
            RunningBalance = StartingStock - 1
            # If already negative, there are no free copies right now - reject immediately
            if RunningBalance < 0:
                return False
            # Apply each event in chronological order. If the balance goes negative at any point,
            # it means the proposed loan would leave insufficient stock to fulfil a reservation
            # or accommodate a returning copy's absence - reject
            for Event in Timeline:
                RunningBalance += Event[1]
                if RunningBalance < 0:
                    return False
            # Balance never went negative throughout the entire loan window - safe to issue
            return True
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"Conflict Check Error: {e}")
            return False
# --- Getter Methods --- 
    def GetAuthorDetails(self, UAID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve author details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves and returns author details
            self.__Curs.execute("""
                SELECT UAID, Forename, Middlenames, Surname
                FROM Authors
                WHERE UAID = ?
            """, (UAID,))
            # Logs and returns as a tuple
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for author {UAID}")
            return self.__Curs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for author {UAID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetBookDetails(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve book details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves book details including all linked authors
            self.__Curs.execute("""
                SELECT Books.ISBN, Books.Title, Authors.Forename, Authors.Middlenames, Authors.Surname, Books.Genre, Books.Subject
                FROM Books
                JOIN BooksAuthors ON Books.ISBN = BooksAuthors.ISBN
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
                WHERE Books.ISBN = ?
            """, (ISBN,))
            # Logs and returns as a list of tuples (one per author)
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for book {ISBN}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for book {ISBN} and encountered an error: {e}")
            return f"System error: {e}"
     
    def GetAuthors(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve authors for book: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all authors linked to the given book
            self.__Curs.execute("""
                SELECT Authors.UAID, Authors.Forename, Authors.Middlenames, Authors.Surname
                FROM BooksAuthors
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
                WHERE BooksAuthors.ISBN = ?
            """, (ISBN,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved author details for book {ISBN}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve author details for book {ISBN} and encountered an error: {e}")
            return f"System error: {e}"

    def GetCopyDetails(self, UCID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve copy details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves copy details including both home and current location names
            self.__Curs.execute("""
                SELECT Copies.UCID, Books.Title, Books.ISBN, CurrentLoc.ClassCode, HomeLoc.ClassCode
                FROM Copies
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Locations AS CurrentLoc ON Copies.CurrentLocationID = CurrentLoc.ULocID
                JOIN Locations AS HomeLoc ON Copies.HomeLocationID = HomeLoc.ULocID
                WHERE Copies.UCID = ?
            """, (UCID,))
            # Logs and returns as a tuple
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for copy {UCID}")
            return self.__Curs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for copy {UCID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetLoanDetails(self, ULoanID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                return "Access Denied: Insufficient Permissions."
            # Retrieves loan details including book title and student name
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.LoanDate, Loans.DueDate, Loans.ReturnDate, Loans.UStuID, Loans.UStaID, Copies.UCID, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.ULoanID = ?
            """, (ULoanID,))
            # Logs and returns as a tuple
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for loan {ULoanID}")
            return self.__Curs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for loan {ULoanID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetLocationDetails(self, ULocID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve location details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves and returns location details
            self.__Curs.execute("""
                SELECT ULocID, ClassCode
                FROM Locations
                WHERE ULocID = ?
            """, (ULocID,))
            # Logs and returns as a tuple
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for location {ULocID}")
            return self.__Curs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for location {ULocID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetReservationDetails(self, URID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve reservation details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves reservation details including staff name and location
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity, Reservations.UStaID, Staff.Forename, Staff.Surname, Locations.ClassCode
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                JOIN Locations ON Reservations.ULocID = Locations.ULocID
                WHERE Reservations.URID = ?
            """, (URID,))
            # Logs and returns as a tuple
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved details for reservation {URID}")
            return self.__Curs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve details for reservation {URID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllAuthors(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all authors: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all authors
            self.__Curs.execute("""
                SELECT UAID, Forename, Middlenames, Surname
                FROM Authors
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all authors")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all authors and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllBooks(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all books: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all books including linked author names
            self.__Curs.execute("""
                SELECT Books.ISBN, Books.Title, Authors.Forename, Authors.Middlenames, Authors.Surname, Books.Genre, Books.Subject
                FROM Books
                JOIN BooksAuthors ON Books.ISBN = BooksAuthors.ISBN
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all books")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all books and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllBooksAuthored(self, UAID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve books for author: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all books linked to the given author
            self.__Curs.execute("""
                SELECT Books.ISBN, Books.Title, Authors.UAID, Authors.Forename, Authors.Middlenames, Authors.Surname
                FROM Books
                JOIN BooksAuthors ON Books.ISBN = BooksAuthors.ISBN
                JOIN Authors ON BooksAuthors.UAID = Authors.UAID
                WHERE Authors.UAID = ?
            """, (UAID,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved all books for author {UAID}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve books for author {UAID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllCopies(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all copies: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all copies including home and current location names
            self.__Curs.execute("""
                SELECT Copies.UCID, Books.Title, Books.ISBN, CurrentLoc.ClassCode, HomeLoc.ClassCode
                FROM Copies
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Locations AS CurrentLoc ON Copies.CurrentLocationID = CurrentLoc.ULocID
                JOIN Locations AS HomeLoc ON Copies.HomeLocationID = HomeLoc.ULocID
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all copies")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all copies and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllCopiesByISBN(self, ISBN):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve copies for book: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all copies of a specific book including location names
            self.__Curs.execute("""
                SELECT Copies.UCID, Books.Title, Books.ISBN, CurrentLoc.ClassCode, HomeLoc.ClassCode
                FROM Copies
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Locations AS CurrentLoc ON Copies.CurrentLocationID = CurrentLoc.ULocID
                JOIN Locations AS HomeLoc ON Copies.HomeLocationID = HomeLoc.ULocID
                WHERE Books.ISBN = ?
            """, (ISBN,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all copies for book {ISBN}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of copies for book {ISBN} and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllLoans(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all loans including book title and student name
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.LoanDate, Loans.DueDate, Loans.ReturnDate, Loans.UStuID, Loans.UStaID, Copies.UCID, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all loans")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all loans and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllActiveLoans(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all active loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all loans with no return date (i.e. still active)
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.LoanDate, Loans.DueDate, Loans.UStuID, Loans.UStaID, Copies.UCID, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.ReturnDate IS NULL
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all active loans")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of active loans and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllLoansByStudent(self, UStuID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve loans for student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all loans for a specific student
            self.__Curs.execute("""
                SELECT Loans.ULoanID, Books.Title, Loans.LoanDate, Loans.DueDate, Loans.ReturnDate, Loans.UStaID, Copies.UCID, Students.Forename, Students.Surname
                FROM Loans
                JOIN Copies ON Loans.UCID = Copies.UCID
                JOIN Books ON Copies.ISBN = Books.ISBN
                JOIN Students ON Loans.UStuID = Students.UStuID
                WHERE Loans.UStuID = ?
            """, (UStuID,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all loans for student {UStuID}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of loans for student {UStuID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllLocations(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all locations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all locations
            self.__Curs.execute("""
                SELECT ULocID, ClassCode
                FROM Locations
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all locations")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all locations and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllReservations(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve all reservations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all reservations including staff name and location
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity, Reservations.UStaID, Staff.Forename, Staff.Surname, Locations.ClassCode
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                JOIN Locations ON Reservations.ULocID = Locations.ULocID
            """)
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all reservations")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of all reservations and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllReservationsByStaff(self, UStaID):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve reservations for staff member: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves all reservations made by a specific staff member
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity, Reservations.UStaID, Staff.Forename, Staff.Surname, Locations.ClassCode
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                JOIN Locations ON Reservations.ULocID = Locations.ULocID
                WHERE Reservations.UStaID = ?
            """, (UStaID,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all reservations made by staff member {UStaID}")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of reservations for staff member {UStaID} and encountered an error: {e}")
            return f"System error: {e}"

    def GetAllReservationsToday(self):
        try:
            # Permission check
            if self.__AM.CheckPermission("Teacher") != True:
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to retrieve today's reservations: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Generates today's date for filtering
            Today = int(datetime.now().strftime("%Y%m%d"))
            # Retrieves all reservations for today
            self.__Curs.execute("""
                SELECT Reservations.URID, Books.Title, Reservations.ReservationDate, Reservations.Quantity, Reservations.UStaID, Staff.Forename, Staff.Surname, Locations.ClassCode
                FROM Reservations
                JOIN Books ON Reservations.ISBN = Books.ISBN
                JOIN sysconfig.Staff AS Staff ON Reservations.UStaID = Staff.UStaID
                JOIN Locations ON Reservations.ULocID = Locations.ULocID
                WHERE Reservations.ReservationDate = ?
            """, (Today,))
            # Logs and returns as a list of tuples
            self.__AM.Log(f"{self.__AM.GetCurrentUser()} retrieved a list of all reservations for today")
            return self.__Curs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser()} attempted to retrieve a list of reservations for today and encountered an error: {e}")
            return f"System error: {e}"