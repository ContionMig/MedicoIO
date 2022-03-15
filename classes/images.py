from __init__ import db
from helper import helper, encryption

import time, json, validators

from urllib.request import urlopen

from classes.user_details import UserDetailData
from classes.site_settings import site


class ImagesData:

    table = 'images'

    def __init__(self, catergory=None, image=None, description=None, userid=None, doctor=None, time_taken=None, imacon=None, create=False):

        if imacon is None:
            imacon = helper.random_character(site.get_id_length())
            
        imacon = helper.remove_symbol(imacon)

        self.__imacon = imacon

        exist = db.Exist(self.table, "id", self.__imacon)
        self.setup_encryption()

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(id, timestamp) VALUES(?, ?);", (self.__imacon, str(int(time.time()))))
            db.Commit()


        self.set_catergory(catergory)
        self.set_image(image=image)
        self.set_description(description)
        self.set_userid(userid)
        self.set_doctor(doctor)
        self.set_time_taken(time_taken)

        self.__exist = exist
    
    def __str__(self):

        output =  "\n----------- ImagesData -----------\n"
        print(self.id())

        return output

    def id(self):
        return self.__imacon

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

        seed = helper.random_character(128, seed=f"{self.__imacon}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(sec_seed + sec_seed[::-1] + seed), site.get_database_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(seed[::-1] + sec_seed + seed[::-1]), site.get_database_hash()).encode("utf-8")
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
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_images_encryption())

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE id = ?;", (val, self.__imacon))
    
    def get_item(self, item, to_byte=True):
        
        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False
        
        val = db.Execute(f"SELECT {item} FROM {self.table} WHERE id='{self.__imacon}';")[0][0]
        if val is None:
            return "-"

        if encrypt:
            val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_images_encryption())
        
        return val


    def get_catergory(self):
        return str(self.get_item("catergory"))
    
    def set_catergory(self, catergory):
        self.set_item(catergory, "catergory")
    

    def get_description(self):
        return str(self.get_item("description"))
    
    def set_description(self, description):
        self.set_item(description, "description")
    

    def get_userid(self):
        return str(self.get_item("userid"))
    
    def set_userid(self, userid):
        self.set_item(userid, "userid")

  
    def get_doctor(self):
        return str(self.get_item("doctor"))
    
    def set_doctor(self, doctor):
        self.set_item(doctor, "doctor")
    
    def get_time_taken(self):
        return str(self.get_item("time_taken"))
    
    def set_time_taken(self, time_taken):
        self.set_item(time_taken, "time_taken")
   
    def set_image(self, image=None, path=None):

        if validators.url(str(image)):
            image = urlopen(image).read()

        if path:

            in_file = open(path, "rb")
            data = in_file.read()
            in_file.close()

            image = data

        self.set_item(image, "image", False)
    

    def get_image(self):
        return self.get_item("image", False)

    def get_timestamp(self):
        return str(self.get_item("timestamp"))
    
    def set_timestamp(self, timestamp):
        self.set_item(timestamp, "timestamp")

    

class imagesSystemData():

    table = ImagesData.table
 
    def __init__(self, userid):
        self.__userid = userid

    def __str__(self):
        output =  "----------- imagesSystemData -----------"
        output += ""

        return output
    
    def create_image(self, catergory, image, description, doctor, time_taken):
        
        created_image = ImagesData(catergory=catergory, image=image, description=description, userid=self.__userid, doctor=doctor, time_taken=time_taken, create=True)
        return created_image
    

    def retrive_images(self, search=None):
        
        if search is None:
            r_images = db.Execute(f"SELECT id FROM {self.table} WHERE userid='{self.__userid}';")
        else:
            r_images = db.Execute(f"SELECT id FROM {self.table} WHERE userid = ? AND catergory = ?;", (self.__userid, search))

        all_images = []

        for x in range(len(r_images)):
            curr_con = ImagesData(imacon=r_images[x][0])
            print(x, curr_con)
            all_images.append(curr_con)

        print(all_images)

        return all_images
    

    def retrive_image(self, imacon):

        image = ImagesData(imacon=imacon)
        return image.get_image()

    def approved_doctor(self, imacon):
        
        image = ImagesData(imacon=imacon)

        doctor = UserDetailData(userid=image.get_doctor(), create=False)
        return f"{doctor.get_fname()} {doctor.get_lname()}"


    def purge_images(self, duration=None):

        if not duration is None:
            duration = int(duration)
            now = int(time.time())

            db.Execute(f"DELETE FROM {self.table} WHERE timestamp < ? AND userid = ?", (int(now - duration), self.__userid))
        else:
            db.Execute(f"DELETE FROM {self.table}")

        db.Commit()