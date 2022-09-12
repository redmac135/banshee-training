from .env import env

if env.bool("LIVE"):
    from .prod import *
else:
    from .dev import *
