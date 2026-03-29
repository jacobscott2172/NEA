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
# Used for sending email notifications
import smtplib
from email.mime.text import MIMEText

class AccountManager:

    def __init__ (self):
        try:
            # Establishes class variables for relevant connections and cursors
            self.__SysConn = sqlite3.connect("Databases/SystemConfig.db")
            self.__SysCurs = self.__SysConn.cursor()
            self.__LibConn = sqlite3.connect("Databases/LibraryData.db")
            self.__LibCurs = self.__LibConn.cursor()
            self.__CurrentUser = None
            self.__CurrentAccessLevel = "None"
            self.__LogFile = open("Log.txt", "a")
        # Error handling and logging
        except Exception as e:  
            print(f"Initialization Error: {e}")
    
    def __del__(self):
        try:
            # Closes all database files, saves then closes the log file
            self.__SysConn.commit()
            self.__SysConn.close()
            self.__LibConn.commit()
            self.__LibConn.close()
            self.__LogFile.flush()
            self.__LogFile.close()
            self.__CurrentAccessLevel = "None"
            self.__CurrentUser =  None
        # Suppresses errors if __init__ failed before attributes were assigned
        except AttributeError:
            pass
    
    # Public wrapper for __del__, used when exiting the program.
    def Exit(self):
        self.__del__()

# --- Adding / Removing accounts ---
    def AddStaff(self, Password, Forename, Surname, AccessLevel, Email):
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
            # Inserts data
            self.__SysCurs.execute(
                "INSERT INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel, Email)  VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ID, PasswordHash, Salt, Forename, Surname, AccessLevel, Email)
            )
            # Commits, Logs, Returns confirmation
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
            if int(ID) == self.__CurrentUser:
                self.Log(f"{self.__CurrentUser} attempted to delete their own account")
                return "Error: You cannot delete your own account"
            # Deletes data
            self.__SysCurs.execute(
                "DELETE FROM Staff WHERE UStaID = (?)",
                (ID,)
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} removed staff member {ID}")
            return "Staff removed successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to remove staff and encountered an error: {e}")
            return f"System error: {e}"

    def AddStudent(self, Forename, Surname, EntryYear, Email):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to add a student: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Retrieves default max loan amount
            self.__SysCurs.execute(
                "SELECT SettingValue from Settings where SettingName = 'DefaultMaxLoans'",
            )
            MaxLoansRow = self.__SysCurs.fetchone()
            MaxLoans = int(MaxLoansRow[0]) if MaxLoansRow else 3
            # Finds next free ID
            ID = self.GetNextID(self.__LibCurs, "Students", "UStuID")
            # Inserts new data
            self.__LibCurs.execute(
                "INSERT INTO Students (UStuID, Forename, Surname, MaxActiveLoans, EntryYear, Email)  VALUES (?, ?, ?, ?, ?, ?)",
                (ID, Forename, Surname, MaxLoans, EntryYear, Email)
            )
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} added student {ID}")
            return "Student added successfully"
        # Error handling and logging
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
            # Outstanding loan check
            self.__LibCurs.execute(
                "SELECT COUNT(*) FROM Loans WHERE UStuID = ? AND ReturnDate IS NULL", (ID,)
            )
            if self.__LibCurs.fetchone()[0] > 0:
                return "Error: Student has outstanding loans and cannot be removed."
            # Removes student with the given ID
            self.__LibCurs.execute(
                "DELETE FROM Students WHERE UStuID = (?)",
                (ID,)
            )
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} removed student {ID}")
            return "Student removed successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to purge old accounts and encountered an error: {e}")
            return f"System error: {e}"

    def BatchImportStudents(self, FilePath):
        # Permission check
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
                    if len(Data) == 4:
                        try:
                            Forename = Data[0]
                            Surname = Data[1]
                            EntryYear = int(Data[2])
                            Email = Data[3].strip()
                            Result = self.AddStudent(Forename, Surname, EntryYear, Email)
                            # Only increments if AddStudent succeeded
                            if Result == "Student added successfully":
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
        # Error handling and logging
        except Exception as e:
            return f"An error occurred during import: {e}"

    def PurgeOldAccounts(self):
        # Permission check
        if self.CheckPermission("Admin") != True:
            self.Log(f"{self.__CurrentUser} attempted to purge old accounts: Insufficient permissions")
            return "Access Denied: Insufficient Permissions."
        try:
            # Retrieves retention period from settings
            MonthsToKeep = self.GetRetentionMonths()
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
                AND UStuID NOT IN (SELECT UStuID FROM Loans WHERE ReturnDate IS NULL)""", 
                (CutOffDate,)
                )
            # Counts deleted accounts
            StudentsDeleted = self.__LibCurs.rowcount
            # Deletes staff
            self.__SysCurs.execute(
                "DELETE FROM Staff WHERE AccountActive = 0 AND InactiveDate < ?", 
                (CutOffDate,)
            )
            # Counts deleted accounts
            StaffDeleted = self.__SysCurs.rowcount
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} purged {StudentsDeleted} students and {StaffDeleted} staff inactive since before {CutOffDate}")
            return f"Purged {StudentsDeleted} students and {StaffDeleted} staff inactive since before {CutOffDate}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to purge old accounts and encountered an error: {e}")
            return f"System error: {e}"

    def PurgeStudentsByEntryYear(self, EntryYear):
        # Permission check
        if self.CheckPermission("Admin") != True:
            self.Log(f"{self.__CurrentUser} attempted to purge students by entry year: Insufficient permissions")
            return "Access Denied: Insufficient Permissions."
        try:
            # Deletes inactive students from the given entry year with no outstanding loans
            self.__LibCurs.execute("""
                DELETE FROM Students
                WHERE EntryYear = ? AND AccountActive = 0
                AND UStuID NOT IN (SELECT UStuID FROM Loans WHERE ReturnDate IS NULL)
            """, (EntryYear,))
            StudentsDeleted = self.__LibCurs.rowcount
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} purged {StudentsDeleted} inactive students from entry year {EntryYear}")
            return f"Purged {StudentsDeleted} inactive students from entry year {EntryYear}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to purge students by entry year and encountered an error: {e}")
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
            # Updates password hash and salt
            self.__SysCurs.execute(
                "UPDATE Staff SET PasswordHash = ?, Salt = ? WHERE UStaID = ?",
                (PasswordHash, Salt, ID)
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed password for staff member {ID}")
            return "Password changed"
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
            # Generates strings for logging
            AccType = "Staff" if IsStaff else "Student"
            StatusStr = "Active" if MakeActive else "Inactive"
            # Generates date of inactivity / removes inactive date if being made active
            Date = int(datetime.now().strftime("%Y%m%d")) if not MakeActive else None
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to set {AccType} account {ID} to {StatusStr}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(Curs, Table, IDCol, ID):
                self.Log(f"{self.__CurrentUser} attempted to change the status of a {AccType} account to {StatusStr}: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Updates data
            Curs.execute(
                f"UPDATE {Table} SET AccountActive = ?, InactiveDate = ? WHERE {IDCol} = ?",
                (MakeActive, Date, ID)
            )
            # Commits, Logs, Returns confirmation
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
            # Self-promotion check
            elif int(ID) == self.__CurrentUser:
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
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} promoted user {ID} to {NewLevel}")
            return f"Promoted successfully to {NewLevel}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to promote staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"
          
    def DemoteStaff (self, ID):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to demote staff member {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to demote staff: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Self-demotion check
            elif int(ID) == self.__CurrentUser:
                self.Log(f"{self.__CurrentUser} attempted to self-demote")
                return "Access Denied: you cannot demote yourself. If you would like to be demoted, contact another System Admin or promote your replacement"
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
            # Changes to next lowest access level
            self.__SysCurs.execute(
                "UPDATE Staff SET Accesslevel = ? WHERE UStaID = ?",
                (NewLevel, ID)
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} demoted user {ID} to {NewLevel}")
            return f"Demoted successfully to {NewLevel}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to demote   staff member {ID} and encountered an error: {e}")
            return f"System error: {e}"

# --- Updating account details ---
    def UpdateStaffEmail(self, ID, Email):
        try:
            # Permission check: SysAdmins can update any staff email; staff can update their own
            if self.__CurrentUser != int(ID) and self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update email for staff {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to update email for staff {ID}: ID does not exist")
                return "Error: ID does not exist"
            # Updates email address
            self.__SysCurs.execute(
                "UPDATE Staff SET Email = ? WHERE UStaID = ?",
                (Email, ID)
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} updated email for staff member {ID}")
            return "Email updated successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to update email for staff {ID} and encountered an error: {e}")
            return f"System error: {e}"

    def UpdateStudentEmail(self, ID, Email):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update email for student {ID}: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Typo check
            if not self.CheckIDExists(self.__LibCurs, "Students", "UStuID", ID):
                self.Log(f"{self.__CurrentUser} attempted to update email for student {ID}: ID does not exist")
                return "Error: ID does not exist"
            # Updates email address
            self.__LibCurs.execute(
                "UPDATE Students SET Email = ? WHERE UStuID = ?",
                (Email, ID)
            )
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} updated email for student {ID}")
            return "Email updated successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to update email for student {ID} and encountered an error: {e}")
            return f"System error: {e}"

    def UpdateSMTPSettings(self, Host, Port, User, Password, Sender):
        try:
            # Permission check
            if self.CheckPermission("SysAdmin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update SMTP settings: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Builds a list of name/value pairs and updates each setting
            Settings = [("SMTPHost", Host), ("SMTPPort", str(Port)), ("SMTPUser", User), ("SMTPPassword", Password), ("SMTPSender", Sender)]
            for Name, Value in Settings:
                self.__SysCurs.execute(
                    "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                    (Value, Name)
                )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} updated SMTP settings")
            return "SMTP settings updated successfully"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to update SMTP settings and encountered an error: {e}")
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
            # Commits, Logs, Returns confirmation
            self.__LibConn.commit()
            self.Log(f"User {self.__CurrentUser} changed maximum loans for student {ID} to {MaxLoans}")
            return f"Max Loans for student {Name[0]} {Name[1]} changed to {MaxLoans}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted update max loans of student {ID} to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"
    
    def UpdateDefaultMaxLoans(self, MaxLoans):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update default max loans: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Updates Default max loans for new student accounts
            self.__SysCurs.execute(
                "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                (str(MaxLoans), "DefaultMaxLoans")
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed maximum loans for default students to {MaxLoans}")
            return f"Changed default max loans to {MaxLoans}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted default max loans to {MaxLoans} and encountered an error: {e}")
            return f"System error: {e}"

    def UpdateDefaultLoanPeriod(self, LoanPeriod):
        try:
            # Permission check
            if self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to update default loan period: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Updates default loan period for new loans
            self.__SysCurs.execute(
                "UPDATE Settings SET SettingValue = ? WHERE SettingName = ?",
                (str(LoanPeriod), "DefaultLoanPeriod")
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"User {self.__CurrentUser} changed loan period for default students to {LoanPeriod}")
            return f"Changed default loan period to {LoanPeriod}"
        # Error handling and logging
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
                "SELECT UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel, AccountActive, InactiveDate, Email FROM Staff WHERE UStaID = ?",
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
            # Assigns CurrentUser and CurrentAccessLevel their respective values
            self.__CurrentUser = int(row[0])
            self.__CurrentAccessLevel = str(row[5])
            # Logs the login and returns confirmation
            self.Log(f"User {self.__CurrentUser} logged in")
            return f"Logged in successfully as {row[3]} {row[4]}"
        # Error handling and logging
        except Exception as e:
            self.Log(f"A user attempted to log in and encountered an error: {e}")
            return f"System error: {e}"

    def LogOut(self):
        # Logs logging out
        self.Log(f"User {self.__CurrentUser} logged out")
        # Sets current user and access level to None
        self.__CurrentUser = None
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
            self.__SysCurs.execute("SELECT UStaID, Forename, Surname, AccessLevel, AccountActive, Email FROM Staff")
            # Logs retrieval and returns all staff details as a list of tuples
            self.Log(f"User {self.__CurrentUser} retrieved all staff details")
            return self.__SysCurs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve all staff details and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetAllStudents(self):
        try:
            # Permission check
            if self.CheckPermission("Teacher") != True:
                self.Log(f"{self.__CurrentUser} attempted to view all student details: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Selects all student details
            self.__LibCurs.execute("SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email FROM Students")
            # Logs retrieval and returns all student details as a list of tuples
            self.Log(f"User {self.__CurrentUser} retrieved all student details")
            return self.__LibCurs.fetchall()
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve all student details and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetStaffDetails(self, ID):
        try:
            # Permission check
            if self.__CurrentUser != int(ID) and self.CheckPermission("Admin") != True:
                self.Log(f"{self.__CurrentUser} attempted to view unauthorised staff details: Insufficient permissions")
                return "Access Denied: Insufficient permission to view others' details, you can only view your own"
            # Typo check
            if not self.CheckIDExists(self.__SysCurs, "Staff", "UStaID", ID):
                self.Log(f"{self.__CurrentUser} attempted to retrieve staff details: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Retrieves details of 1 staff member - specified with ID
            self.__SysCurs.execute(
                "SELECT UStaID, Forename, Surname, AccessLevel, AccountActive, Email FROM Staff WHERE UStaID = ?", 
                (ID,)
                )
            # Logs and returns details as a tuple
            self.Log(f"User {self.__CurrentUser} retrieved details of staff member {ID}")
            return self.__SysCurs.fetchone()
        # Error handling and logging
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
                self.Log(f"{self.__CurrentUser} attempted to retrieve student details: Input ID ({ID}) does not exist")
                return "Error: ID does not exist"
            # Retrieves details of 1 student - specified with ID
            self.__LibCurs.execute(
                "SELECT UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email FROM Students WHERE UStuID = ?", 
                (ID,)
                )
            # Logs and returns details as a tuple
            self.Log(f"User {self.__CurrentUser} retrieved details of student {ID}")
            return self.__LibCurs.fetchone()
        # Error handling and logging
        except Exception as e:
            self.Log(f"User {self.__CurrentUser} attempted to retrieve details of student {ID} and encountered an error: {e}")
            return f"System error: {e}"
    
    def GetCurrentUser(self):
        return self.__CurrentUser
  
    def GetCurrentAccessLevel(self):
        return self.__CurrentAccessLevel

    def GetCurrentUserName(self):
        # Retrieves the current user's name without logging
        try:
            self.__SysCurs.execute(
                "SELECT Forename, Surname FROM Staff WHERE UStaID = ?",
                (self.__CurrentUser,)
            )
            Result = self.__SysCurs.fetchone()
            if Result:
                return f"{Result[0]} {Result[1]}"
            return "Unknown"
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error retrieving current user name: {e}")
            return "Unknown"

    def GetLoanPeriod(self):
        try:
            # Finds and returns the default loan period
            self.__SysCurs.execute(
                "SELECT SettingValue FROM Settings WHERE SettingName = 'DefaultLoanPeriod'",
            )
            return int(self.__SysCurs.fetchone()[0])
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error retrieving loan period: {e}")
            # Otherwise, returns a reasonable loan period
            return 14

    def GetRetentionMonths(self):
        try:
            # Finds and returns the default data retention period in months
            self.__SysCurs.execute(
                "SELECT SettingValue FROM Settings WHERE SettingName = 'DefaultRetentionMonths'",
            )
            return int(self.__SysCurs.fetchone()[0])
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error retrieving retention months: {e}")
            # Otherwise, returns a reasonable retention period
            return 6

    def GetSMTPSettings(self):
        try:
            # Retrieves all SMTP settings as a dictionary
            self.__SysCurs.execute(
                "SELECT SettingName, SettingValue FROM Settings WHERE SettingName IN ('SMTPHost', 'SMTPPort', 'SMTPUser', 'SMTPPassword', 'SMTPSender')"
            )
            return {row[0]: row[1] for row in self.__SysCurs.fetchall()}
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error retrieving SMTP settings: {e}")
            return {}

    def SendEmail(self, ToAddress, Subject, Body):
        try:
            # Retrieves SMTP settings
            SMTPSettings = self.GetSMTPSettings()
            # Checks that all required settings are present and filled in
            Required = ["SMTPHost", "SMTPPort", "SMTPUser", "SMTPPassword", "SMTPSender"]
            if not all(SMTPSettings.get(k) for k in Required):
                self.Log("Email send failed: SMTP settings incomplete")
                return "Error: SMTP settings incomplete"
            # Builds the email
            Message = MIMEText(Body)
            Message["Subject"] = Subject
            Message["From"] = SMTPSettings["SMTPSender"]
            Message["To"] = ToAddress
            # Connects to SMTP server and sends
            with smtplib.SMTP(SMTPSettings["SMTPHost"], int(SMTPSettings["SMTPPort"])) as Server:
                Server.starttls()
                Server.login(SMTPSettings["SMTPUser"], SMTPSettings["SMTPPassword"])
                Server.sendmail(SMTPSettings["SMTPSender"], ToAddress, Message.as_string())
            self.Log(f"Email sent to {ToAddress}: {Subject}")
            return True
        # Error handling and logging
        except Exception as e:
            self.Log(f"Email send failed to {ToAddress}: {e}")
            return f"System error: {e}"

# --- Checking methods ---
    def CheckPermission(self, NecessaryPerms):
        # Maps each access level to a numeric value so higher levels inherit lower level permissions
        RoleHierarchy = {"None" : 0, "Teacher" : 1, "Admin" : 2, "SysAdmin" : 3}
        # Defaults to 0 if level not found, reducing bypass risk; unknown required perms default to 100 so they always fail
        CurrentValue = RoleHierarchy.get(self.__CurrentAccessLevel, 0)
        NecessaryValue = RoleHierarchy.get(NecessaryPerms, 100)
        # No user logged in check
        if self.__CurrentUser is None:
            return "No User logged in"
        # Active account check
        if self.IsAccountActive(self.__SysCurs, "Staff", "UStaID", self.__CurrentUser) != True:
            return False
        # Compares numeric values to determine if current user has sufficient permissions
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
        # Counts up until the expected ID is either the end of the list, or finds a gap in the list
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
        Result = Cursor.fetchone()
        if Result is None:
            return False
        return Result[0] == 1
       
    def CheckStaffMemberActive(self, ID):
        # Public method for making checks within the SystemConfig file, as LibraryManager will not have access to this
        return self.IsAccountActive(self.__SysCurs, "Staff", "UStaID", ID)

# --- Search Methods ---
    def SearchStaff(self, SearchTerm):
        try:
            # Permission check
            if self.CheckPermission("Teacher") != True:
                self.Log(f"{self.__CurrentUser} attempted to search staff: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            # Searches by forename, surname, or ID
            Query = """
                SELECT UStaID, Forename, Surname
                FROM Staff
                WHERE Forename LIKE ? OR Surname LIKE ? OR CAST(UStaID AS TEXT) LIKE ?
            """
            self.__SysCurs.execute(Query, (Term, Term, Term))
            Results = self.__SysCurs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find a staff member matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"
        
    def CreateNotification(self, UStaID, NotifBody):
        try:
            # Inserts a new undelivered notification for the given staff member
            UNID = self.GetNextID(self.__SysCurs, "Notifications", "UNID")
            self.__SysCurs.execute(
                "INSERT INTO Notifications (UNID, UStaID, NotifBody, Delivered) VALUES (?, ?, ?, ?)",
                (UNID, UStaID, NotifBody, False)
            )
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"Notification {UNID} created for staff member {UStaID}")
            return True
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error creating notification for staff member {UStaID}: {e}")
            return f"System error: {e}"

    def DeliverNotifications(self):
        try:
            # Fetches all undelivered notifications for the currently logged in user
            self.__SysCurs.execute(
                "SELECT UNID, NotifBody FROM Notifications WHERE UStaID = ? AND Delivered = ?",
                (self.__CurrentUser, False)
            )
            Pending = self.__SysCurs.fetchall()
            if not Pending:
                return "No pending notifications."
            # Retrieves the current user's email address
            self.__SysCurs.execute(
                "SELECT Email FROM Staff WHERE UStaID = ?",
                (self.__CurrentUser,)
            )
            EmailRow = self.__SysCurs.fetchone()
            if not EmailRow or not EmailRow[0]:
                self.Log(f"Notification delivery skipped for user {self.__CurrentUser}: no email address on record")
                return "No email address on record, notifications not delivered."
            ToAddress = EmailRow[0]
            # Sends each notification and marks it as delivered
            Delivered = 0
            for UNID, NotifBody in Pending:
                Result = self.SendEmail(ToAddress, "Library System Notification", NotifBody)
                if Result == True:
                    self.__SysCurs.execute(
                        "UPDATE Notifications SET Delivered = ? WHERE UNID = ?",
                        (True, UNID)
                    )
                    Delivered += 1
                else:
                    self.Log(f"Failed to deliver notification {UNID} to {ToAddress}")
            # Commits, Logs, Returns confirmation
            self.__SysConn.commit()
            self.Log(f"Delivered {Delivered} of {len(Pending)} notifications to user {self.__CurrentUser}")
            return f"Delivered {Delivered} of {len(Pending)} notifications."
        # Error handling and logging
        except Exception as e:
            self.Log(f"Error delivering notifications for user {self.__CurrentUser}: {e}")
            return f"System error: {e}"

    def SearchStudents(self, SearchTerm):
        try:
            # Permission check
            if self.CheckPermission("Teacher") != True:
                self.Log(f"{self.__CurrentUser} attempted to search students: Insufficient permissions")
                return "Access Denied: Insufficient Permissions."
            # Wraps search term in wildcards for partial matching
            Term = f"%{SearchTerm}%"
            # Searches by forename, surname, or ID
            Query = """
                SELECT UStuID, Forename, Surname
                FROM Students
                WHERE Forename LIKE ? OR Surname LIKE ? OR CAST(UStuID AS TEXT) LIKE ?
            """
            self.__LibCurs.execute(Query, (Term, Term, Term))
            Results = self.__LibCurs.fetchall()
            # Returns results or a not found message
            return Results if Results else f"Could not find a student matching '{SearchTerm}'."
        # Error handling and logging
        except Exception as e:
            return f"Search Error: {e}"