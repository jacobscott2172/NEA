import sqlite3

conn1 = sqlite3.connect("Databases\LibraryData.db")
curs1 = conn1.cursor()

curs1.execute('PRAGMA foreign_keys = ON')

curs1.execute('''
CREATE TABLE IF NOT EXISTS Students(
              UStuID INTEGER PRIMARY KEY NOT NULL,
              Forename TEXT NOT NULL, 
              Surname TEXT NOT NULL,
              MaxActiveLoans INTEGER NOT NULL, 
              AccountActive BOOLEAN NOT NULL DEFAULT TRUE,
              InactiveDate TEXT,
              EntryYear INTEGER NOT NULL
              )''')

curs1.execute('''
CREATE TABLE IF NOT EXISTS Authors(
              UAID INTEGER PRIMARY KEY NOT NULL, 
              Forename TEXT NOT NULL, 
              Middlenames TEXT, 
              Surname TEXT NOT NULL
              )''')

curs1.execute('''
CREATE TABLE IF NOT EXISTS Books(
              ISBN INTEGER PRIMARY KEY NOT NULL, 
              Title TEXT NOT NULL,
              Genre TEXT,
              Subject TEXT,
              LearnerLevel TEXT,
              YearGroup TEXT
              )''')

curs1.execute('''
CREATE TABLE IF NOT EXISTS BooksAuthors(
              ISBN INTEGER NOT NULL,  
              UAID INTEGER NOT NULL,
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN), 
              FOREIGN KEY (UAID) REFERENCES Authors(UAID), 
              PRIMARY KEY(ISBN, UAID)
              )''')

curs1.execute('''
CREATE TABLE IF NOT EXISTS Locations(
              ULocID INTEGER PRIMARY KEY NOT NULL, 
              ClassCode TEXT NOT NULL UNIQUE
              )''')

curs1.execute('''
CREATE TABLE IF NOT EXISTS Copies(
              UCID INTEGER PRIMARY KEY NOT NULL, 
              ISBN INTEGER NOT NULL,
              HomeLocationID INTEGER NOT NULL,
              CurrentLocationID INTEGER NOT NULL,
              Status TEXT NOT NULL,
              Condition TEXT NOT NULL,
              FOREIGN KEY (ISBN) REFERENCES Books(ISBN),
              FOREIGN KEY (HomeLocationID) REFERENCES Locations(ULocID),
              FOREIGN KEY (CurrentLocationID) REFERENCES Locations(ULocID)
              )''')
conn1.commit()