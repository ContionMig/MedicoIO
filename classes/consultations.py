from __init__ import db
from helper import helper, encryption

import time, json

from classes.user_details import UserDetailData
from classes.site_settings import site


class ConsultationData:

    table = 'consultations'

    def __init__(self, c_time=None, c_date=None, comments=None, block=None, unit=None, department=None, userid=None, doctor=None, conid=None, create=False):

        if conid is None:
            conid = helper.random_character(site.get_id_length())
            
        conid = helper.remove_symbol(conid)

        self.__conid = conid

        exist = db.Exist(self.table, "id", self.__conid)
        self.setup_encryption()

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(id, timestamp) VALUES(?, ?);", (self.__conid, str(int(time.time()))))
            db.Commit()


        self.set_c_time(c_time)
        self.set_c_date(c_date)
        self.set_comments(comments)
        self.set_block(block)
        self.set_unit(unit)
        self.set_department(department)
        self.set_userid(userid)
        self.set_doctor(doctor)

        self.__exist = exist
    
    def __str__(self):

        output =  "\n----------- ConsultationData -----------\n"

        return output

    def id(self):
        return self.__conid

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

        seed = helper.random_character(128, seed=f"{self.__conid}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(sec_seed + seed[::-1] + sec_seed), site.get_database_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(seed[::-1] + seed + sec_seed[::-1]), site.get_database_hash()).encode("utf-8")
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
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_consultations_encryption())

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE id = ?;", (val, self.__conid))
    
    def get_item(self, item, to_byte=True):
        
        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False
        
        val = db.Execute(f"SELECT {item} FROM {self.table} WHERE id='{self.__conid}';")[0][0]
        if val is None:
            return "-"

        if encrypt:
            val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_consultations_encryption())
        
        return val


    def get_c_time(self):
        return str(self.get_item("c_time"))
    
    def set_c_time(self, c_time):
        self.set_item(c_time, "c_time")
    
    def get_c_date(self):
        return str(self.get_item("c_date"))
    
    def set_c_date(self, c_date):
        self.set_item(c_date, "c_date")
    
    def get_comments(self):
        return str(self.get_item("comments"))
    
    def set_comments(self, comments):
        self.set_item(comments, "comments")
    
    def get_block(self):
        return str(self.get_item("block"))
    
    def set_block(self, block):
        self.set_item(block, "block")
    
    def get_unit(self):
        return str(self.get_item("unit"))
    
    def set_unit(self, unit):
        self.set_item(unit, "unit")
    
    def get_department(self):
        return str(self.get_item("department"))
    
    def set_department(self, department):
        self.set_item(department, "department")

    def get_userid(self):
        return str(self.get_item("userid"))
    
    def set_userid(self, userid):
        self.set_item(userid, "userid")
    
    def get_doctor(self):
        return str(self.get_item("doctor"))
    
    def set_doctor(self, doctor):
        self.set_item(doctor, "doctor")
    
    def get_timestamp(self):
        return str(self.get_item("timestamp"))
    
    def set_timestamp(self, timestamp):
        self.set_item(timestamp, "timestamp")

    

class ConsultationSystemData():

    table = ConsultationData.table

    def __init__(self, userid):
        self.__userid = userid

    def __str__(self):
        output =  "----------- ConsultationSystemData -----------"
        output += ""

        return output
    
    def create_consultation(self, c_time, c_date, comments, block, unit, department, doctor):
        
        consultation = ConsultationData(c_time=c_time, c_date=c_date, comments=comments, block=block, unit=unit, department=department, userid=self.__userid, doctor=doctor, create=True)
        return consultation
    

    def retrieve_consultation(self):
        r_consultations = db.Execute(f"SELECT id FROM {self.table} WHERE userid='{self.__userid}';")
        all_consultations = []
        
        for x in range(len(r_consultations)):
            curr_con = ConsultationData(conid=r_consultations[x][0])
            all_consultations.append(curr_con)

        return all_consultations
    
    def approved_doctor(self, conid):
        
        consultation = ConsultationData(conid=conid)

        doctor = UserDetailData(userid=consultation.get_doctor(), create=False)
        return f"{doctor.get_fname()} {doctor.get_lname()}"


    def purge_consultations(self, duration=None):

        if not duration is None:
            duration = int(duration)
            now = int(time.time())

            db.Execute(f"DELETE FROM {self.table} WHERE timestamp < ? AND userid = ?", (int(now - duration), self.__userid))
        else:
            db.Execute(f"DELETE FROM {self.table}")

        db.Commit()