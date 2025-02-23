# threads_config.py

# Мапінг токенів у відповідні треди
TOKEN_CONFIG = {
    "ROSTIKSON 2.0": {
        "thread_id": 7,
        "contract_address": "0xcdfb52783591231ea098d9e3207dc6c699513b00",
    },
    "S": {
        "thread_id": 4,
        "contract_address": "0xd44257dde89ca53f1471582f718632e690e46dc2",
    },
    "HITCOIN": {
        "thread_id": 9,
        "contract_address": "0xc95e481e86d71d7892dbb7d1f4e98455e4e52ca7",
    },
    "GRIMASS": {
        "thread_id": 5,
        "contract_address": "0x6ceb7abc1b001b2f874185ac4932e7aee83970ef",
    },
}

# Значення за замовчуванням, якщо токену немає в списку
DEFAULT_THREAD_ID = 60
DEFAULT_CONTRACT_ADDRESS = None
