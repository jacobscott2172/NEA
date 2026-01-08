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
from datetime import datetime
# Imports the LibraryManager class for the GetNextID method
from LibraryManager import LibraryManager

class AccountManager:

    def __init__ (self):
        # Establishes class variables for relevant connections and cursors
        self.__SysConn = sqlite3.connect("Databases/SystemConfig.db")
        self.__SysCurs = self.__SysConn.cursor()
        self.__LibConn = sqlite3.connect("Databases/LibraryData.db")
        self.__LibCurs = self.__LibConn.cursor()
        self.__CurrentUser = "None"
        self.__CurrentAccessLevel = "None"

    def AddStaff(self, Password, Forename, Surname, AccessLevel):
        Salt = uuid.uuid4().hex
        PasswordHash = hashlib.sha256(Salt.encode() + Password.encode()).hexdigest()
        ID = LibraryManager.GetNextID(self.__SysCurs, "Staff", "UStaID")
        self.__SysCurs.execute(
            "INSERT INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel)  VALUES (?, ?, ?, ?, ?, ?)",
            (ID, PasswordHash, Salt, Forename, Surname, AccessLevel)
        )
        self.__SysConn.commit()
        return "Staff added successfully"
    
    def ChangePassword(self, ID, NewPassword):
        Salt = uuid.uuid4().hex
        PasswordHash = hashlib.sha256(Salt.encode() + NewPassword.encode()).hexdigest()
        self.__SysCurs.execute(
            "UPDATE Staff SET PasswordHash = ?, Salt = ? WHERE UStaID = ?",
            (PasswordHash, Salt, ID)
        )

    def SetAccountStatus(self, TargetID, IsStaff, MakeActive):
        Table = "Staff" if IsStaff else "Students"
        IDCol = "UStaID" if IsStaff else "UStuID"
        Conn = self.__SysConn if IsStaff else self.__LibConn
        Curs = self.__SysCurs if IsStaff else self.__LibCurs
        DateValue = int(datetime.now().strftime("%Y%m%d")) if not MakeActive else None
        Curs.execute(
            f"UPDATE {Table} SET AccountActive = ?, InactiveDate = ? WHERE {IDCol} = ?",
            (MakeActive, DateValue, TargetID)
        )
        Conn.commit()

    def AddStudent(self, Forename, Surname, EntryYear):
        self.__SysCurs.execute(
            "SELECT SettingValue from Settings where SettingName = 'DefaultMaxLoans'",
        )
        MaxLoans = self.__SysCurs.fetchone()
        ID = LibraryManager.GetNextID(self.__LibCurs, "Students", "UStuID")
        self.__LibCurs.execute(
            "INSERT INTO Students (UStuID, Forename, Surname, MaxActiveLoans, EntryYear)  VALUES (?, ?, ?, ?, ?)",
            (ID, Forename, Surname, MaxLoans[0], EntryYear)
        )
        self.__LibConn.commit()
    
    def LogIn(self, InputID, InputPassword):
        self.__SysCurs.execute(
            "SELECT * from Staff where UStaID = ?",
            (InputID,)
        )
        row = self.__SysCurs.fetchone()
        if row is None:
            return "Invalid ID or Password"
        InputPassword = hashlib.sha256(row[2].encode() + InputPassword.encode()).hexdigest()
        if InputPassword != row[1]:
            return "Invalid ID or Password"
        self.__CurrentUser = str(row[0])
        self.__CurrentAccessLevel = str(row[5])
        return f"Logged in successfully as {row[3]} {row[4]}"
    
    def PromoteStaff (self, ID):
        self.__SysCurs.execute(
            "SELECT AccessLevel FROM Staff WHERE UStaID = ?",
            (ID,)
        )
        OldLevel = self.__SysCurs.fetchone()[0]
        if OldLevel == "Teacher":
            NewLevel = "Admin"
        elif OldLevel == "Admin":
            NewLevel = "SysAdmin"
        else:
            return "Cannot promote, no role higher than SysAdmin"
        self.__SysCurs.execute(
            "UPDATE Staff SET Accesslevel = ? WHERE UStaID = ?",
            (NewLevel, ID)
        )
        self.__SysConn.commit()
        return f"Promoted successfully to {NewLevel}"
    
    def DemoteStaff (self, ID):
        self.__SysCurs.execute(
            "SELECT AccessLevel FROM Staff WHERE UStaID = ?",
            (ID,)
        )
        OldLevel = self.__SysCurs.fetchone()[0]
        if OldLevel == "Admin":
            NewLevel = "Teacher"
        elif OldLevel == "SysAdmin":
            NewLevel = "Admin"
        else:
            return "Cannot Demote, no role lower than Teacher"
        self.__SysCurs.execute(
            "UPDATE Staff SET Accesslevel = ? WHERE UStaID = ?",
            (NewLevel, ID)
        )
        self.__SysConn.commit()
        return f"Demoted successfully to {NewLevel}"

AM = AccountManager()
print(AM.DemoteStaff(4))