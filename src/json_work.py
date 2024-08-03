import json
import adafruit_hashlib


def read_json(path):
    with open(f'{path}', "r") as json_data:
        json_read = json.load(json_data)

    return json_read


def write_json(path, object):
    with open(f'{path}', 'w') as json_data:
        json.dump(object, json_data)



def encrypt_private_key(private_key, password):
    data = read_json("key.json")

    encrypted = []
    for i in range(2):
        tmp = []
        for j in range(len(str(private_key[i]))):
            tmp.append(
                str(int(str(private_key[i])[j]) ^ int(bytes(password, 'utf-8').hex(), 16))
                )
        encrypted.append(' '.join(tmp))

    return encrypted


def decrypt_private_key(private_key, password):
    data = read_json("key.json")

    if adafruit_hashlib.sha256(password).digest().hex() != data["phash"]:
        return "Incorrect password"

    decrypt = []
    for i in range(2):
        tmp = []
        for j in private_key[i].split():
            tmp.append(
                str(int(j) ^ int(bytes(password, 'utf-8').hex(), 16))
                )
        decrypt.append(int(''.join(tmp)))

    return decrypt


def write_and_encrypt_private_key(private_key, password):
    data = {
        "key": encrypt_private_key(private_key, password),
        "phash": adafruit_hashlib.sha256(password).digest().hex()
    }

    write_json("key.json", data)


def read_and_decrypt_private_key(password):
    data = read_json("key.json")

    return decrypt_private_key(data["key"], password)
