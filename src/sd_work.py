import os
import board
import busio
import storage
import sdcardio
from json_work import write_json, read_json
from rsa import encrypt, decrypt

sck = board.GP10
si = board.GP11
so = board.GP12
cs = board.GP13

spi = busio.SPI(sck, si, so)
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

print("Succesfully init SD")


def append_encrypted():
    with open("/sd/passwords.txt", "r") as file:
        raw_data = file.read().split('\n')

    print(raw_data)
    encrypted_already = len(os.listdir("/sd/enc/")) - 1

    services = read_json("/sd/enc/services.json")

    for i in range(len(raw_data)):
        if raw_data[i]:
            with open(f"/sd/enc/{i + encrypted_already}.txt", "w") as output_file:
                    data = raw_data[i].split("|")
                    output_file.write(f"{data[0]}|{encrypt(data[1])}")
            services[i + encrypted_already] = data[0]
    write_json('/sd/enc/services.json', services)

    with open("/sd/passwords.txt", "w") as file:
        file.write("")

    print("OK")


def decrypt_service(service_id, password):
    with open(f"/sd/enc/{service_id}.txt", "r") as file:
        data = file.read().split("|")

    return [data[0], decrypt(data[1], password)]
