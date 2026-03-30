from Crypto.Cipher import AES
import base64
import os

AES_KEY = os.getenv("AES_KEY", "").encode("utf-8")[:32].ljust(32, b"\0")

def decrypt_password(encrypted_base64: str) -> str:
    combined = base64.b64decode(encrypted_base64)
    iv = combined[:16]
    ciphertext = combined[16:]
    
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)
    
    # Remove PKCS7 padding
    pad_len = decrypted[-1]
    return decrypted[:-pad_len].decode("utf-8")