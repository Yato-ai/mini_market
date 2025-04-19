import gnupg

gpg = gnupg.GPG()

def encrypt_message(message, public_key):
    gpg.import_keys(public_key)
    encrypted_data = gpg.encrypt(message, recipients=None, always_trust=True)
    return str(encrypted_data)

def decrypt_message(cipher_text, passphrase):
    decrypted_data = gpg.decrypt(cipher_text, passphrase=passphrase)
    return str(decrypted_data)
