from __init__ import db
from helper import helper, encryption

import time, json, random

from classes.user_details import UserDetailData
from classes.site_settings import site
from classes.consultations import ConsultationSystemData
from classes.images import imagesSystemData
from classes.blogs import BlogSystemData

import os, globals
from os.path import isfile, join


class UserData:

    table = 'user_info'

    USR_PATIENTS = "2"
    USR_DOCTOR = "1"
    USR_ADMINS = "0"
    USR_NONUSR = "-1"

      
    def __init__(self, NRIC=None, userid=None, create=False):

        if NRIC is None and userid is None or NRIC is not None and not helper.verify_nric(NRIC):
            self.__valid = False
            self.__exist = False
            return

        if userid is None:
            
            nric = helper.remove_symbol(NRIC).strip().upper()
            seed = helper.random_character(site.get_id_length(), seed=nric)

            random.Random(nric).shuffle(list(seed))
            userid = ''.join(seed)

            if site.get_userid_masking() == "hashing":
                userid = encryption.hashing.hash(str(seed + seed[::-1] + seed), site.get_userbase_hash())


        userid = helper.remove_symbol(userid)

        self.__userid = userid

        exist = db.Exist(self.table, "id", self.__userid)
        self.setup_encryption()

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(id) VALUES(?);", (self.__userid, ))

            self.set_user_level(2)
            
            pfp_path = globals.config["website"]["profile_pictures"]
            pfps = [f for f in os.listdir(pfp_path) if isfile(join(pfp_path, f))]

            self.set_pfp(path=f"{pfp_path}/{random.choice(pfps)}")
            self.set_otp("0")

            db.Commit()

        self.__exist = exist
        self.__valid = True

        self.details = UserDetailData(self.__userid, create=create)
        self.consultation = ConsultationSystemData(self.__userid)
        self.images = imagesSystemData(self.__userid)
        self.blogs = BlogSystemData(self.__userid)
    
    def __str__(self):
        output =  "\n----------- UserData -----------\n"
        output += ""

        return output

    def id(self):
        return self.__userid

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

        seed = helper.random_character(128, seed=f"{self.__userid}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(sec_seed + seed[::-1] + seed), site.get_userbase_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(sec_seed[::-1] + seed + seed[::-1]), site.get_userbase_hash()).encode("utf-8")
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
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_user_encryption())

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE id = ?;", (val, self.__userid))
        db.Commit()
    

    def get_item(self, item, to_byte=True):
        
        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False
        
        try:
            
            val = db.Execute(f"SELECT {item} FROM {self.table} WHERE id='{self.__userid}';")[0][0]
            if val is None:
                return "-"

            if encrypt:
                val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_user_encryption())
            
            return val

        except:
            return "-"

    def get_user_level(self):
        return str(self.get_item("user_level"))

    
    def set_user_level(self, user_level):
        self.set_item(str(user_level), "user_level")
    

    def get_otp(self):
        return str(self.get_item("otp"))

    def set_otp(self, otp):
        self.set_item(str(otp), "otp")
    

    def get_ip_address(self):
        return self.get_item("ip_address")
    

    def set_ip_address(self, ip_address):
        self.set_item(ip_address, "ip_address")
    

    def get_login_date(self):
        return self.get_item("login_date")
    

    def set_login_date(self):

        login_date = str(int(time.time()))
        self.set_item(login_date, "login_date")

        self.details.set_login_date()
    

    def get_pass_salt(self):
        return self.get_item("pass_salt")
        

    def set_pass_salt(self, pass_salt):
        self.set_item(pass_salt, "pass_salt")
        
    def get_password(self):
        return self.get_item("pass")
    

    def set_doctor(self, doctor):
        self.set_item(doctor, "doctor")
    

    def get_doctor(self):
        return self.get_item("doctor")


    def set_pfp(self, pfp=None, path=None):

        if path:

            in_file = open(path, "rb")
            data = in_file.read()
            in_file.close()

            pfp = data

        self.set_item(pfp, "pfp", False)
    

    def get_pfp(self):
        return self.get_item("pfp", False)

    def get_abbreviation(self):
        
        if self.get_user_level() == 1:
            return "Dr."

        gender = self.details.get_gender()
        if gender == "Male":
            return "Mr."
        elif gender == "Female":
            return "Miss."
        else:
            return ""


    def set_password(self, password):
        password = str(password)

        ran_salt = helper.random_character(site.get_salt_length())
        self.set_pass_salt(ran_salt)

        password = str(password + ran_salt)
        password = encryption.hashing.hash(password, site.get_pass_hash())

        password = encryption.encrypting.encrypt(password, self.key, self.iv, type=site.get_user_encryption())
        db.Execute(f"UPDATE {self.table} SET pass = ? WHERE id = ?;", (password, self.__userid))
        

    def verify_password(self, password):
        password = str(password)

        ran_salt = self.get_pass_salt()

        password = str(password + ran_salt)
        password =  encryption.hashing.hash(password, site.get_pass_hash())

        hash = self.get_password()

        print(f"Password Hash: {hash}")
        
        if str(hash) == str(password):
            return True
        
        return False
    

class UserManagerData():
    def __init__(self):
        pass

    def purge_users(self, duration=None, user_level=99):

        if not duration is None:
            duration = int(duration)
            now = int(time.time())

            db.Execute(f"DELETE FROM {UserData.table} WHERE login_date < ? AND user_level = ?", (int(now - duration), int(user_level)))
        else:
            db.Execute(f"DELETE FROM {UserData.table} WHERE user_level = ?", (int(user_level),))

        db.Commit()


user_manager = UserManagerData()