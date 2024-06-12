import os

from . import fingerprint
from . import launcher
from . import scripts
from .logger import logger

if not os.path.exists(path='sessions'):
    os.mkdir(path='sessions')
