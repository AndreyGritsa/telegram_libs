from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telegram_libs.constants import MONGO_URI

# Create a new client and connect to the server
mongo_client = MongoClient(MONGO_URI, server_api=ServerApi("1"))