sql_commands = [
    """CREATE TABLE IF NOT EXISTS user_info (
        id TEXT PRIMARY KEY NOT NULL,

        ip_address BLOB,

        pass BLOB,
        pass_salt BLOB,

        pfp BLOB,
        otp BLOB,

        doctor TEXT,
        login_date TEXT,
        user_level TEXT

    );""",
 
    """CREATE TABLE IF NOT EXISTS user_details (
        id TEXT PRIMARY KEY NOT NULL,

        ic_num BLOB,

        f_name BLOB,
        l_name BLOB,

        addr BLOB,
        contact_num BLOB,
        email BLOB,
        dob BLOB,

        gender BLOB,
        blood_type BLOB,

        postal_code BLOB,
        area BLOB,

        height BLOB,
        weight BLOB,

        login_date TEXT,
        admission_date INT
    );""",

    """CREATE TABLE IF NOT EXISTS consultations (
        id TEXT PRIMARY KEY NOT NULL,

        c_time BLOB,
        c_date BLOB,

        comments BLOB,

        block BLOB,
        unit BLOB,
        department BLOB,

        userid TEXT,
        doctor TEXT,

        timestamp INT
    );""",

    """CREATE TABLE IF NOT EXISTS log_detail (
        id TEXT PRIMARY KEY NOT NULL,

        title BLOB,

        description BLOB,
    
        logid BLOB,

        timestamp INT,
        err_level TEXT
    );""",

    """CREATE TABLE IF NOT EXISTS images (
        id TEXT PRIMARY KEY NOT NULL,

        image BLOB,
        description BLOB,
        time_taken BLOB,

        userid TEXT,
        doctor TEXT,
        catergory TEXT,

        timestamp INT
    );""",

     """CREATE TABLE IF NOT EXISTS blogs (
        id TEXT PRIMARY KEY NOT NULL,

        post_title BLOB,
        author BLOB,
        content BLOB,
        image BLOB,

        userid TEXT,
        category TEXT,

        timestamp INT
    );""",

    """CREATE TABLE IF NOT EXISTS ip_blacklist (
        ip_address TEXT PRIMARY KEY NOT NULL,

        violations TEXT,
        time_out TEXT,

        timestamp INT
    );""",
]
