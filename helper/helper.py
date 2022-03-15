import hashlib, random, string, re, time


def verify_nric(nric):

    nric = remove_symbol(nric).lower()
    
    if len(nric) != 9:
        return False
    
    if not nric[0].isalpha() and not nric[8].isalpha():
        return False
    
    for x in range(7):
        if not nric[x+1].isdigit():
            return False


    if not nric[0].lower() in ["s", "t", "g", "f", "m"]:
        return False

    return True


def random_range(min_num, max_num):
    return random.randint(min_num, max_num)


def random_character(size=6, chars=string.ascii_uppercase + string.digits, seed=None):
    if not seed is None:
        random.seed(seed)
    else:
        random.seed(str(time.time()))

    return ''.join(random.choice(chars) for _ in range(size))


def filter_messages(msg):
    return msg


def remove_symbol(content):
    content = str(content)
    content = re.sub(r'[^\w]', ' ', content)
    return str(content)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def password_check(password):
    try:
        password = str(password)
        val = True
        error = ""

        if len(password) < 7:
            error = 'Password length should be at least 7'
            val = False
        elif len(password) > 64:
            error = 'Password length should be not be greater than 64'
            val = False
        elif not any(char.isdigit() for char in password):
            error = 'Password should have at least one numeral'
            val = False
        elif not any(char.isupper() for char in password):
            error = 'Password should have at least one uppercase letter'
            val = False
        elif not any(char.islower() for char in password):
            error = 'Password should have at least one lowercase letter'
            val = False


        return [val, error]
    except:
        return [False, 'Invalid Input']


def check_form(user=None, nric=None, f_name=None, l_name=None, gender=None, blood=None):

    error = ""
    val = True

    if not f_name is None and not (len(f_name) >= 2 and len(f_name) < 20):
        error = "Please make sure your first name is belove 20 characters and above 1 chracters!"
        val = False
    
    if not l_name is None and not (len(l_name) >= 2 and len(l_name) < 20):
        error = "Please make sure your last name is belove 20 characters and above 1 chracters!"
        val = False

    if not nric is None and not verify_nric(nric):
        error = "Invalid NRIC number!"
        val = False

    if not gender is None and not gender in ["Male", "Female"]:
        error = "You have selected an invalid gender!"
        val = False
        
    if not blood is None and not blood in ["O", "A", "B", "AB"]:
        error = "You have selected an invalid blood type!"
        val = False
    
    return [val, error]

