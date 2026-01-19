import sqlite3

class LibraryManager:

    def __init__ (self):
        # Establishes class variables for relevant connections and cursors
        self.__Conn = sqlite3.connect("Databases/LibraryData.db")
        self.__Curs = self.__Conn.cursor()

    