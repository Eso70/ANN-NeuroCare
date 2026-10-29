from sqlalchemy.orm import Session

from app.repositories.health import ping_database


def database_is_ready(session: Session) -> bool:
    return ping_database(session)
