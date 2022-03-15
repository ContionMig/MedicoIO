from __init__ import db, config
from helper import helper, encryption

import time, json, random

from classes.site_settings import site
from classes.logging import logger

import os, globals
from os.path import isfile, join


class IPBlacklistData:

    table = 'ip_blacklist'

    def __init__(self, ip_address=None, create=False):

    
        self.__ip_address = ip_address

        exist = db.Exist(self.table, "ip_address", self.__ip_address)

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(ip_address, timestamp) VALUES(?, ?);", (self.__ip_address, int(time.time())))
            
            self.set_violations(0)
            self.set_time_out(0)
            
            db.Commit()

        self.__exist = exist
        self.__valid = True
    
    def __str__(self):
        output =  "\n----------- IPBlacklistData -----------\n"
        output += ""

        return output

    def id(self):
        return self.__ip_address

    def exist(self):
        return self.__exist 

    def is_valid(self):
        return self.__valid and self.__exist
    
    def self_delete(self):
        tables = db.GetAllTables()
        for x in tables:
            try:
                db.Execute(f"""DELETE FROM {x} WHERE ip_address='{self.id()}';""")
            except:
                pass
        
        db.Commit()


    def set_item(self, val, item):

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE ip_address = ?;", (val, self.__ip_address))
        db.Commit()
    

    def get_item(self, item):
        
        val = db.Execute(f"SELECT {item} FROM {self.table} WHERE ip_address='{self.__ip_address}';")[0][0]
        if val is None:
            return "-"

        return val

    def get_violations(self):
        return int(self.get_item("violations"))

    
    def set_violations(self, violations):
        self.set_item(int(violations), "violations")
    

    def get_time_out(self):
        return int(self.get_item("time_out"))

    def set_time_out(self, time_out):
        self.set_item(int(time_out), "time_out")
    


class IPBlacklistManagerData():
    def __init__(self):
        pass

    def add_violation(self, ip_address):
        
        blacklist = IPBlacklistData(ip_address, create=True)
        
        curr_violation = blacklist.get_violations()
        if curr_violation >= 3:
            
            logger.create_log(logger.LOG_WARNING, "Authentication", f"[{ip_address}] IP Address has been banned for 1 hour due to too many violations")

            blacklist.set_time_out(time.time() + config['violation_timeout'])
            blacklist.set_violations(0)
        
        blacklist.set_violations(curr_violation + 1)
    
    def is_blocked(self, ip_address):
        
        blacklist = IPBlacklistData(ip_address, create=True)
        
        time_out = blacklist.get_time_out()
        
        if time_out == 0:
            return False
        
        if time.time() >= time_out:
            blacklist.set_time_out(0)
            return False
        
        return True
            
    



ip_manager = IPBlacklistManagerData()