# MedicoIO
[[My Website]](https://mitsuzi.xyz/)

MedicoIO is a database security course project focused on protecting, encrypting, and handling data. It offers many configurations which allow the users to choose different encryption & hashing functions, ID lengths, anti brute force methods, and many others. Its main aim is to keep damages from database leakage as low as possible. This was done by using different encryption keys wherever possible. Each row is encrypted using different key and each table is encrypted using different set of keys. The flexible configuration makes it extremely hard to brute force even if the source code was obtained.

# Screenshots
![main](https://github.com/ContionMig/MedicoIO/blob/main/showcase/Screenshot_2-min.png?raw=true)

# Live Features
- Backup & Restore Database
- Data Masking
- Database Encryption & Decryption
- Password & Sensitive Data Hashing
- Basic CRUD Functionalities
- Authentication & Access Controls
- Session Protection



# Backup & Restore Database
![backup](https://github.com/ContionMig/MedicoIO/blob/main/showcase/Screenshot_11-min.png?raw=true)
Backing up and Restoring can be done within a single click. All backups are stored locally under `database/backups` with the creation timestamp. It does back up the entire database and restores it without the need to restart the server however, there aren't much of edge checks and error handling. There will be some issues with restoring with Flask reloader enabled. 


# Data Masking
![masking](https://github.com/ContionMig/MedicoIO/blob/main/showcase/Screenshot_3-min.png?raw=true)
Extremely basic data masking blocks most of the sensitive information. It just displays the last 4 characters and 1st characters using Flask's filters. It is extremely basic but does get the job done. The user's ID is also generated using their NRIC which gets hashed however, it does exist encrypted in one other table `user_details`. 


# Database Encryption & Decryption
![encryption](https://github.com/ContionMig/MedicoIO/blob/main/showcase/Screenshot_11-min.png?raw=true)
Hashing and encryption mainly uses the `pycryptodome` package. However, the users can choose from these options for their encryption or hashing functions:
- Encryption: `["aes", "arc4", "des", "blowfish", "cast-128"]`
- Hashing: `["md5", "sha1", "sha256", "sha384", "sha512", "sha3_224", "sha3_256", "sha3_384", "sha3_512"]`

All encryption functions also make use of an IV to add an extra layer of security. The keys are generated using a basic algorithm that takes table names and user ID into account, this allows every key used to be generated dynamically. Website Administrators can choose what to encrypt and what not to encrypt by choosing between them. Making the encryption system fully dynamic and according to the administrator's needs.
- “BLOB”: Which will encrypt the selected field
- Other Data Types: Which will not be encrypted


# 2 Factor Authentication
![2factor](https://github.com/ContionMig/MedicoIO/blob/main/showcase/Screenshot_12-min.png?raw=true)
Implementation of 2 Factor Authentication for users. Users can use the Google Authenticator App or Twilio Authy App to authenticate themselves. This is supported by `PyOTP` ans should be relatively easy to understand. One good addon would be recovery codes, allowing the users to disable their 2FA using some randomly generated codes.

# Authentication & Access Controls
Access control limits access for the different users. Upon logging in, the system checks the user level that is assigned to the user account. Each user level has specific page access assigned to it. Only Admins will have access to the access control page. Admins can give or remove specific page access to a specific user level.

4 User levels
- The non-user level (-1): Users who are not logged in to the site and for guest accounts
- The patient level (2): Patients to view their personal records
- The doctor level (1): Doctors to upload and update patient medical records
- The admin level (0): Admins to create, update and delete users



# Session Protection
The session key that is used to generate the session ID is renewed every day. When the session key renews, all active sessions become invalidated and users will be logged out. Session ID expires daily to prevent the session ID from being recycled by an attacker. The session ID is matched to the user’s IP address and user agent. The user agent in this case, refers to the browser and device that was used to login into the system. The 2 factors that determine if the session is valid are:
- IP Address
- User Agent

If any of these changes, the user will automatically be logged out, protecting against man-in-the-middle attacks or session hijacking.


# TO-DO
- Edge Cases & Error Handling
- Messy Code - It was a course project
- UI - I honestly passionately dislike CSS 
