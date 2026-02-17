# This class contains all of the methods for adding, removing, promoting (etc.) accounts
# It also contains the method for logging in, and stores the ID of the currently logged in user
# It requires a connection to the LibraryData database in order to edit student accounts

# Imports SQLite for database operations
import sqlite3
# Used for random salt generation in password hashing
import uuid
# Used to hash passwords
import hashlib
# Used for automatic date generation when setting accounts to inactive
from datetime import datetime

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
            self.__LogFile = open("Log.txt", "a")
        except Exception as e:  
            print(f"Initialization Error: {e}")
    
    def __del__(self):
        try:
            self.__SysConn.commit()
            self.__SysConn.close()
            self.__LibConn.commit()
            self.__LibConn.close()
            self.__LogFile.flush()
            self.__LogFile.close()
        except AttributeError:
            pass

# --- Adding / Removing accounts ---
    def AddStaff(self, Password, Forename, Surname, AccessLevel):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to add staff: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Salt generation and Hashing
            Salt = uuid.uuid4().hex
            PasswordHash = hashlib.sha256(Salt.encode() + Password.encode()).hexdigest()
            # Finds next free ID
            ID = self.GetNextID(self.__SysCurs, "Staff", "UStaID")
            # Inserts Data
            self.__SysCurs.execute(
                "INSERT INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel)  VALUES (?, ?, ?, ?, ?, ?)",
                (ID, PasswordHash, Salt, Forename, Surname, AccessLevel)
            )
            # Commits, Logs, returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} added staff member {ID}")
            return "Staff added successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to add staff and encountered an error: {e}")
            return f"System error: {e}"
    
    def RemoveStaff(self, ID):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to remove staff: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to remove staff: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Self-deletion check
            if ID == self.__CurrentUser:
                self.Log(f"{self.__CurrentUser} attempted to delete their own account")
                return "Error: You cannot delete your own account"
            # Deletes data
            self.__SysCurs.execute(
                "DELETE FROM Staff WHERE UStaID = (?)",
                (ID,)
            )
            # Commits, logs, returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} removed staff member {ID}")
            return "Staff removed successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to remove staff and encountered an error: {e}")
            return f"System error: {e}"

    def AddStudent(self, Forename, Surname, EntryYear):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to add a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves default max loan amount
            self.__SysCurs.execute(
                "SELECT SettingValue from Settings where SettingName = 'DefaultMaxLoans'",
            )
            MaxLoans = self.__SysCurs.fetchone()
            # Finds next free ID
            ID = self.GetNextID(self.__LibCurs, "Students", "UStuID")
            # Inserts new data
            self.__LibCurs.execute(
                "INSERT INTO Students (UStuID, Forename, Surname, MaxActiveLoans, EntryYear)  VALUES (?, ?, ?, ?, ?)",
                (ID, Forename, Surname, int(MaxLoans[0]), EntryYear)
            )
            # Commits, Logs, Returns confirmation
            self.Log(f"User {self.__CurrentUser} added student {ID}")
            self.__LibConn.commit()
            return "Student added successfully"
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to add a student and encountered an error: {e}")
            return f"System error: {e}"

    def RemoveStudent(self, ID):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to remove a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__LibCurs, "Students", "UStuID", ID):
                self.Log(f"{self.__CurrentUser} attempted to remove a student: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Removes student with the given ID
            self.__LibCurs.execute(
                "DELETE FROM Students WHERE UStuID = (?)",
                (ID,)
            )
            # Commits, Logs, returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} removed student {ID}")
            return "Student removed successfully"
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to remove a student and encountered an error: {e}")
            return f"System error: {e}"

    def BatchImportStudents(self, FilePath):
        # Permission Check
        if self.CheckPermission("Admin") != True:
            self.Log(f"{self.__CurrentUser} attempted to batch import students: Insufficient permissions")
            return "Access Denied: Insufficient Permissions."
        try:
            # Opens a .txt or .csv file and begins counting the number of students imported
            Count = 0
            with open(FilePath, "r") as File:
                # Skips a header line
                next(File)
                for Line in File:
                    # Splits the data by commas, then inputs each student line by line
                    Data = Line.strip().split(",")
                    if len(Data) == 3:
                        try:
                            Forename = Data[0]
                            Surname = Data[1]
                            EntryYear = int(Data[2])
                            self.AddStudent(Forename, Surname, EntryYear)
                            Count += 1
                        # Error handling: ValueError (i.e entry year is inputted as "Two Thousand and Twenty Five" instead of 2025)
                        except ValueError:
                            self.Log(f"Batch Import: Skipping invalid year data in line: {Line}")
                    # Error handling: erroneous line length
                    else:
                        self.Log(f"Batch Import: Skipping malformed line: {Line}")
            # Logs number imported and returns confirmation
            self.Log(f"User {self.__CurrentUser} batch imported {Count} students")
            return f"Successfully imported {Count} students from {FilePath}."
        # Specific error handling if the file is not found
        except FileNotFoundError:
            return "Error: The specified file was not found."
        # Other error handling
        except Exception as e:
            return f"An error occurred during import: {e}"

    def PurgeOldAccounts(self, MonthsToKeep):
        # Permission check
        if self.CheckPermission("Admin") != True:
            self.Log(f"{self.__CurrentUser} attempted to purge old accounts: Insufficient permissions")
            return "Access Denied: Insufficient Permissions."
        try:
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
            # Deletes students, Also ensures that inactive accounts cannot be deleted if they have outstanding loans
            self.__LibCurs.execute("""
                DELETE FROM Students WHERE AccountActive = 0 AND InactiveDate < ? 
                AND UStuID NOT IN (SELECT BorrowerID FROM Loans WHERE ReturnedDate IS NULL)""", 
                (CutOffDate,)
                )
            # Counts deleted accounts
            StudentsDeleted = self.__LibCurs.rowcount
            # Deletes staff
            self.__SysCurs.execute(
                "DELETE FROM Staff WHERE AccountActive = 0 AND InactiveDate < ?", 
                (CutOffDate,)
            )
            # Coounts deleted accounts
            StaffDeleted = self.__SysCurs.rowcount
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} purged {StudentsDeleted} students and {StaffDeleted} staff inactive since before {CutOffDate}")
            return f"Purged {StudentsDeleted} students and {StaffDeleted} staff inactive since before {CutOffDate}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to remove a student and encountered an error: {e}")
            return f"System error: {e}"

# --- Account editing ---
    def ChangePassword(self, ID, NewPassword):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to change password of staff {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to change a password: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # New salt generation and password hashing
            Salt = uuid.uuid4().hex
            PasswordHash = hashlib.sha256(Salt.encode() + NewPassword.encode()).hexdigest()
            # Updates, commits, logs, returns confirmation
            self.__SysCurs.execute(
                "UPDATE Staff SET PasswordHash = ?, Salt = ? WHERE UStaID = ?",
                (PasswordHash, Salt, ID)
            )
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed password for staff member {ID}")
            return "Passowrd changed"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to change password for staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"

    def SetAccountStatus(self, ID, IsStaff, MakeActive):
        try:
            # Determines the necessary table, column, etc depending on if a staff or student account is having its status changed
            Table = "Staff" if IsStaff else "Students"
            IDCol = "UStaID" if IsStaff else "UStuID"
            Conn = self.__SysConn if IsStaff else self.__LibConn
            Curs = self.__SysCurs if IsStaff else self.__LibCurs
            # Generates strings for Logging
            AccType = "Staff" if IsStaff else "Student"
            StatusStr = "Active" if MakeActive else "Inactive"
            # Generates date of inactivity / removes inactive date if being made active
            Date = int(datetime.now().strftime("%Y%m%d")) if not MakeActive else None
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to set {AccType} account {ID} to {StatusStr}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(Curs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to change the status of a {AccType} account to {StatusStr}: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Updates data
            Curs.execute(
                f"UPDATE {Table} SET AccountActive = ?, InactiveDate = ? WHERE {IDCol} = ?",
                (MakeActive, Date, ID)
            )
            # Commits, logs, returns confirmation
            Conn.commit()
            self.Log(f"User {self.__CurrentUser} set {AccType} account {ID} to {StatusStr}")
            return "Activity status changed"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to set {AccType} account {ID} to {StatusStr} and encountered an error: {e}")
            return f"System error: {e}"
    
    def PromoteStaff (self, ID):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted promote staff member {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to promote staff: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Self-Promotion Check
            elif ID == self.__CurrentUser:
                self.Log(f"{self.__CurrentUser} attempted to self-promote")
                return "Access Denied: you cannot promote yourself."
            # Finds the current access level given ID
            self.__SysCurs.execute(
                "SELECT AccessLevel FROM Staff WHERE UStaID = ?",
                (ID,)
            )
            # Automatically selects the next highest access level
            OldLevel = self.__SysCurs.fetchone()[0]
            if OldLevel == "Teacher":
                NewLevel = "Admin"
            elif OldLevel == "Admin":
                NewLevel = "SysAdmin"
            else:
                return "Cannot promote, no role higher than SysAdmin"
            # Changes to next highest access level
            self.__SysCurs.execute(
                "UPDATE Staff SET Accesslevel = ? WHERE UStaID = ?",
                (NewLevel, ID)
            )
            # Commits, Logs, returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} promoted user {ID} to {NewLevel}")
            return f"Promoted successfully to {NewLevel}"
        # Error Handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to promote staff member {ID} to {NewLevel} and encountered an error: {e}")
            return f"System error: {e}"
          
    def DemoteStaff (self, ID):
        try:
            # Permission Check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to demote staff member {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to demote staff: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Self-Demotion Check
            elif ID == self.__CurrentUser:
                self.Log(f"{self.__CurrentUser} attempted to self-demote")
                return "Access Denied: you cannot demote yourself."
            # Finds the current access level given ID
            self.__SysCurs.execute(
                "SELECT AccessLevel FROM Staff WHERE UStaID = ?",
                (ID,)
            )
            # Automatically selects the next lowest access level
            OldLevel = self.__SysCurs.fetchone()[0]
            if OldLevel == "Admin":
                NewLevel = "Teacher"
            elif OldLevel == "SysAdmin":
                NewLevel = "Admin"
            else:
                return "Cannot Demote, no role lower than Teacher"
            # Changes to next highest access level
            self.__SysCurs.execute(
                "UPDATE Staff SET Accesslevel = ? WHERE UStaID = ?",
                (NewLevel, ID)
            )
            # Commits, Logs, returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} demoted user {ID} to {NewLevel}")
            return f"Demoted successfully to {NewLevel}"
        # Error Handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to demote   staff member {ID} to {NewLevel} and encountered an error: {e}")
            return f"System error: {e}"

# --- Default settings editing ---
    def UpdateStudentMaxLoans(self, ID, MaxLoans):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update max loans for student {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__LibCurs, "Students", "UStuID", ID):
                self.Log(f"{self.__CurrentUser} attempted to update a student's max loans: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Retrieves student name for clarity in confirmation statement
            self.__LibCurs.execute(
                "SELECT Forename, Surname FROM Students WHERE UStuID = ?", 
                (ID,)
                )
            Name = self.__LibCurs.fetchone()
            # Updates max loans for an ID specified student
            self.__LibCurs.execute(
                "UPDATE Students SET MaxActiveLoans = ? WHERE UStuID = ?",
                (MaxLoans, ID)
            )
            # Commits, Logs, and returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} changed maximum loans for student {ID} to {MaxLoans}")
            return f"Max Loans for student {Name[0]} {Name[1]} changed to {MaxLoans}"
        # Error handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted update max loans of student {ID} to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"
    
    def UpdateDefaultMaxLoans(self, MaxLoans):
        try:
            # Permission Check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update default max loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Updates Default max loans for new student accounts
            self.__SysCurs.execute(
                "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                (str(MaxLoans), "DefaultMaxLoans")
            )
            # Commits, Logs, and returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed maximum loans for default students to {MaxLoans}")
            return f"Changed default max loans to {MaxLoans}"
        # Error handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted default max loans to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"

    def UpdateDefaultLoanPeriod(self, LoanPeriod):
        try:
            # Permission Check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update default loan period: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Updates Default max loans for new student accounts
            self.__SysCurs.execute(
                "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                (str(LoanPeriod), "DefaultLoanPeriod")
            )
            # Commits, Logs, and returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed loan period for default students to {LoanPeriod}")
            return f"Changed default loan period to {LoanPeriod}"
        # Error handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted default max loans to {LoanPeriod} and encountered an error: {e}")
            return f"System error: {e}"
        
# --- Internal Logger ---
    def Log(self, message):
        # Generates current date and time (Not formatted to ISO 8601 to aid readability)
        CurrentDateTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        # Writes to Log.txt file
        self.__LogFile.write(f"{CurrentDateTime} - {message}\n")
        # Immediately pushes to Log.txt so logs can be read in real time
        self.__LogFile.flush()

# --- Log in/out ---
    def LogIn(self, InputID, InputPassword):
        try:
            # Selects the entire row with the supplied ID
            self.__SysCurs.execute(
                "SELECT * from Staff where UStaID = ?",
                (InputID,)
            )
            row = self.__SysCurs.fetchone()
            # If there's no row with that ID, The ID must be incorrect
            if row is None:
                self.Log(f"A user attempted to log in: Invalid ID")
                return "Invalid ID or Password"
            # Hashes the inputted password using the included salt
            InputPassword = hashlib.sha256(row[2].encode() + InputPassword.encode()).hexdigest()
            # If the password does not match that which is stored, it must be incorrect
            if InputPassword != row[1]:
                self.Log(f"A user attempted to log in: Invalid Password")
                return "Invalid ID or Password"
            #Assigns CurrentUser and CurrentAccessLevel their respective values
            self.__CurrentUser = str(row[0])
            self.__CurrentAccessLevel = str(row[5])
            # Logs the login and returns confirmation
            self.Log(f"User {self.__CurrentUser} logged in")
            return f"Logged in successfully as {row[3]} {row[4]}"
        #Error handling
        except Exception as e:
            self.Log(f"A user attempted to log in and encountered an error: {e}")
            return f"System error: {e}"

    def LogOut(self):
        # Logs logging out
        self.Log(f"User {self.__CurrentUser} logged out")
        # Sets current user and access level to None
        self.__CurrentUser = "None"
        self.__CurrentAccessLevel = "None"
        # Returns confirmation
        return "Logged out successfully"
    
# --- Getter Methods ---
    def GetAllStaff(self):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to view all staff details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Selects all staff details
            self.__SysCurs.execute("SELECT UStaID, Forename, Surname, AccessLevel, AccountActive FROM Staff")
            # Logs retrieval and returns all staff details as a list of tuples
            self.Log(f"User {self.__CurrentUser} retrieved all staff details")
            return self.__SysCurs.fetchall()
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve all staff details and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetAllStudents(self):
        try:
            # Permission check
            if self.CheckPermission("Teacher") != True:
                self.Log(f"{self.__CurrentUser} attempted to view all student details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Selects all staff details
            self.__LibCurs.execute("SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear FROM Students")
            # Logs retrieval and returns all staff details as a list of tuples
            self.Log(f"User {self.__CurrentUser} retrieved all student details")
            return self.__LibCurs.fetchall()
        # Error Handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve all student details and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetStaffDetails(self, ID):
        try:
            # Permission check
            if self.__CurrentUser != str(ID) and self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to view unauthorised staff details: Insufficient permissions")
                return "Access Denied: Insufficient permission to view others' details, you can only view your own"
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to retrieve staff details: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Retrieves details of 1 staff member - specified with ID
            self.__SysCurs.execute(
                "SELECT UStaID, Forename, Surname, AccessLevel, AccountActive FROM Staff WHERE UStaID = ?", 
                (ID,)
                )
            # Logs and returns details as a tuple
            self.Log(f"User {self.__CurrentUser} retrieved details of staff member {ID}")
            return self.__SysCurs.fetchone()
        # Error handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve details of staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetStudentDetails(self, ID):
        try:
            # Permission check
            if self.CheckPermission("Teacher") != True:
                self.Log(f"{self.__CurrentUser} attempted to view unauthorised student details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__LibCurs, "Students", "UStuID", ID):
                self.Log(f"{self.__CurrentUser} attempted to remove staff: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Retrieves details of 1 student - specified with ID
            self.__LibCurs.execute(
                "SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear FROM Students WHERE UStuID = ?", 
                (ID,)
                )
            # Logs and returns details as a tuple
            self.Log(f"User {self.__CurrentUser} retrieved details of student {ID}")
            return self.__LibCurs.fetchone()
        # Error handling
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve details of staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetCurrentUser(self):
        return self.__CurrentUser
    
    def GetCurrentAccessLevel(self):
        return self.__CurrentAccessLevel

# --- Checking methods ---
    def CheckPermission(self, NecessaryPerms):
        RoleHierarchy = {"None" : 0, "Teacher" : 1, "Admin" : 2, "SysAdmin" : 3}
        # Get numeric values, default to 0 if not found as to reduce bypass risk
        CurrentValue = RoleHierarchy.get(self.__CurrentAccessLevel, 0)
        NecessaryValue = RoleHierarchy.get(NecessaryPerms, 100) # Default to 100 so unknown perms fail
        # Compare values
        if self.__CurrentUser == "None":
            return "No User logged in"
        # Active account check
        if self.IsAccountActive(self.__SysCurs, "Staff", "UStaID", self.__CurrentUser) != True:
            return False
        # More value comparison
        if CurrentValue >= NecessaryValue:
            return True
        else:
            return False

    @staticmethod
    def CheckIDExists(Cursor, Table, IDColumn, ID):
        # Checks if an inputted ID exists, Used to find and detect typos in user input
        Cursor.execute(f"SELECT 1 FROM {Table} WHERE {IDColumn} = ?", (ID,)) 
        return Cursor.fetchone() is not None
    
    @staticmethod
    def GetNextID(Cursor, Table, IDColumn):
        # Finds the next available ID in a table. I prefer this over AutoIncrement as it fills in gaps, reducing overall database size
        Cursor.execute(f"SELECT {IDColumn} FROM {Table} ORDER BY {IDColumn} ASC")
        rows = Cursor.fetchall()
        # Isolates the list of tuples from .fetchall into a list of IDs
        existing_ids = [row[0] for row in rows]
        expected_id = 1
        # counts Up until the expected ID is either the end of the list, or finds a gap in the list
        for id in existing_ids:
            if id != expected_id:
                break
            expected_id += 1
        return expected_id
    
    @staticmethod
    def IsAccountActive(Cursor, Table, IDcolumn, ID):
        # Checks if an account is active, returns the boolean value
        Cursor.execute(
            f"SELECT AccountActive FROM {Table} WHERE {IDcolumn} = ?",
            (ID, )
        )
        return Cursor.fetchone()[0] == 1
       
    def CheckStaffMemberActive(self, ID):
        # Public method for making checks within the SystemConfig file, as LibraryManager will not have access to this
        return self.IsAccountActive(self.__SysCurs, "Staff", "UStaID", ID)

AM = AccountManager()