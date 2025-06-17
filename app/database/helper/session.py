from sqlalchemy.orm import Session

from .common import handle_sqlalchemy_error
from app.database.models.session import get_session_table


class SessionResponse:
    def __init__(self, id: str, user_id: str):
        self.id = id
        self.user_id = user_id


@handle_sqlalchemy_error
def create_session(db: Session, namespace_id: str, user_id: str):
    session_table = get_session_table(namespace_id)
    session = session_table(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@handle_sqlalchemy_error
def get_sessions(db: Session, namespace_id: str, query_args: dict):
    session_table = get_session_table(namespace_id)
    return db.query(session_table).filter_by(**query_args).all()
