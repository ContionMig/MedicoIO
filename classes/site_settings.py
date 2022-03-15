from helper import helper

import time, json, shelve

from sqlitedict import SqliteDict

from globals import *

class SiteSettingsData:

    table = 'site_settings'

    def __init__(self, filename=config["shelve"]["path"]):
        self.db = SqliteDict(filename, autocommit=True)

    def get_max_log(self):

        if not "max_log" in self.db:
            self.db["max_log"] = config['defaults']['max_log']

        return self.db["max_log"]

    def set_max_log(self, max_log):
        self.db["max_log"] = max_log
    

    def get_max_pat(self):

        if not "max_pat" in self.db:
            self.db["max_pat"] = config['defaults']['max_pat']

        return self.db["max_pat"]

    def set_max_pat(self, max_pat):
        self.db["max_pat"] = max_pat


    def get_pass_hash(self):

        if not "pass_hash" in self.db:
            self.db["pass_hash"] = config['defaults']['pass_hash']

        return self.db["pass_hash"]

    def set_pass_hash(self, pass_hash):

        if pass_hash in config["encryption"]["hashes"]:
            self.db["pass_hash"] = pass_hash
    

    def get_hashing_layers(self):

        if not "hashing_layers" in self.db:
            self.db["hashing_layers"] = config['defaults']['hashing_layers']

        return int(self.db["hashing_layers"])

    def set_hashing_layers(self, hashing_layers):
        self.db["hashing_layers"] = int(hashing_layers)


    def get_database_hash(self):

        if not "database_hash" in self.db:
            self.db["database_hash"] = config['defaults']['database_hash']

        return self.db["database_hash"]

    def set_database_hash(self, database_hash):

        if database_hash in config["encryption"]["hashes"]:
            self.db["database_hash"] = database_hash
    

    def get_userbase_hash(self):

        if not "userbase_hash" in self.db:
            self.db["userbase_hash"] = config['defaults']['userbase_hash']

        return self.db["userbase_hash"]

    def set_userbase_hash(self, userbase_hash):

        if userbase_hash in config["encryption"]["hashes"]:
            self.db["userbase_hash"] = userbase_hash
    

    def get_id_length(self):

        if not "id_length" in self.db:
            self.db["id_length"] = config['defaults']['id_length']

        return int(self.db["id_length"])

    def set_id_length(self, id_length):
        self.db["id_length"] = int(id_length)

    def get_userid_masking(self):

        if not "userid_masking" in self.db:
            self.db["userid_masking"] = config['defaults']['userid_masking']

        return self.db["userid_masking"]

    def set_userid_masking(self, userid_masking):
        self.db["userid_masking"] = userid_masking
    

    def get_encryption_keyiv(self):

        if not "encryption_keyiv" in self.db:
            self.db["encryption_keyiv"] = config['defaults']['encryption_keyiv']

        return self.db["encryption_keyiv"]

    def set_encryption_keyiv(self, encryption_keyiv):
        self.db["encryption_keyiv"] = encryption_keyiv
    

    def get_hashing_layers(self):

        if not "hashing_layers" in self.db:
            self.db["hashing_layers"] = config['defaults']['hashing_layers']

        return int(self.db["hashing_layers"])

    def set_hashing_layers(self, hashing_layers):
        self.db["hashing_layers"] = int(hashing_layers)
    

    def get_salt_length(self):

        if not "salt_length" in self.db:
            self.db["salt_length"] = config['defaults']['salt_length']

        return int(self.db["salt_length"])

    def set_salt_length(self, salt_length):
        self.db["salt_length"] = int(salt_length)
    

    def get_layer_algo(self):

        if not "layer_algo" in self.db:
            self.db["layer_algo"] = config['defaults']['layer_algo']

        return self.db["layer_algo"]

    def set_layer_algo(self, layer_algo):

        if layer_algo in config["encryption"]["hashes"]:
            self.db["layer_algo"] = layer_algo
    
    def get_access_control(self):

        if not "access_control" in self.db:
            self.db["access_control"] = {}

        return self.db["access_control"]

    def get_access_control_url(self, url):

        if not "access_control" in self.db:
            self.db["access_control"] = {}
        
        access_control =  self.db["access_control"]
        if not url in access_control:
            access_control[url] = config['website']['default_access']
            self.db["access_control"] = access_control
        
        access_control = self.db["access_control"]

        return access_control[url]

    def set_access_control_url(self, url, access):
        access_control = self.db["access_control"]
        access_control[url] = access
        self.db["access_control"] = access_control

    def get_user_rention(self):

        if not "user_rention" in self.db:
            self.db["user_rention"] = config['defaults']['user_rention']

        return self.db["user_rention"]

    def set_user_rention(self, user_rention):
        self.db["user_rention"] = int(user_rention)

    
    def get_image_rention(self):

        if not "image_rention" in self.db:
            self.db["image_rention"] = config['defaults']['image_rention']

        return self.db["image_rention"]

    def set_image_rention(self, image_rention):
        self.db["image_rention"] = int(image_rention)


    def get_consultation_rention(self):

        if not "consultation_rention" in self.db:
            self.db["consultation_rention"] = config['defaults']['consultation_rention']

        return self.db["consultation_rention"]

    def set_consultation_rention(self, consultation_rention):
        self.db["consultation_rention"] = int(consultation_rention)
    

    def get_encryption_key(self):

        if not "encryption_key" in self.db:
            self.db["encryption_key"] = helper.random_character(128)

        return self.db["encryption_key"]

    def set_encryption_key(self, encryption_key):
        self.db["encryption_key"] = str(encryption_key)



    def get_user_encryption(self):

        if not "user_encryption" in self.db:
            self.db["user_encryption"] = config['encryption']['encrypt'][0]

        return self.db["user_encryption"]

    def set_user_encryption(self, user_encryption):
        self.db["user_encryption"] = str(user_encryption)


    
    def get_user_detail_encryption(self):

        if not "user_detail_encryption" in self.db:
            self.db["user_detail_encryption"] = config['encryption']['encrypt'][0]

        return self.db["user_detail_encryption"]

    def set_user_detail_encryption(self, user_detail_encryption):
        self.db["user_detail_encryption"] = str(user_detail_encryption)
    



    def get_consultations_encryption(self):

        if not "consultations_encryption" in self.db:
            self.db["consultations_encryption"] = config['encryption']['encrypt'][0]

        return self.db["consultations_encryption"]

    def set_consultations_encryption(self, consultations_encryption):
        self.db["consultations_encryption"] = str(consultations_encryption)
    


    def get_log_encryption(self):

        if not "log_encryption" in self.db:
            self.db["log_encryption"] = config['encryption']['encrypt'][0]

        return self.db["log_encryption"]

    def set_log_encryption(self, log_encryption):
        self.db["log_encryption"] = str(log_encryption)

    
    def get_images_encryption(self):

        if not "images_encryption" in self.db:
            self.db["images_encryption"] = config['encryption']['encrypt'][0]

        return self.db["images_encryption"]

    def set_images_encryption(self, images_encryption):
        self.db["images_encryption"] = str(images_encryption)


    def get_blog_encryption(self):

        if not "blog_encryption" in self.db:
            self.db["blog_encryption"] = config['encryption']['encrypt'][0]

        return self.db["blog_encryption"]

    def set_blog_encryption(self, blog_encryption):
        self.db["blog_encryption"] = str(blog_encryption)


    

    

site = SiteSettingsData()