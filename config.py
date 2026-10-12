"""ShopEase configuration.
Set USE_MYSQL=1 and the MYSQL_* vars to use MySQL.
By default the app runs on SQLite (zero setup) so you can run it immediately.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USE_MYSQL = os.environ.get("USE_MYSQL", "0") == "1"

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DB", "shopease"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
}

SQLITE_PATH = os.path.join(BASE_DIR, "shopease.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "shopease-secret-dev-key")
