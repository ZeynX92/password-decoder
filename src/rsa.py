from math import isnan
from json_work import write_and_encrypt_private_key, write_json, read_and_decrypt_private_key, read_json
from random import randint, getrandbits


def mod_exp(base, exponent, modulus):
    result = 1
    base = int(base)
    exponent = int(exponent)
    modulus = int(modulus)

    while exponent > 0:
        if (exponent & 1) == 1:
            result = (result * base) % modulus
        exponent >>= 1
        base = (base * base) % modulus
    return result


def rabin_miller_strong_pseudo_prime_test(n: int, attemps=28) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    s = n - 1
    r = 0
    while s % 2 == 0:
        r += 1
        s //= 2

    while attemps:
        a = randomint(1, n  - 1)

        if mod_exp(a, s, n) != 1:
            for j in range(r):
                if mod_exp(a, (2 ** j) * s, n) == n - 1:
                    break
            else:
                return False
        attemps -= 1
        continue

    return True


def randomint(a, b):
    x = randombits(len(bin(b)) - 2)

    while not (a <= x <= b):
        x = randombits(len(bin(b)) - 2)
    else:
        return x


def randombits(bits: int) -> int:
    ans = '1'
    while bits - 1:
        ans += str(getrandbits(1))
        bits -= 1
    return int(ans, 2)


def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        g, y, x = extended_gcd(b % a, a)
        return (g, x - (b // a) * y, y)


def modular_multiplicative_inverse(a, m):
    gcd, x, y = extended_gcd(a, m)

    if gcd != 1:
        return None
    else:
        return x % m


def generate_keys(bit_size, password='00000000'):
    e = 2 ** 16 + 1

    while True:
        print("Start")
        s = bit_size // 2
        p, q = None, None
        mask = 0b11 << (s - 2) | 0b1
        while True:
            p = randombits(s) | mask
            if p % e != 1 and rabin_miller_strong_pseudo_prime_test(p):
                break

        print("p:", p)

        s = bit_size - s
        mask = 0b11 << (s - 2) | 0b1
        while True:
            q = randombits(s) | mask
            if q != p and q % e != 1 and rabin_miller_strong_pseudo_prime_test(q):
                break

        print("q:", q)

        n = p * q
        phi = (p - 1) * (q - 1)
        d = modular_multiplicative_inverse(e, phi)

        if d and not isnan(d):
            break
    print("d:", d)

    write_and_encrypt_private_key([n, d], password)
    write_json("open.json", {"key": [n, e]})

    return [n, e], [n, d]


def encrypt(message: str):
    encrypted_message = []
    open_key = read_json("open.json")["key"]

    for symbol in message:
        encrypted_message.append(str(mod_exp(ord(symbol), open_key[-1], open_key[0])))

    return ' '.join(encrypted_message)


def decrypt(message: str, password):
    message = [int(i) for i in message.split()]
    private_key = read_and_decrypt_private_key(password)

    if private_key == "Incorrect password":
        return "Incorrect password"

    decrypted_message = []

    for symbol in message:
        decrypted_message.append(chr(mod_exp(symbol, private_key[-1], private_key[0])))

    return ''.join(decrypted_message)

