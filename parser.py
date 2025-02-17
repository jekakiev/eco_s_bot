

import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
