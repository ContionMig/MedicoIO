from __init__ import db
from helper import helper, encryption

import time, json

from classes.user_details import UserDetailData
from classes.site_settings import site

class LoggingData:

    table = 'log_detail'

    def __init__(self, err_level=None, title=None, description=None, timestamp=None, logid=None, create=False):

        if logid is None:
            logid = helper.random_character(site.get_id_length())
            
        logid = helper.remove_symbol(logid)

        self.__logid = logid

        exist = db.Exist(self.table, "id", self.__logid)
        self.setup_encryption()

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(id, timestamp) VALUES(?, ?);", (self.__logid, str(int(time.time()))))
            db.Commit()

        self.set_err_level(err_level)
        self.set_title(title)
        self.set_description(description)
        self.set_timestamp(timestamp)

        self.__exist = exist
    
    def __str__(self):

        output =  "\n----------- LoggingData -----------\n"
        output += f"ID: {self.id()} | Error Level: {self.get_err_level()}\n"
        output += f"Title: {self.get_title()}\n"
        output += f"Description: {self.get_description()}\n"
        output += f"Timestamp: {self.get_timestamp()}\n"

        return output

    def id(self):
        return self.__logid

    def exist(self):
        return self.__exist 

    def is_valid(self):
        return self.__valid and self.__exist


    def self_delete(self):
        tables = db.GetAllTables()
        for x in tables:
            try:
                db.Execute(f"""DELETE FROM {x} WHERE id='{self.id()}';""")
            except:
                pass
        
        db.Commit()

    def setup_encryption(self):

        seed = helper.random_character(128, seed=f"{self.__logid}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(sec_seed + seed[::-1] + sec_seed), site.get_database_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(seed[::-1] + sec_seed + sec_seed[::-1]), site.get_database_hash()).encode("utf-8")
        else:
            key = str(seed).encode("utf-8")
            iv = str(sec_seed).encode("utf-8")

        self.key = key
        self.iv = iv

    def set_item(self, val, item, to_byte=True):
        
        if val is None:
            return

        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False


        if encrypt:
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_log_encryption())

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE id = ?;", (val, self.__logid))
    
    def get_item(self, item, to_byte=True):
        
        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False
        
        val = db.Execute(f"SELECT {item} FROM {self.table} WHERE id='{self.__logid}';")[0][0]
        if val is None:
            return "-"

        if encrypt:
            val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_log_encryption())
        
        return val

    def get_err_level(self):

        err_level = self.get_item("err_level")
        if err_level == "-":
            err_level = 0

        return int(err_level)

    def get_title(self):
        return self.get_item("title")

    def get_description(self):
        return self.get_item("description")

    def get_logid(self):
        return self.get_item("logid")
    
    def set_err_level(self, err_level):
        self.set_item(err_level, "err_level")

    def set_title(self, title):
        self.set_item(title, "title")

    def set_description(self, description):
        self.set_item(description, "description")

    def set_logid(self, logid):
        self.set_item(logid, "logid")
    
    def set_timestamp(self, timestamp):
        self.set_item(timestamp, "timestamp")
    
    def get_timestamp(self):
        return self.get_item("timestamp")
    

class LoggingSystemData():

    LOG_EMERG = 0
    LOG_ALERT = 1
    LOG_CRIT = 2
    LOG_ERR = 3
    LOG_WARNING = 4
    LOG_NOTICE = 5
    LOG_INFO = 6
    LOG_DEBUG = 7

    def __init__(self):
        pass

    def __str__(self):
        output =  "----------- LoggingSystemData -----------"
        output += ""

        return output
    
    def create_log(self, errno, title, description):
        
        log = LoggingData(errno, title, description, create=True)
        return log

    def create_view(self, request):
        
        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
            ip_address = ip_address.split(",")
            ip_address = ip_address[0]
        else:
            ip_address = str(request.remote_addr)
        
        log = LoggingData(self.LOG_INFO, "Page Visit", f"[{ip_address}] - {request.url} | {request.user_agent}", create=True)
        return log
    


    def retrieve_logs(self, filter=None):


        if not filter:
            r_logs = db.Execute(f"SELECT id FROM {LoggingData.table};")
        else:
            r_logs = db.Execute(f"SELECT id FROM {LoggingData.table} WHERE err_level = ?;", (filter,))

        all_logs = []
        
        for x in range(len(r_logs)):
            curr_con = LoggingData(logid=r_logs[x][0])
            all_logs.append(curr_con)

        return all_logs

    def purge_logs(self, duration=None):

        if not duration is None:
            duration = int(duration)
            now = int(time.time())

            db.Execute(f"DELETE FROM log_detail WHERE timestamp < ?", (int(now - duration),))
        else:
            db.Execute(f"DELETE FROM log_detail")

        db.Commit()


logger = LoggingSystemData()

