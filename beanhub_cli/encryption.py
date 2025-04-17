import io


def decrypt_file(
    input_file: io.BytesIO, output_file: io.BytesIO, iv: bytes, key: bytes
):
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import algorithms
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers import modes

    cipher = Cipher(algorithms.AES256(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padder = padding.PKCS7(128).unpadder()
    while True:
        chunk = input_file.read(4096)
        if not chunk:
            break
        decrypted = decryptor.update(chunk)
        unpadded_chunk = padder.update(decrypted)
        output_file.write(unpadded_chunk)
    output_file.write(padder.update(decryptor.finalize()))
    output_file.write(padder.finalize())
    output_file.flush()
    output_file.seek(0)
