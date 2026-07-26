# Import Base and all model classes so they are registered with metadata
from app.db.database import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.evaluation import Evaluation  # noqa: F401
from app.models.parent_student import ParentStudent  # noqa: F401
