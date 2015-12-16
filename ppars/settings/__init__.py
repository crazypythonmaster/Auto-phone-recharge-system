print(__file__, 'loaded')

from .defaults import *

try:
    from .settings_local import *
except ImportError as e:
    print '**** settings_local.py not found ***'
    # logging.error("Can't find settings_local.py settings")
    print e