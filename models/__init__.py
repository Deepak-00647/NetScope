from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User        # noqa: E402,F401
from .packet import Packet    # noqa: E402,F401
from .alert import Alert      # noqa: E402,F401
from .report import Report    # noqa: E402,F401
