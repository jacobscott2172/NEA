# This class contains all of the methods for adding, removing, promoting (etc.) accounts
# It also contains the method for logging in, and stores the ID of the currently logged in user
# It requires a connection to the LibraryData database in order to edit student accounts
# This file contains raw methods

# Imports SQLite for database operations
import sqlite3
# Used for random salt generation in password hashing
import uuid
# Used to hash passwords
import hashlib
# Used for automatic date generation when setting accounts to inactive
import datetime
# Imports the LibraryManager class for the GetNextID method
from LibraryManager import LibraryManager

class AccountManager:

    def __init__ (self):
        # Establishes class variables for relevant connections and cursors
        self.__StaffConn = sqlite3.connect("Databases/StaffLogins.db")
        self.__StaffCurs = self.__StaffConn.cursor()
        self.__LibConn = sqlite3.connect("Databases/LibraryData.db")
        self.__LibCurs = self.__LibConn.cursor()
        self.__CurrentUser = "None"
        self.__CurrentAccessLevel = "None"

    def AddStaff(self, Password, Forename, Surname, AccessLevel):
        Salt = uuid.uuid4().hex
        PasswordHash = hashlib.sha256(Salt.encode() + Password.encode()).hexdigest()
        ID = LibraryManager.GetNextID(self.__StaffCurs, "Staff", "UStaID")
        self.__StaffCurs.execute(
            "INSERT INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel)  VALUES (?, ?, ?, ?, ?, ?)",
            (ID, PasswordHash, Salt, Forename, Surname, AccessLevel)
        )
        self.__StaffConn.commit()
        return "Staff added successfully"
    
    def LogIn(self, InputID, InputPassword):
        self.__StaffCurs.execute(
            "SELECT * from Staff where UStaID = ?",
            (InputID,)
        )
        row = self.__StaffCurs.fetchone()
        if row is None:
            return "Invalid ID or Password"
        InputPassword = hashlib.sha256(row[2].encode() + InputPassword.encode()).hexdigest()
        if InputPassword != row[1]:
            return "Invalid ID or Password"
        self.__CurrentUser = str(row[0])
        self.__CurrentAccessLevel = str(row[5])
        return f"Logged in successfully as {row[3]} {row[4]}"
        

AM = AccountManager()
print(AM.AddStaff("password", "Example", "SysAdmin", "SysAdmin"))