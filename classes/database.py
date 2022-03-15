from datetime import time
import sqlite3, traceback, sys, json, os

from shutil import copyfile

import time as timeog

from sqlite3 import Error
from helper import sql_tables
from globals import *


class database:
    def __init__(self, database_name=config["database"]["path"], backup=config["database"]["backup"]):
        self.__conn = None
        self.__path = database_name
        self.__backup = backup

        try:

            self.__conn = sqlite3.connect(database_name, check_same_thread=False)
            self.__closed = False

            print("SQLITE Connection Established! v{v}".format(v=sqlite3.version_info))

            for x in sql_tables.sql_commands:
                self.Execute(x)

            self.Commit()

        except Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def IsClosed(self):
        return self.__closed

    def Connection(self):
        return self.__conn.cursor()

    def CloseConnection(self):
        if self.__conn:
            self.__conn.close()
            self.__closed = True

    def Commit(self):

        while self.IsClosed():
            time.sleep(5)
            return

        try:
            self.__conn.commit()
        except:
            pass

    def Exist(self, table, column, key):
        try:

            while self.IsClosed():
                time.sleep(5)
                return

            c = self.__conn.cursor()
            c.execute(f"SELECT * FROM {table} WHERE {column} = ?", (key,))
            rows = c.fetchall()

            if not rows:
                return False
            else:
                return True
        except Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    def Delete(self, table, column, key):
        try:
            
            while self.IsClosed():
                time.sleep(5)
                return
            
            c = self.__conn.cursor()
            c.execute(f"DELETE FROM {table} WHERE {column} = ?", (key,))
            self.Commit()

        except Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def RetrieveAll(self, table):
        try:

            while self.IsClosed():
                time.sleep(5)
                return

            sql_statement = """SELECT * FROM {table}""".format(table=table)

            c = self.__conn.cursor()
            c.execute(sql_statement)
            return c.fetchall()
            
        except Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def Retrieve(self, table, column=None, key=None):

        while self.IsClosed():
            time.sleep(5)
            return

        c = self.__conn.cursor()

        if not column is None and not key is None:
            c.execute(f"""SELECT * FROM {table} WHERE {column} = '{key}';""")
        else:
            c.execute(f"""SELECT * FROM {table};""")

        return list(c.fetchall())

    def Execute(self, command, changes=None):

        while self.IsClosed():
            time.sleep(5)
            return

        c = self.__conn.cursor()

        try:
            if changes is None:
                c.execute(command)
            else:
                c.execute(command, changes)
        except:
            pass

        self.Commit()
        return c.fetchall()

    def GetAllTables(self):

        while self.IsClosed():
            time.sleep(5)
            return

        c = self.__conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")

        return_tables = []
        tables = c.fetchall()
        for x in tables:
            return_tables.append(x[0])

        return return_tables

    def GetTableColumn(self, table):

        while self.IsClosed():
            time.sleep(5)
            return
        

        c = self.__conn.cursor()
        c.execute(f"PRAGMA table_info({table});")

        return_tables = []
        tables = c.fetchall()
        for x in tables:
            return_tables.append(x[1])

        return return_tables

    def GetLastFew(self, table, limit=30, id=None, order="timestamp", extra=""):

        while self.IsClosed():
            time.sleep(5)
            return
        

        c = self.Connection()

        if id is None:
            c.execute(f"SELECT * FROM {table} ORDER BY {order} DESC;")
        else:
            c.execute(f"SELECT * FROM {table} WHERE id = '{id}' ORDER BY {order} DESC;")

        return_last = []
        rows = list(c.fetchall())

        max_items = 0
        for x in range(len(rows)):
        
            return_last.append(rows[x][0])

            max_items += 1
            if len(return_last) > limit:
                break
                
        return return_last
    
    def Backup(self):

        curr_path = str(self.__path) 
        file_name = os.path.basename(curr_path) 

        back_path = self.__backup + file_name + "_" + str(int(timeog.time()))

        copyfile(curr_path, back_path)
    
    def RestoreBackup(self, backupid):
        
        self.Commit()
        self.CloseConnection()

        try:
            os.remove(self.__path)
            os.remove(self.__path + "-journal")
        except:
            pass

        copyfile(self.__backup + backupid, self.__path)

        self.__init__()

    def DeleteBackup(self, backupid):
        os.remove(self.__backup + backupid)
    
    def SelfDestruct(self):
        self.CloseConnection()

        try:
            os.remove(self.__path)
            os.remove(self.__path + "-journal")
        except:
            pass
            
        self.__init__()
