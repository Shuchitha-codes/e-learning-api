# In Python, a folder is only treated as a module if it contains an empty __init__.py.
# You need them in:
# app/

# app/utils/

# app/routes/

from . import auth
from . import course
from . import progress
from . import analytics
from . import cache
