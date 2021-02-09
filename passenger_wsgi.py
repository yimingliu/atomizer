import sys, os
INTERP = os.getenv('APP_INTERPRETER')
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

APP_PATH = os.getenv('APP_PATH')
if APP_PATH:
    sys.path.append(APP_PATH)

from app import app as application