# Database definition
# Dates will be stored to the ISO 8601 standard YYYYMMDD
# Both because it is the international standard and when sorted in ascending or descending order, the dates are chronological

# imports SQLite
import sqlite3

# Creates connections to database files and cursors for creating/editing tables
conn1 = sqlite3.connect("Databases\LibraryData.db")
curs1 = conn1.cursor()
conn2 = sqlite3.connect("Databases\SystemConfig.db")
curs2 = conn2.cursor()

# Enables foreign keys, so tables can refer to each other
curs1.execute('PRAGMA foreign_keys = ON')
curs2.execute('PRAGMA foreign_keys = ON')

# Creates the "Students" table, including a unique ID
# This stores account details for all of the students in the school
# The inactive date will be stored as the ISO 8601 standard YYYYMMDD
curs1.execute('''
CREATE TABLE IF NOT EXISTS Students(
              UStuID INTEGER PRIMARY KEY NOT NULL,
              Forename TEXT NOT NULL, 
              Surname TEXT NOT NULL,
              MaxActiveLoans INTEGER NOT NULL, 
              AccountActive BOOLEAN NOT NULL DEFAULT TRUE,
              InactiveDate INTEGER,
              EntryYear INTEGER NOT NULL,
              Email TEXT
              )''')

# Creates the "Authors" table, including a unique ID
# This stores the names of all the authors, which will later be linked to a book
curs1.execute('''
CREATE TABLE IF NOT EXISTS Authors(
              UAID INTEGER PRIMARY KEY NOT NULL, 
              Forename TEXT NOT NULL, 
              Middlenames TEXT, 
              Surname TEXT NOT NULL
              )''')

# Creates the "Books" table, including a International standard book number (ISBN)
# This stores the details of books, such as their title
curs1.execute('''
CREATE TABLE IF NOT EXISTS Books(
              ISBN INTEGER PRIMARY KEY NOT NULL, 
              Title TEXT NOT NULL,
              Genre TEXT,
              Subject TEXT
              )''')

# Creates the table which links books and authors
# No unique ID is needed as each combination of book and author is unique
curs1.execute('''
CREATE TABLE IF NOT EXISTS BooksAuthors(
              ISBN INTEGER NOT NULL,  
              UAID INTEGER NOT NULL,
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN), 
              FOREIGN KEY (UAID) REFERENCES Authors(UAID), 
              PRIMARY KEY(ISBN, UAID)
              )''')

# Creates the "Locations" table, including a unique ID
# This gives all of the locations in the school an identifier
# So that each copy of a book can have a known location
curs1.execute('''
CREATE TABLE IF NOT EXISTS Locations(
              ULocID INTEGER PRIMARY KEY NOT NULL, 
              ClassCode TEXT NOT NULL UNIQUE
              )''')

# Creates the "Copies" table, including a unique ID
# This identifies and stores each copy of each book, including copy specific values
# The book's current location can be a NULL value, because it will be set as such when the book is loaned out 
curs1.execute('''
CREATE TABLE IF NOT EXISTS Copies(
              UCID INTEGER PRIMARY KEY NOT NULL, 
              ISBN INTEGER NOT NULL,
              HomeLocationID INTEGER NOT NULL,
              CurrentLocationID INTEGER,
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN),
              FOREIGN KEY (HomeLocationID) REFERENCES Locations(ULocID),
              FOREIGN KEY (CurrentLocationID) REFERENCES Locations(ULocID)
              )''')

# Creates the "Staff" table, including a unique ID
# Staff passwords will be stored hashed and salted for security
# Access levels will be organised into 3 categories, "Teacher" "Admin" and "SysAdmin"
curs2.execute('''
CREATE TABLE IF NOT EXISTS Staff(
              UStaID INTEGER PRIMARY KEY NOT NULL,
              PasswordHash TEXT NOT NULL,
              Salt TEXT NOT NULL,
              Forename TEXT NOT NULL,
              Surname TEXT NOT NULL,
              AccessLevel TEXT NOT NULL,
              AccountActive BOOLEAN NOT NULL DEFAULT TRUE,
              InactiveDate INTEGER,
              Email TEXT
              )''')

conn2.commit()

# Creates the "Loans" table, including a unique ID
# This links all the relevant data of one loan into a single entry, such as:
# The copy loaned, The student loaned to, The teacher who authorised the loan
# Logic will be used to ensure that if the number of copies of a book reserved for a certain day is equal to the number available, no more can be loaned
curs1.execute('''
CREATE TABLE IF NOT EXISTS Loans(
              ULoanID INTEGER PRIMARY KEY NOT NULL,
              UStuID INTEGER NOT NULL,
              UStaID INTEGER NOT NULL,
              UCID INTEGER NOT NULL,
              LoanDate INTEGER NOT NULL,
              DueDate INTEGER NOT NULL,
              ReturnDate INTEGER,
              FOREIGN KEY (UCID) REFERENCES Copies(UCID),
              FOREIGN KEY (UStuID) REFERENCES Students(UStuID),
              FOREIGN KEY (UStaID) REFERENCES Staff(UStaID)
              )''')
conn1.commit()

# Creates the "Reservations" table, including a unique ID
# This links all the relevant data of one reservation into a single entry, such as:
# The date of creation, the teacher reserved to, location reserved to, and the number reserved
# The placement, start, and end dates will be stored as the ISO 8601 standard YYYYMMDD
# Placement dates will be used to fulfil reservations based upon a "First reserved, first served" basis
# Logic will be used to find the locations of the reserved books books on the day, preferrign books that are in one room for ease of collection
curs1.execute('''
CREATE TABLE IF NOT EXISTS Reservations(
              URID INTEGER PRIMARY KEY NOT NULL,
              ULocID INTEGER NOT NULL,
              CreationDate INTEGER NOT NULL,
              ReservationDate INTEGER NOT NULL,
              ISBN INTEGER NOT NULL,
              UStaID INTEGER NOT NULL,
              Quantity INTEGER NOT NULL,
              FOREIGN KEY (ULocID) REFERENCES Locations(ULocID),
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN),
              FOREIGN KEY (UStaID) REFERENCES Staff(UStaID)
              )''')
conn1.commit()

# This stores global config settings, such as the maximum number of loans a default student account can have
# it auto-inserts default values as they are not specific to the school like room codes or staff names
# however these values can be changed later
curs2.execute('''
              CREATE TABLE IF NOT EXISTS Settings (
              SettingName TEXT PRIMARY KEY,
              SettingValue TEXT
              )''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('DefaultMaxLoans', '3')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('DefaultLoanPeriod', '14')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('DefaultRetentionMonths', '6')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('SMTPHost', '')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('SMTPPort', '')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('SMTPUser', '')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('SMTPPassword', '')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('SMTPSender', '')
              ''')

curs2.execute('''
              INSERT OR IGNORE INTO Settings (SettingName, SettingValue)
              VALUES ('OnLoanLocation', '1')
              ''')

conn2.commit()

# ===== SAMPLE DATA =====

# --- Locations ---
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (1, 'ON LOAN')")
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (2, 'LIB01')")
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (3, 'ENG01')")
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (4, 'SCI01')")
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (5, 'HIS01')")
curs1.execute("INSERT OR IGNORE INTO Locations (ULocID, ClassCode) VALUES (6, 'MAT01')")

# --- Authors ---
# Authors 1-4: single-book authors
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (1, 'William', NULL, 'Shakespeare')")
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (2, 'George', NULL, 'Orwell')")
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (3, 'Mary', NULL, 'Shelley')")
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (4, 'John', 'Ronald Reuel', 'Tolkien')")
# Authors 5-6: multi-book authors who also co-author Good Omens together
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (5, 'Terry', NULL, 'Pratchett')")
curs1.execute("INSERT OR IGNORE INTO Authors (UAID, Forename, Middlenames, Surname) VALUES (6, 'Neil', NULL, 'Gaiman')")

# --- Books ---
# Original books (single author each)
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780141396132, 'Macbeth', 'Fiction', 'English Literature')")
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780451524935, 'Nineteen Eighty-Four', 'Fiction', 'English Literature')")
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780486282114, 'Frankenstein', 'Fiction', 'English Literature')")
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780261102217, 'The Lord of the Rings', 'Fiction', 'English Literature')")
# Multi-author book: Good Omens by Pratchett AND Gaiman
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780060853983, 'Good Omens', 'Fiction', 'English Literature')")
# Additional Pratchett book (demonstrates author with multiple books)
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780552166591, 'The Colour of Magic', 'Fiction', 'English Literature')")
# Additional Gaiman book (demonstrates author with multiple books)
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780063081918, 'American Gods', 'Fiction', 'English Literature')")
# Additional Gaiman book
curs1.execute("INSERT OR IGNORE INTO Books (ISBN, Title, Genre, Subject) VALUES (9780380807345, 'Coraline', 'Fiction', 'English Literature')")

# --- BooksAuthors links ---
# Single-author links
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780141396132, 1)")  # Macbeth - Shakespeare
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780451524935, 2)")  # 1984 - Orwell
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780486282114, 3)")  # Frankenstein - Shelley
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780261102217, 4)")  # LOTR - Tolkien
# Multi-author link: Good Omens has TWO authors
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780060853983, 5)")  # Good Omens - Pratchett
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780060853983, 6)")  # Good Omens - Gaiman
# Pratchett's other book
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780552166591, 5)")  # Colour of Magic - Pratchett
# Gaiman's other books
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780063081918, 6)")  # American Gods - Gaiman
curs1.execute("INSERT OR IGNORE INTO BooksAuthors (ISBN, UAID) VALUES (9780380807345, 6)")  # Coraline - Gaiman

# --- Copies ---
# Macbeth: 3 copies in LIB01 and ENG01
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (1, 9780141396132, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (2, 9780141396132, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (3, 9780141396132, 3, 3)")
# 1984: 2 copies
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (4, 9780451524935, 3, 3)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (5, 9780451524935, 2, 2)")
# Frankenstein: 2 copies
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (6, 9780486282114, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (7, 9780486282114, 3, 3)")
# LOTR: 1 copy
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (8, 9780261102217, 4, 4)")
# Good Omens: 3 copies across different rooms
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (9, 9780060853983, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (10, 9780060853983, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (11, 9780060853983, 3, 3)")
# Colour of Magic: 2 copies
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (12, 9780552166591, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (13, 9780552166591, 5, 5)")
# American Gods: 1 copy
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (14, 9780063081918, 2, 2)")
# Coraline: 2 copies
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (15, 9780380807345, 2, 2)")
curs1.execute("INSERT OR IGNORE INTO Copies (UCID, ISBN, HomeLocationID, CurrentLocationID) VALUES (16, 9780380807345, 3, 3)")

conn1.commit()

# --- Students ---
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (1, 'Alice', 'Johnson', 3, TRUE, 2022, 'alice.johnson@school.example.com')")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (2, 'Ben', 'Carter', 3, TRUE, 2022, 'ben.carter@school.example.com')")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (3, 'Charlotte', 'Davies', 3, TRUE, 2023, 'charlotte.davies@school.example.com')")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (4, 'Daniel', 'Evans', 3, TRUE, 2023, 'daniel.evans@school.example.com')")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (5, 'Emily', 'Foster', 3, TRUE, 2024, 'emily.foster@school.example.com')")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (6, 'Finn', 'Green', 3, TRUE, 2024, NULL)")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (7, 'Grace', 'Hall', 3, FALSE, 2020, NULL)")
curs1.execute("INSERT OR IGNORE INTO Students (UStuID, Forename, Surname, MaxActiveLoans, AccountActive, EntryYear, Email) VALUES (8, 'Harry', 'Jones', 3, TRUE, 2021, 'harry.jones@school.example.com')")

conn1.commit()

# --- Staff test accounts ---
# Password is "password" for all three
curs2.execute("""
              INSERT OR IGNORE INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel, Email)
              VALUES (1, '166c88fd2ff550a17d1a587ebaeeb2bd3e7dd1e68f919dc3d2b076b7f2abe87f', 'ae0680da10104bb7bab3e508688c0ddd', 'Example', 'Teacher', 'Teacher', 'teacher@example.com')
              """)
 
curs2.execute("""
              INSERT OR IGNORE INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel, Email)
              VALUES (2, '1bd2d70c6aecb2045a982507cca1ac2c2e22110306ac4a6809fa8a484de5a76b', '80bcc3c87677494db59a08243efe04cf', 'Example', 'Admin', 'Admin', 'admin@example.com')
              """)
 
curs2.execute("""
              INSERT OR IGNORE INTO Staff (UStaID, PasswordHash, Salt, Forename, Surname, AccessLevel, Email)
              VALUES (3, 'ea0bd76c36f08ef064f6dbf29bb5c25b75cca79a23eab40baf4f6a070e94848e', '83d2bbecc0a140f38ec1e5ed72cec154', 'Example', 'SysAdmin', 'SysAdmin', 'sysadmin@example.com')
              """)
 
conn2.commit()