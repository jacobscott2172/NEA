import sqlite3

class LibraryManager:

    def __init__ (self):
        # Establishes class variables for relevant connections and cursors
        self.__Conn = sqlite3.connect("Databases/LibraryData.db")
        self.__Curs = self.__Conn.cursor()

    @staticmethod
    def GetNextID(Cursor, Table, ID):
        # Returns the next available ID from a table, useful over autoincrement as it accounts for record deletion
        Cursor.execute(f"SELECT {ID} FROM {Table} ORDER BY {ID} ASC")
        rows = Cursor.fetchall()
        existing_ids = [row[0] for row in rows]
        expected_id = 1
        for id in existing_ids:
            if id != expected_id:
                break
            expected_id += 1
        return expected_id