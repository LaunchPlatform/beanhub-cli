import io
import os
import tempfile
import typing

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes

from beanhub_cli.encryption import decrypt_file

SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5


def encrypt_file(
    input_file: io.BytesIO, output_file: io.BytesIO
) -> typing.Tuple[bytes, bytes]:
    key = os.urandom(32)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES256(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    while True:
        chunk = input_file.read(4096)
        if not chunk:
            break
        padded_chunk = padder.update(chunk)
        output_file.write(encryptor.update(padded_chunk))
    output_file.write(encryptor.update(padder.finalize()))
    output_file.write(encryptor.finalize())
    output_file.flush()
    output_file.seek(0)
    return (key, iv)


def test_decrypt_file():
    data = b"hello there"
    with tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as encrypted_file:
        key, iv = encrypt_file(input_file=io.BytesIO(data), output_file=encrypted_file)
        output = io.BytesIO()
        decrypt_file(input_file=encrypted_file, output_file=output, key=key, iv=iv)
    assert output.getvalue() == data
