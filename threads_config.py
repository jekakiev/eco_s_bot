# threads_config.py

# Мапінг токенів: {Назва токена: (ID треда, Контрактна адреса)}
TOKEN_CONFIG = {
    "ROSTIKSON 2.0": (7, "0xcdfb52783591231ea098d9e3207dc6c699513b00"),  
    "S": (4, "0xd44257dde89ca53f1471582f718632e690e46dc2"),             
    "HITCOIN": (9, "0xc95e481e86d71d7892dbb7d1f4e98455e4e52ca7"),       
    "GRIMASS": (5, "0x6ceb7abc1b001b2f874185ac4932e7aee83970ef"),      
}

# Значення за замовчуванням для невідомих токенів
DEFAULT_THREAD_ID = 60
DEFAULT_CONTRACT_ADDRESS = None  # Якщо немає вказаної адреси
