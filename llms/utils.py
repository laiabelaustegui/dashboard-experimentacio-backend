from cryptography.fernet import Fernet
from django.conf import settings

def encrypt(text):
    fernet = Fernet(settings.SECRET_KEY_ENCRYPT)
    return fernet.encrypt(text.encode()).decode()

def decrypt(token):
    fernet = Fernet(settings.SECRET_KEY_ENCRYPT)
    return fernet.decrypt(token.encode()).decode()
