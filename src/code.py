import board, time, digitalio
import busio, adafruit_ssd1306, board
from sd_work import append_encrypted, decrypt_service
from rsa import encrypt, decrypt, generate_keys
from json_work import write_and_encrypt_private_key, write_json, read_json, read_and_decrypt_private_key

button_dec = digitalio.DigitalInOut(board.GP16)
button_dec.switch_to_input(pull=digitalio.Pull.UP)

button_oke = digitalio.DigitalInOut(board.GP17)
button_oke.switch_to_input(pull=digitalio.Pull.UP)

button_inc = digitalio.DigitalInOut(board.GP19)
button_inc.switch_to_input(pull=digitalio.Pull.UP)

i2c = busio.I2C(board.GP21, board.GP20)

# инициализация дисплея
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.show()


def oled_print(text, x=0, y=0):
    oled.fill(0)
    text = text.split('\n')
    for i in range(len(text)):
        oled.text(text[i], 0, 8 * i, 1, size=1)
    oled.show()


display_mode = 'main'  # password|menu|main

# Global indexes
main_dsp_idx, menu_dsp_idx, password_dsp_idx, pin_idx = 0, 0, 0, 0

# Global options lists
main_dsp_options = ["decrypt", "append", "revoke keys", "revoke pin"]
menu_list = [i[-1] for i in sorted(read_json('/sd/enc/services.json').items())] + ["back"]

# Global flags
pin_in_progress = False
revoke_keys, revoke_pin, revoking_in_progress = False, False, False

# Default values
attempts = 3
alpha = '0123456789'
pin, old_pin = '00000000', '00000000'

while True:
    # Mode init
    if display_mode == 'menu':
        menu_list = [i[-1] for i in sorted(read_json('/sd/enc/services.json').items())] + ["back"]

    if display_mode == 'pin' and not pin_in_progress:
        pin = '00000000'
        pin_l = list(pin)
        mask = ['*'] * 8
        mask[password_dsp_idx] = pin[password_dsp_idx]
        pin_in_progress = True

        oled_print(f"Enter pin for {menu_list[menu_dsp_idx]}\n{''.join(mask)}")

    if display_mode == 'pin' and pin_in_progress:
        pin_l = list(pin)
        pin_l[password_dsp_idx] = alpha[pin_idx]
        pin = ''.join(pin_l)

    # Buttons behavior
    if not button_dec.value:
        while not button_dec.value:
            pass
        print("Decrement button pressed")

        if display_mode == 'main':
            main_dsp_idx = (main_dsp_idx - 1) % len(main_dsp_options)

            oled_print(main_dsp_options[main_dsp_idx])

        if display_mode == 'menu':
            menu_dsp_idx = (menu_dsp_idx - 1) % len(menu_list)

            oled_print(
                f"   {menu_list[(menu_dsp_idx - 1) % len(menu_list)]}\n-> {menu_list[menu_dsp_idx]}\n   {menu_list[(menu_dsp_idx + 1) % len(menu_list)]}\n   {menu_list[(menu_dsp_idx + 2) % len(menu_list)]}")

        if display_mode == 'pin':
            pin_idx = (pin_idx + 1) % len(alpha)

            # Apply pin number shift
            pin_l = list(pin)
            pin_l[password_dsp_idx] = alpha[pin_idx]
            pin = ''.join(pin_l)
            mask = ['*'] * 8
            mask[password_dsp_idx] = pin[password_dsp_idx]

            oled_print(f"Enter pin for {menu_list[menu_dsp_idx]}\n{''.join(mask)}")

    if not button_inc.value:
        while not button_inc.value:
            pass
        print("Increment button pressed")

        if display_mode == 'main':
            main_dsp_idx = (main_dsp_idx + 1) % len(main_dsp_options)

            oled_print(main_dsp_options[main_dsp_idx])

        if display_mode == 'menu':
            menu_dsp_idx = (menu_dsp_idx + 1) % len(menu_list)

            oled_print(
                f"   {menu_list[(menu_dsp_idx - 1) % len(menu_list)]}\n-> {menu_list[menu_dsp_idx]}\n   {menu_list[(menu_dsp_idx + 1) % len(menu_list)]}\n   {menu_list[(menu_dsp_idx + 2) % len(menu_list)]}")

        if display_mode == 'pin':
            password_dsp_idx = (password_dsp_idx + 1) % 8

            # Apply mask shift
            mask = ['*'] * 8
            mask[password_dsp_idx] = pin[password_dsp_idx]

            oled_print(f"Enter pin for {menu_list[menu_dsp_idx]}\n{''.join(mask)}")

    if not button_oke.value:
        while not button_oke.value:
            pass
        print("Oke button pressed")

        if display_mode == 'main':
            # Костыль ALERT: Для экономии памяти обрабатываем только номер опции, а не её str вид
            if main_dsp_idx == 0:  # menu
                display_mode = 'menu'

                oled_print(
                    f"   {menu_list[(menu_dsp_idx - 1) % len(menu_list)]}\n-> {menu_list[menu_dsp_idx]}\n   {menu_list[(menu_dsp_idx + 1) % len(menu_list)]}\n   {menu_list[(menu_dsp_idx + 2) % len(menu_list)]}")

            elif main_dsp_idx == 1:  # append encrypted
                append_encrypted()

                oled_print("Append OK")

            elif main_dsp_idx == 2:  # revoke keys
                revoke_keys = True
                revoke_pin = False
                display_mode = 'pin'

            elif main_dsp_idx == 3:  # revoke pin
                revoke_pin = True
                revoke_keys = False
                display_mode = 'pin'

        elif display_mode == 'menu':
            #  Menu behavior 
            if menu_list[menu_dsp_idx] != 'back':
                display_mode = 'pin'
            else:
                display_mode = 'main'

                oled_print(main_dsp_options[main_dsp_idx])

        elif display_mode == 'pin':
            # Different pin output
            if revoke_keys:  # if revoke keys flag is up
                print("revoke Keys")
                if read_and_decrypt_private_key(pin) != "Incorrect password":  # TODO: Error handler
                    oled_print("Start reloading...")

                    generate_keys(1024, pin)

                    oled_print("Reload successfully")

                    revoke_keys = False  # fall flag down
                else:
                    display_mode = 'main'

            elif revoke_pin:  # id revoke pin flag is up
                print("revoke pin")
                if read_and_decrypt_private_key(pin) != "Incorrect password":  # TODO: Error handler
                    old_pin = pin  # save old pin

                    revoke_pin = False  # change revoke stage to inputting new pin
                    revoking_in_progress = True  # up flag of second stage

                    display_mode = 'pin'
                else:
                    display_mode = 'main'

            elif revoking_in_progress:
                write_and_encrypt_private_key(read_and_decrypt_private_key(old_pin), pin)  # received a new pin revoke

                revoking_in_progress = False  # falling flag down

                oled_print("OK")
                time.sleep(1)

                display_mode = 'main'
            else:
                oled_print("Starting decrypt...")

                s = decrypt_service(menu_dsp_idx, pin)

                if s[-1] == "Incorrect password":
                    oled_print("Incorrect password")
                    display_mode = 'menu'

                    # Block system
                    attempts -= 1
                    if attempts == 0:
                        write_json("key.json", {"0": "Access FAILED!!!"})
                        while True:
                            oled_print("BLOCKED")

                    pin_in_progress = False
                else:
                    oled_print(s[-1])  # display password
                    attempts = 3
                    display_mode = 'menu'

                    pin_in_progress = False

    time.sleep(0.1)
