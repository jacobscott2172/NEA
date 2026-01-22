import sqlite3
from AccountManager import AccountManager

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
                self.__AM.Log(f"{self.__AM.GetCurrentUser()} attempted to add a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Duplicate check
            self.__LibCurs.execute(
                "SELECT UAID FROM Authors WHERE Forename = ? AND Middlename = ? AND Surname = ?",
                (Forename, Middlename, Surname)
            )
            ExistingAuthor = self.__LibCurs.fetchone()
            if ExistingAuthor:
                # Author already exists, return their UAID
                return f"Author already exists. ID: {ExistingAuthor[0]}"
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
            return "Author added successfully"
        # Error handling amd logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser} attempted to add a student and encountered an error: {e}")
            return f"System error: {e}"

###########
# IMPROVE #
########### 
    def AddBook(self, ISBN, Title, Genre, Subject, LearnerLevel, YearGroup):
        try:
            # Permission check
            if self.__AM.CheckPermission("Admin") != True:
                return "Access Denied: Insufficient Permissions."
            # No ID to be generated as ISBNs are unique
            # Validation of the user inputted ISBN
            ISBN = str(ISBN)
            if len(ISBN) != 13:
                return "Invalid length ISBN. Only 13 digit format accepted"
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
                return "Invalid check digit. Check you inputted the ISBN correctly"
            self.__Curs.execute(
                "INSERT INTO Books (ISBN, Title, Genre, Subject, LearnerLevel, YearGroup) VALUES (?, ?, ?, ?, ?, ?)",
                (ISBN, Title, Genre, Subject, LearnerLevel, YearGroup)
            )
        # Error handling amd logging
        except Exception as e:
            self.__AM.Log(f"User {self.__AM.GetCurrentUser} attempted to add a book and encountered an error: {e}")
            return f"System error: {e}"
            