"""AES transport used by Dai Minh Chu 8.0.2 client.

Confirmed from Assembly-CSharp.dll:
- RijndaelManaged / AES-128
- CBC
- PKCS7
- same 16-byte value for Key and IV
"""

from __future__ import annotations

import base64

from Crypto.Cipher import AES

KEY = bytes.fromhex("03051f0205060315061705202a1f5620")
IV = KEY
BLOCK_SIZE = 16


def _pad(data: bytes) -> bytes:
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([pad_len]) * pad_len


def _unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("empty plaintext")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > BLOCK_SIZE:
        raise ValueError("invalid PKCS7 padding length")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("invalid PKCS7 padding bytes")
    return data[:-pad_len]


def encrypt_text(text: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, iv=IV)
    encrypted = cipher.encrypt(_pad(text.encode("utf-8")))
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_text(ciphertext_b64: str) -> str:
    encrypted = base64.b64decode(ciphertext_b64)
    cipher = AES.new(KEY, AES.MODE_CBC, iv=IV)
    plaintext = _unpad(cipher.decrypt(encrypted))
    return plaintext.decode("utf-8")
