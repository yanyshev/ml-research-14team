import os
from dotenv import load_dotenv

load_dotenv()

GIGA_KEY = os.getenv('GIGA_KEY')
if not GIGA_KEY:
    raise ValueError("GIGA_KEY is not set!")