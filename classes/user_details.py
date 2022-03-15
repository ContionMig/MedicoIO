from __init__ import db
from helper import helper, encryption

import time, json

from classes.site_settings import site


class UserDetailData:

    table = 'user_details'

    def __init__(self, userid, create=True):

        exist = db.Exist(self.table, "id", userid)
        if create and not exist:
            db.Execute(f"INSERT INTO {self.table}(id, admission_date) VALUES(?, ?);", (userid, int(time.time())))

            db.Commit()

        self.__userid = userid

        self.setup_encryption()
    
    
    def __str__(self):
        output =  "\n----------- UserData -----------\n"
        output += f"ID: {self.userid()} | Name: {self.f_name() + self.l_name()}\n"
        output += f"NRIC: {self.ic_num()}\n"
        output += f""

        return output

    def get_id(self):
        return self.__userid


    def setup_encryption(self):

        seed = helper.random_character(128, seed=f"{self.__userid}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(sec_seed + seed[::-1] + sec_seed), site.get_userbase_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(seed[::-1] + seed + sec_seed[::-1]), site.get_userbase_hash()).encode("utf-8")
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
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_user_detail_encryption())

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
                val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_user_detail_encryption())
            
            return val

        except:
            return "-"

    def get_nric(self):
        return self.get_item("ic_num")
    

    def set_nric(self, ic_num):
        self.set_item(ic_num, "ic_num")


    def get_fname(self):
        return self.get_item("f_name")
    

    def set_fname(self, f_name):
        self.set_item(f_name, "f_name")
    

    def get_lname(self):
        return self.get_item("l_name")
    

    def set_lname(self, l_name):
        self.set_item(l_name, "l_name")
    

    def get_addr(self):
        return self.get_item("addr")
    

    def set_addr(self, addr):
        self.set_item(addr, "addr")
    

    def get_contact(self):
        return self.get_item("contact_num")
    

    def set_contact(self, contact_num):
        self.set_item(contact_num, "contact_num")


    def get_email(self):
        return self.get_item("email")
    

    def set_email(self, email):
        self.set_item(email, "email")
    

    def get_gender(self):
        return self.get_item("gender")
    

    def set_gender(self, gender):
        self.set_item(gender, "gender")
    

    def get_blood(self):
        return self.get_item("blood_type")
    

    def set_blood(self, blood_type):
        self.set_item(blood_type, "blood_type")

    
    def get_dob(self):
        return self.get_item("dob")
    

    def set_dob(self, dob):
        self.set_item(dob, "dob")
    

    def get_height(self):
        return self.get_item("height")
    
    def set_height(self, height):
        self.set_item(height, "height")
    

    def get_weight(self):
        return self.get_item("weight")
    
    def set_weight(self, weight):
        self.set_item(weight, "weight")
    

    def get_postal_code(self):
        return self.get_item("postal_code")
    
    def set_postal_code(self, postal_code):
        self.set_item(postal_code, "postal_code")

    
    def get_area(self):
        return self.get_item("area")
    
    def set_area(self, area):
        self.set_item(area, "area")


    def get_admission(self):
        return self.get_item("admission_date")

    def get_login_date(self):
        return self.get_item("login_date")
    

    def set_login_date(self):

        login_date = str(int(time.time()))
        self.set_item(login_date, "login_date")
   
