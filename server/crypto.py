from __future__ import annotations

import base64

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# CONFIRMED from Aes::.ctor() + <PrivateImplementationDetails>::$$field-33
# in Đại Minh Chủ 8.0.2 Assembly-CSharp.dll. The client uses the same
# 16-byte buffer for AES/Rijndael key and IV, CBC mode, PKCS7 padding.
KEY = bytes.fromhex("03051f0205060315061705202a1f5620")
IV = KEY
BLOCK_BITS = 128


def encrypt_text(text: str) -> str:
    raw = text.encode("utf-8")
    padder = padding.PKCS7(BLOCK_BITS).padder()
    padded = padder.update(raw) + padder.finalize()
    encryptor = Cipher(algorithms.AES(KEY), modes.CBC(IV)).encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_text(value: str) -> str:
    encrypted = base64.b64decode(value)
    decryptor = Cipher(algorithms.AES(KEY), modes.CBC(IV)).decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(BLOCK_BITS).unpadder()
    raw = unpadder.update(padded) + unpadder.finalize()
    return raw.decode("utf-8")
