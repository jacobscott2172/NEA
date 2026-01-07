# Database definition
# Dates will be stored to the ISO 8601 standard YYYYMMDD
# Both because it is the international standard and when sorted in ascending or descending order, the dates are chronological

# imports SQLite
import sqlite3

# Creates connections to database files and cursors for creating/editing tables
conn1 = sqlite3.connect("Databases\LibraryData.db")
curs1 = conn1.cursor()
conn2 = sqlite3.connect("Databases\StaffLogins.db")
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
              EntryYear INTEGER NOT NULL
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
              Subject TEXT,
              LearnerLevel TEXT,
              YearGroup TEXT
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
# such as that copy's condition, storage and status
# The book's current location can be a NULL value, because it will be set as such when the book is loaned out 
curs1.execute('''
CREATE TABLE IF NOT EXISTS Copies(
              UCID INTEGER PRIMARY KEY NOT NULL, 
              ISBN INTEGER NOT NULL,
              HomeLocationID INTEGER NOT NULL,
              CurrentLocationID INTEGER,
              Status TEXT NOT NULL,
              Condition TEXT NOT NULL,
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
              InactiveDate INTEGER
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
              Loandate INTEGER NOT NULL,
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
              ReservationDate INTEGER NOT NULL,
              StartDate INTEGER NOT NULL,
              EndDate INTEGER NOT NULL,
              ISBN INTEGER NOT NULL,
              UStaID INTEGER NOT NULL,
              Quantity INTEGER NOT NULL,
              Status TEXT NOT NULL,
              FOREIGN KEY (ULocID) REFERENCES Locations(ULocID),
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN),
              FOREIGN KEY (UStaID) REFERENCES Staff(UStaID)
              )''')
conn1.commit()