"""Every documented Yandex Tracker v3 endpoint, one tool each.

Modules mirror the sections of the official documentation, so a doc page maps to
exactly one code file. Importing a module registers its tools.
"""

from . import admin as admin  # noqa: F401
from . import boards as boards  # noqa: F401
from . import entities as entities  # noqa: F401
from . import issues as issues  # noqa: F401
from . import queues as queues  # noqa: F401
from . import users as users  # noqa: F401
