from __init__ import db
from helper import helper, encryption

import time, json, markdown

import validators
from urllib.request import urlopen

from classes.user_details import UserDetailData
from classes.site_settings import site


class BlogsData:

    table = 'blogs'

    def __init__(self, post_title=None, author=None, content=None, image=None, userid=None, category=None, blogid=None, create=False):

        if blogid is None:
            blogid = helper.random_character(site.get_id_length())
            
        blogid = helper.remove_symbol(blogid)

        self.__blogid = blogid

        exist = db.Exist(self.table, "id", self.__blogid)
        self.setup_encryption()

        if not exist and create:
            db.Execute(f"INSERT INTO {self.table}(id, timestamp) VALUES(?, ?);", (self.__blogid, str(int(time.time()))))
            db.Commit()


        self.set_post_title(post_title)
        self.set_author(author)
        self.set_content(content)
        self.set_image(image)
        self.set_userid(userid)
        self.set_category(category)

        self.__exist = exist
    
    def __str__(self):

        output =  "\n----------- ConsultationData -----------\n"

        return output

    def id(self):
        return self.__blogid

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
        
        seed = helper.random_character(128, seed=f"{self.__blogid}_{self.table}_{site.get_encryption_key()}")
        sec_seed = "".join(sorted(seed)).strip()[64:]

        if site.get_encryption_keyiv() == "hashing":
            key = encryption.hashing.hash(str(seed + seed[::-1] + sec_seed), site.get_database_hash()).encode("utf-8")
            iv = encryption.hashing.hash(str(sec_seed[::-1] + sec_seed + seed[::-1]), site.get_database_hash()).encode("utf-8")
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
            val = encryption.encrypting.encrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_blog_encryption())

        db.Execute(f"UPDATE {self.table} SET {item} = ? WHERE id = ?;", (val, self.__blogid))
    
    def get_item(self, item, to_byte=True):
        
        encrypt = True
        table_info = list(db.Execute(f'PRAGMA TABLE_INFO({self.table})'))

        for x in range(len(table_info)):
            if str(table_info[x][1]).lower() == str(item).lower():
                if str(table_info[x][2]) != "BLOB":
                    encrypt = False
        
        val = db.Execute(f"SELECT {item} FROM {self.table} WHERE id='{self.__blogid}';")[0][0]
        if val is None:
            return "-"

        if encrypt:
            val = encryption.encrypting.decrypt(val, self.key, self.iv, to_byte=to_byte, type=site.get_blog_encryption())
        
        return val


    def get_post_title(self):
        return str(self.get_item("post_title"))
    
    def set_post_title(self, post_title):
        self.set_item(post_title, "post_title")
    

    def get_author(self):
        return str(self.get_item("author"))
    
    def set_author(self, author):
        self.set_item(author, "author")
    

    def get_content(self, marked=True):

        content = self.get_item("content")

        if marked:
            content = markdown.markdown(content)

        return content
    
    def set_content(self, content):
        self.set_item(content, "content")

  
    def get_userid(self):
        return str(self.get_item("userid"))
    
    def set_userid(self, userid):
        self.set_item(userid, "userid")
    
    def get_category(self):
        return str(self.get_item("category"))
    
    def set_category(self, category):
        self.set_item(category, "category")
   
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
        return int(self.get_item("timestamp"))
    
    def set_timestamp(self, timestamp):
        self.set_item(timestamp, "timestamp")

    

class BlogSystemData():

    table = BlogsData.table
 
    def __init__(self, userid):
        self.__userid = userid

    def __str__(self):
        output =  "----------- BlogSystemData -----------"
        output += ""

        return output
    
    def create_blog(self,  post_title, author, content, image, category):
        
        created_image = BlogsData(post_title=post_title, author=author, content=content, image=image, userid=self.__userid, category=category, create=True)
        return created_image
    
    def update_blog(self, blogid, post_title=None, author=None, content=None, image=None, category=None):
        
        created_image = BlogsData(blogid=blogid, post_title=post_title, author=author, content=content, image=image, userid=self.__userid, category=category, create=False)
        return created_image

    def retrive_blogs(self, search=None, limit=None):
        
        if search is None:
            r_blogs = db.Execute(f"SELECT id FROM {self.table} ORDER BY timestamp DESC;")
        else:
            r_blogs = db.Execute(f"SELECT id FROM {self.table} catergory = ?;", (search,))

        all_blogs = []
        
        for x in range(len(r_blogs)):
            curr_con = BlogsData(blogid=r_blogs[x][0])
            all_blogs.append(curr_con)

            if limit:
                if len(all_blogs) >= limit:
                    break

        return all_blogs
    

    def retrive_blog(self, blogid):

        blog = BlogsData(blogid=blogid)
        return blog

    def purge_blogs(self, duration=None):

        if not duration is None:
            duration = int(duration)
            now = int(time.time())

            db.Execute(f"DELETE FROM {self.table} WHERE timestamp < ? AND userid = ?", (int(now - duration), self.__userid))
        else:
            db.Execute(f"DELETE FROM {self.table}")

        db.Commit()