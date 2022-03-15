import random, string, json
import time
from urllib.request import urlopen

from classes.user import UserData

from essential_generators import DocumentGenerator
from markdownify import markdownify

from __init__ import app, db, config

addresses = json.loads(urlopen("https://raw.githubusercontent.com/neosergio/random-address/d8a2ea2f7fcef51725cfea827b51883dbcda873c/random_address/addresses-us-all.min.json").read())
names = json.loads(urlopen("https://raw.githubusercontent.com/dominictarr/random-name/master/first-names.json").read())
gen = DocumentGenerator()

def generate_passwords():
    return str(''.join(random.choice(string.ascii_lowercase) for _ in range(16)))
    
def generate_numbers(char=7):

    output = ""
    for x in range(char):
        output += random.choice(string.digits)
    
    return output

def generate_title():
    return gen.sentence()

def generate_random_image():
    list = ['https://i.pinimg.com/originals/15/be/33/15be33d514f99d4cb6bc453e405cbb6d.jpg',
            'https://images.newindianexpress.com/uploads/user/imagelibrary/2018/12/31/original/Prabu_EPS_Photo11.jpg',
            'https://cdn.dnaindia.com/sites/default/files/styles/full/public/2020/08/16/919650-salman-khan-bigg-boss-14-promo.png']
    
    return random.choice(list)

def generate_body():
    output = ''

    for x in range(random.randint(10, 20)):
        randoms = random.randint(1, 5)
        if randoms == 1:
            imgblock = '<div><img src="' + str(generate_random_image()) + '" alt="Girl in a jacket" width="100%"><br></div>'
            output += imgblock

        output += gen.paragraph() + "<br><br>"
    
    output = markdownify(output)
    return output


def generate_author():
    return str(gen.word() + " " + gen.word())

def generate_demo(limit=50):

    time.sleep(30)
    abc = list(string.ascii_lowercase)

    for x in range(limit):

        try:

            if db.IsClosed():
                time.sleep(10)

            nric = str(random.choice(["s", "t", "g", "f", "m"]).upper() + generate_numbers() + random.choice(abc).upper())

            user = UserData(nric, create=True)
            user.set_password(generate_passwords())
            user.set_user_level(random.randint(0, 2))

            user.details.set_nric(nric)

            address = random.choice(addresses["addresses"])
            user.details.set_addr(address['address1'] + ", " + address['postalCode'])

            user.details.set_blood(random.choice(["O", "A", "B", "AB"]))
            user.details.set_gender(random.choice(["Male", "Female"]))

            user.details.set_fname(random.choice(names))
            user.details.set_lname(random.choice(names))

            email = str(str(random.choice(names)).lower() + "@" + str(random.choice(["gmail", "hotmail", "yahoo"])) + str(random.choice([".com", ".org", ".net"])))

            user.details.set_email(email)
            user.details.set_contact(generate_numbers(8))

            user.details.set_height(random.randint(140, 210))
            user.details.set_weight(random.randint(60, 120))

            user.details.set_area(random.choice(["Central Region", "East Region", "North Region", "North-East Region", "West Region"]))
            user.details.set_postal_code(generate_numbers(6))

            user.blogs.create_blog(generate_title(), generate_author(), generate_body(), generate_random_image(), random.choice(["News", "Updates", "Tips & Tricks", "DIY"]))

            for x in range(random.randint(3, 5)):
                user.consultation.create_consultation(F"{generate_numbers(2)}:{generate_numbers(2)}", F"20{generate_numbers(2)}-{generate_numbers(2)}-{generate_numbers(2)}", generate_body()[:500], random.choice(["A","B","C","D","E"]), generate_numbers(3), random.choice(["Outpatient Department (Consultation)","Medical Department","Nursing Department","Paramedical Department","Rehabilitation Department","Operation Theatre Complex", "Radiology Department", "Dietary Department", "Counseling"]), user.id())
                user.images.create_image(random.choice(["X-Ray", "Ultrasound", "Computed Tomography (CT)", "Magnetic Resonance Imaging (MRI)", "Positron Emission Tomography (PET)"]), image=random.choice(["https://cdn.mos.cms.futurecdn.net/VRv8ab66tAfezxvXdXVpfe-320-80.jpg", "https://lbah.com/wp-content/uploads/2020/03/wildlife-osprey-xray-radiograph.jpg", "https://embed.widencdn.net/img/veritas/bvjp0lg4mc/1200x675px/mri-scan-neck.jpeg", "https://d2cbg94ubxgsnp.cloudfront.net/Pictures/1024x536/3/3/5/108335_p3320329-coloured_sagittal_mri_scans_of_the_human_brain-spl---hero.jpg"]), description=generate_body()[:500], doctor=user.id(), time_taken=f"{generate_numbers(2)}:{generate_numbers(2)}")

            db.Commit()
            time.sleep(3)

            print("User Created")

        except:
            pass


