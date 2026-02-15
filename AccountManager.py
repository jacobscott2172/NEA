# This class contains all of the methods for adding, removing, promoting (etc.) accounts
# It also contains the method for logging in, and stores the ID of the currently logged in user
# It requires a connection to the LibraryData database in order to edit student accounts

# Imports SQLite for database operations
import sqlite3
# Used for random salt generation in password hashing
import uuid
# Used to hash passwords
import hashlib
# Used for automatic date generation when logging / setting accounts to inactive
from datetime import datetime
# Imports the LibraryManager class for the GetNextID method
from LibraryManager import LibraryManager

class AccountManager:

    def __init__ (self):
        try:
            # Establishes class variables for relevant connections and cursors
            self.__SysConn = sqlite3.connect("Databases/SystemConfig.db")
            self.__SysCurs = self.__SysConn.cursor()
            self.__LibConn = sqlite3.connect("Databases/LibraryData.db")
            self.__LibCurs = self.__LibConn.cursor()
            self.__CurrentUser = "None"
            self.__CurrentAccessLevel = "None"
            self.__Log = open("Log.txt", "a")
        except Exception as e:  
            print(f"Initialization Error: {e}")

    def AddStaff(self, Password, Forename, Surname, AccessLevel):
        try:
            if self.__CheckPermission("SysAdmin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to add staff: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            Salt = uuid.uuid4().hex
            PasswordHash = hashlib.sha256(Salt.encode() + Password.encode()).hexdigest()
            ID = LibraryManager.GetNextID(self.__SysCurs, "Staff", "UStaID")
            self.__SysCurs.execute(
                "INSERT INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel)  VALUES (?, ?, ?, ?, ?, ?)",
                (ID, PasswordHash, Salt, Forename, Surname, AccessLevel)
            )
            self.__SysConn.commit()
            self.__Log(f"User {self.__CurrentUser} added staff member {ID}")
            return "Staff added successfully"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to add staff and encountered an error: {e}")
            return f"System error: {e}"
    
    def RemoveStaff(self, ID):
        try:
            if self.__CheckPermission("SysAdmin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to remove staff: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__SysCurs.execute(
                "DELETE FROM Staff WHERE UStaID = (?)",
                (ID,)
            )
            self.__SysConn.commit()
            self.__Log(f"User {self.__CurrentUser} removed staff member {ID}")
            return "Staff removed successfully"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to remove staff and encountered an error: {e}")
            return f"System error: {e}"
    
    def ChangePassword(self, ID, NewPassword):
        try:
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to change password of staff {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            Salt = uuid.uuid4().hex
            PasswordHash = hashlib.sha256(Salt.encode() + NewPassword.encode()).hexdigest()
            self.__SysCurs.execute(
                "UPDATE Staff SET PasswordHash = ?, Salt = ? WHERE UStaID = ?",
                (PasswordHash, Salt, ID)
            )
            self.__Log(f"User {self.__CurrentUser} changed password for staff member {ID}")
            self.__SysConn.commit()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to change password for staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"

    def SetAccountStatus(self, TargetID, IsStaff, MakeActive):
        try:
            Table = "Staff" if IsStaff else "Students"
            IDCol = "UStaID" if IsStaff else "UStuID"
            Conn = self.__SysConn if IsStaff else self.__LibConn
            Curs = self.__SysCurs if IsStaff else self.__LibCurs
            AccType = "Staff" if IsStaff else "Student"
            StatusStr = "Active" if MakeActive else "Inactive"
            Date = int(datetime.now().strftime("%Y%m%d")) if not MakeActive else None
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to set {AccType} account {TargetID} to {StatusStr}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            Curs.execute(
                f"UPDATE {Table} SET AccountActive = ?, InactiveDate = ? WHERE {IDCol} = ?",
                (MakeActive, Date, TargetID)
            )

            self.__Log(f"User {self.__CurrentUser} set {AccType} account {TargetID} to {StatusStr}")
            Conn.commit()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to set {AccType} account {TargetID} to {StatusStr} and encountered an error: {e}")
            return f"System error: {e}"

    def AddStudent(self, Forename, Surname, EntryYear):
        try:
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to add a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__SysCurs.execute(
                "SELECT SettingValue from Settings where SettingName = 'DefaultMaxLoans'",
            )
            MaxLoans = self.__SysCurs.fetchone()
            ID = LibraryManager.GetNextID(self.__LibCurs, "Students", "UStuID")
            self.__LibCurs.execute(
                "INSERT INTO Students (UStuID, Forename, Surname, MaxActiveLoans, EntryYear)  VALUES (?, ?, ?, ?, ?)",
                (ID, Forename, Surname, MaxLoans[0], EntryYear)
            )
            self.__Log(f"User {self.__CurrentUser} added student {ID}")
            self.__LibConn.commit()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to add a student and encountered an error: {e}")
            return f"System error: {e}"

    def RemoveStudent(self, ID):
        try:
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to remove a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__LibCurs.execute(
                "DELETE FROM Students WHERE UStuID = (?)",
                (ID,)
            )
            self.__LibConn.commit()
            self.__Log(f"User {self.__CurrentUser} removed student {ID}")
            return "Student removed successfully"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to remove a student and encountered an error: {e}")
            return f"System error: {e}"
    
    def LogIn(self, InputID, InputPassword):
        try:
            self.__SysCurs.execute(
                "SELECT * from Staff where UStaID = ?",
                (InputID,)
            )
            row = self.__SysCurs.fetchone()
            if row is None:
                self.__Log(f"A user attempted to log in: Invalid ID")
                return "Invalid ID or Password"
            InputPassword = hashlib.sha256(row[2].encode() + InputPassword.encode()).hexdigest()
            if InputPassword != row[1]:
                self.__Log(f"A user attempted to log in: Invalid Password")
                return "Invalid ID or Password"
            self.__CurrentUser = str(row[0])
            self.__CurrentAccessLevel = str(row[5])
            self.__Log(f"User {self.__CurrentUser} logged in")
            return f"Logged in successfully as {row[3]} {row[4]}"
        except Exception as e:
            self.__Log(f"A user attempted to log in and encountered an error: {e}")
            return f"System error: {e}"
    
    def PromoteStaff (self, ID):
        try:
            if self.__CheckPermission("SysAdmin") != True:
                self.__Log(f"{self.__CurrentUser} attempted promote staff member {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
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
            self.__Log(f"User {self.__CurrentUser} promoted user {ID} to {NewLevel}")
            return f"Promoted successfully to {NewLevel}"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to promote staff member {ID} to {NewLevel} and encountered an error: {e}")
            return f"System error: {e}"
          
    def DemoteStaff (self, ID):
        try:
            if self.__CheckPermission("SysAdmin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to demote staff member {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            elif ID == self.__CurrentUser:
                self.__Log(f"{self.__CurrentUser} attempted to self-demote")
                return "Access Denied: you cannot demote yourself."
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
            self.__Log(f"User {self.__CurrentUser} demoted user {ID} to {NewLevel}")
            return f"Demoted successfully to {NewLevel}"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to demote   staff member {ID} to {NewLevel} and encountered an error: {e}")
            return f"System error: {e}"
    
    def __Log(self, message):
        CurrentDateTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        self.__Log.write(f"{CurrentDateTime} - {message}\n")
        self.__Log.flush()
    
    def __CheckPermission(self, NecessaryPerms):
        RoleHierarchy = {"None" : 0, "Teacher" : 1, "Admin" : 2, "SysAdmin" : 3}
        # Get numeric values, default to 0 if not found
        CurrentValue = RoleHierarchy.get(self.__CurrentAccessLevel, 0)
        NecessaryValue = RoleHierarchy.get(NecessaryPerms, 100) # Default to 100 so unknown perms fail
        
        if self.__CurrentUser == "None":
            return "No logged user"
            
        if CurrentValue >= NecessaryValue:
            return True
        else:
            return "Insufficient Permission"
        
    def GetStaffDetails(self, ID):
        try:
            if self.__CurrentUser != str(ID) and self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to view unauthorised staff details: Insufficient permissions")
                return "Access Denied: Insufficient permission to view others' details, you can only view your own"
            self.__SysCurs.execute(
                "SELECT UStaID, Forename, Surname, AccessLevel, AccountActive FROM Staff WHERE UStaID = ?", 
                (ID,)
                )
            self.__Log(f"User {self.__CurrentUser} retrieved details of staff member {ID}")
            return self.__SysCurs.fetchone()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to retrieve details of staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetStudentDetails(self, ID):
        try:
            if self.__CheckPermission("Teacher") != True:
                self.__Log(f"{self.__CurrentUser} attempted to view unauthorised student details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__LibCurs.execute(
                "SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear FROM Students WHERE UStuID = ?", 
                (ID,)
                )
            self.__Log(f"User {self.__CurrentUser} retrieved details of student {ID}")
            return self.__LibCurs.fetchone()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to retrieve details of staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"
    
    def UpdateStudentMaxLoans(self, ID, MaxLoans):
        try:
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to update max loans for student {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__LibCurs.execute(
                "SELECT Forename, Surname FROM Students WHERE UStuID = ?", 
                (ID,)
                )
            Name = self.__LibCurs.fetchone()
            self.__LibCurs.execute(
                "UPDATE Students SET MaxActiveLoans = ? WHERE UStuID = ?",
                (MaxLoans, ID)
            )
            self.__LibConn.commit()
            self.__Log(f"User {self.__CurrentUser} changed maximum loans for student {ID} to {MaxLoans}")
            return f"Max Loans for student {Name[0]} {Name[1]} changed to {MaxLoans}"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted update max loans of student {ID} to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"
    
    def UpdateDefaultMaxLoans(self, MaxLoans):
        try:
            if self.__CheckPermission("Admin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to update default max loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__SysCurs.execute(
                "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                (str(MaxLoans), "DefaultMaxLoans")
            )
            self.__SysConn.commit()
            self.__Log(f"User {self.__CurrentUser} changed maximum loans for default students to {MaxLoans}")
            return f"Changed default max loans to {MaxLoans}"
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted default max loans to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetAllStaff(self):
        try:
            if self.__CheckPermission("SysAdmin") != True:
                self.__Log(f"{self.__CurrentUser} attempted to view all staff details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__SysCurs.execute("SELECT UStaID, Forename, Surname, AccessLevel, AccountActive FROM Staff")
            self.__Log(f"User {self.__CurrentUser} retrieved all staff details")
            return self.__SysCurs.fetchall()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to retrieve all staff details and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetAllStudents(self):
        try:
            if self.__CheckPermission("Teacher") != True:
                self.__Log(f"{self.__CurrentUser} attempted to view all student details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            self.__LibCurs.execute("SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear FROM Students")
            self.__Log(f"User {self.__CurrentUser} retrieved all student details")
            return self.__LibCurs.fetchall()
        except Exception as e:
            self.__Log(f"User {self.__CurrentUser} attempted to retrieve all student details and encountered an error: {e}")
            return f"System error: {e}"
    
    def LogOut(self):
        self.__Log(f"User {self.__CurrentUser} logged out")
        self.__CurrentUser = "None"
        self.__CurrentAccessLevel = "None"
        return "Logged out successfully"
    
    def BatchImportStudents(self, FilePath):
        if self.__CheckPermission("Admin") != True:
            self.__Log(f"{self.__CurrentUser} attempted to batch import students: Insufficient permissions")
            return "Access Denied: Insufficient Permissions."
        try:
            Count = 0
            with open(FilePath, "r") as File:
                next(File)
                for Line in File:
                    Data = Line.strip().split(",")
                    if len(Data) == 3:
                        Forename = Data[0]
                        Surname = Data[1]
                        EntryYear = int(Data[2])
                        self.AddStudent(Forename, Surname, EntryYear)
                        Count += 1
            self.__Log(f"User {self.__CurrentUser} batch imported {Count} students")
            return f"Successfully imported {Count} students from {FilePath}."
        except FileNotFoundError:
            return "Error: The specified file was not found."
        except Exception as e:
            return f"An error occurred during import: {e}"
        
    def SearchStudents(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            # Searches by Name or ID
            self.__LibCurs.execute(
                "SELECT UStuID, Forename, Surname, EntryYear FROM Students WHERE Forename LIKE ? OR Surname LIKE ? OR CAST(UStuID AS TEXT) LIKE ?",
                (Term, Term, Term)
            )
            Results = self.__LibCurs.fetchall()
            return Results if Results else f"Could not find any students matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"

    def SearchStaff(self, SearchTerm):
        try:
            Term = f"%{SearchTerm}%"
            # Searches the SystemConfig database for staff accounts
            self.__SysCurs.execute(
                "SELECT UStaID, Forename, Surname, AccessLevel FROM Staff WHERE Forename LIKE ? OR Surname LIKE ? OR CAST(UStaID AS TEXT) LIKE ?",
                (Term, Term, Term)
            )
            Results = self.__SysCurs.fetchall()
            return Results if Results else f"Could not find any staff accounts matching '{SearchTerm}'."
        except Exception as e:
            return f"Search Error: {e}"
    

AM = AccountManager()
