import hashlib, random, string, re, base64, os, zlib


from Cryptodome.Cipher import AES, ARC4, DES, Blowfish, CAST
from Cryptodome.Random import get_random_bytes
from Crypto.Hash import SHA3_224, SHA3_256, SHA3_384, SHA3_512

from classes.site_settings import site

from globals import config


class HashData:

    hashes = config["encryption"]["hashes"]

    def hash(self, string, hash, layers=site.get_hashing_layers()):
        
        if not hash in self.hashes:
            raise RuntimeError('Hashing Algorithm Invalid') 
        
        hashed = ""
        if hash == "md5":
            hashed = self.to_md5(string)
        elif hash == "sha256":
            hashed = self.to_sha256(string)
        elif hash == "sha384":
            hashed = self.to_sha384(string)
        elif hash == "sha1":
            hashed = self.to_sha1(string)
        elif hash == "sha512":
            hashed = self.to_sha512(string)
        elif hash == "sha3_224":
            hashed = self.to_sha3_224(string)
        elif hash == "sha3_256":
            hashed = self.to_sha3_256(string)
        elif hash == "sha3_384":
            hashed = self.to_sha3_384(string)
        elif hash == "sha3_512":
            hashed = self.to_sha3_512(string)
        
        if layers:
            return self.hash(hashed, site.get_layer_algo(), layers=layers-1)
        
        return hashed


    def to_sha1(self, string):
        hs = hashlib.sha1(str(string).encode('utf-8')).hexdigest()
        return str(hs)

    def to_sha256(self, string):
        hs = hashlib.sha256(str(string).encode('utf-8')).hexdigest()
        return str(hs)

    def to_sha384(self, string):
        hs = hashlib.sha384(str(string).encode('utf-8')).hexdigest()
        return str(hs)
    
    def to_sha512(self, string):
        hs = hashlib.sha512(str(string).encode('utf-8')).hexdigest()
        return str(hs)
    
    def to_md5(self, string):
        hs = hashlib.md5(str(string).encode('utf-8')).hexdigest()
        return str(hs)

    def to_md5(self, string):
        hs = hashlib.md5(str(string).encode('utf-8')).hexdigest()
        return str(hs)
    
    def to_sha3_224(self, string):
        hs = SHA3_224.new(str(string).encode('utf-8')).hexdigest()
        return str(hs)
    
    def to_sha3_256(self, string):
        hs = SHA3_256.new(str(string).encode('utf-8')).hexdigest()
        return str(hs)
    
    def to_sha3_384(self, string):
        hs = SHA3_384.new(str(string).encode('utf-8')).hexdigest()
        return str(hs)

    def to_sha3_512(self, string):
        hs = SHA3_512.new(str(string).encode('utf-8')).hexdigest()
        return str(hs)

    def urandom_from_random(self, rng, length):
        if length == 0:
            return b''

        import sys
        chunk_size = 65535
        chunks = []
        while length >= chunk_size:
            chunks.append(rng.getrandbits(
                    chunk_size * 8).to_bytes(chunk_size, sys.byteorder))
            length -= chunk_size
        if length:
            chunks.append(rng.getrandbits(length * 8).to_bytes(length, sys.byteorder))
        result = b''.join(chunks)
        return result


hashing = HashData()


class EncryptData:

    encryption = config["encryption"]["encrypt"]

    def encrypt(self, data, key, iv, to_byte=True, type=config["encryption"]["encrypt"][2]):

        if not type in self.encryption:
            raise RuntimeError('Encryption Algorithm Invalid') 
        
        if to_byte:
            data = f"{site.get_encryption_key()}_{data}"

        encrytped = ""
        if type == "aes":
            encrytped = self.aes_encrypt(data, key, iv, to_byte)
        elif type == "arc4":
            encrytped = self.arc4_encrypt(data, key, iv, to_byte)
        elif type == "des":
            encrytped = self.des_encrypt(data, key, iv, to_byte)
        elif type == "blowfish":
            encrytped = self.blowfish_encrypt(data, key, iv, to_byte)
        elif type == "cast-128":
            encrytped = self.cast_encrypt(data, key, iv, to_byte)
        
        encrytped = zlib.compress(encrytped)

        return encrytped

    def decrypt(self, ciphered_data, key, iv, to_byte=True, type=config["encryption"]["encrypt"][2]):

        if not type in self.encryption:
            raise RuntimeError('Encryption Algorithm Invalid') 

        ciphered_data = zlib.decompress(ciphered_data)

        decrypted = ""
        if type == "aes":
            decrypted = self.aes_decrypt(ciphered_data, key, iv, to_byte)
        elif type == "arc4":
            decrypted = self.arc4_decrypt(ciphered_data, key, iv, to_byte)
        elif type == "des":
            decrypted = self.des_decrypt(ciphered_data, key, iv, to_byte)
        elif type == "blowfish":
            decrypted = self.blowfish_decrypt(ciphered_data, key, iv, to_byte)
        elif type == "cast-128":
            decrypted = self.cast_decrypt(ciphered_data, key, iv, to_byte)
        
        if to_byte:
            decrypted = decrypted[len(site.get_encryption_key())+1:]

        return decrypted
    

    def aes_encrypt(self, data, key, iv, to_byte=True):

        if to_byte:
            data = str(data).encode("utf-8")

        cipher = AES.new(key[:32], AES.MODE_CFB, iv=iv[:16])
        ciphered_data = cipher.encrypt(data)
        return ciphered_data
    
    def aes_decrypt(self, ciphered_data, key, iv, to_byte=True):

        cipher = AES.new(key[:32], AES.MODE_CFB, iv=iv[:16])
        original_data = cipher.decrypt(ciphered_data)

        if to_byte:
            return str(original_data.decode('utf-8'))
        else:
            return bytes(original_data)


    def arc4_encrypt(self, data, key, iv, to_byte=True):

        if to_byte:
            data = str(data).encode("utf-8")

        hs = str(hashlib.sha256(key+iv).hexdigest()).encode("utf-8")

        cipher = ARC4.new(hs)
        ciphered_data =  cipher.encrypt(data)
        return ciphered_data
    
    def arc4_decrypt(self, ciphered_data, key, iv, to_byte=True):

        hs = str(hashlib.sha256(key+iv).hexdigest()).encode("utf-8")

        cipher = ARC4.new(hs)
        original_data = cipher.decrypt(ciphered_data)

        if to_byte:
            return str(original_data.decode('utf-8'))
        else:
            return bytes(original_data)
        
    

    def des_encrypt(self, data, key, iv, to_byte=True):

        if to_byte:
            data = str(data).encode("utf-8")

        cipher = DES.new(key[:8], DES.MODE_CFB, iv=iv[:8])
        ciphered_data = cipher.encrypt(data)
        return ciphered_data
    
    def des_decrypt(self, ciphered_data, key, iv, to_byte=True):

        cipher = DES.new(key[:8], DES.MODE_CFB, iv=iv[:8])
        original_data = cipher.decrypt(ciphered_data)

        if to_byte:
            return str(original_data.decode('utf-8'))
        else:
            return bytes(original_data)

    

    def blowfish_encrypt(self, data, key, iv, to_byte=True):

        if to_byte:
            data = str(data).encode("utf-8")

        cipher = Blowfish.new(key[:56], Blowfish.MODE_CFB, iv=iv[:8])
        ciphered_data = cipher.encrypt(data)
        return ciphered_data
    
    def blowfish_decrypt(self, ciphered_data, key, iv, to_byte=True):

        cipher = Blowfish.new(key[:56], Blowfish.MODE_CFB, iv=iv[:8])
        original_data = cipher.decrypt(ciphered_data)

        if to_byte:
            return str(original_data.decode('utf-8'))
        else:
            return bytes(original_data)

    
    def cast_encrypt(self, data, key, iv, to_byte=True):

        if to_byte:
            data = str(data).encode("utf-8")

        cipher = CAST.new(key[:16], CAST.MODE_CFB, iv=iv[:8])
        ciphered_data = cipher.encrypt(data)
        return ciphered_data
    
    def cast_decrypt(self, ciphered_data, key, iv, to_byte=True):

        cipher = CAST.new(key[:16], CAST.MODE_CFB, iv=iv[:8])
        original_data = cipher.decrypt(ciphered_data)

        if to_byte:
            return str(original_data.decode('utf-8'))
        else:
            return bytes(original_data)
    
            
encrypting = EncryptData()