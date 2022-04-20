import pytest
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import Session, declarative_base

from birdfeeder.sqlalchemy.explain_helper import get_explain_statement

Base = declarative_base()


class User(Base):
    __tablename__ = "user_account"
    id = Column(Integer, primary_key=True)  # noqa: VNE003
    name = Column(String(30))
    fullname = Column(String)


@pytest.fixture()
def create_sqlite_engine():
    engine = create_engine("sqlite://", echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def create_mysql_engine(empty_db):
    engine = create_engine(empty_db, echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine


def test_explain_with_sqlalchemy_2x_style(create_sqlite_engine):
    stmt = select(User)
    explain = get_explain_statement(stmt)
    assert (
        explain
        == 'EXPLAIN FORMAT=json SELECT user_account.id, user_account.name, user_account.fullname \nFROM user_account'
    )


def test_explain_with_sqlalchemy_2x_style_postgres(create_sqlite_engine):
    stmt = select(User)
    explain = get_explain_statement(stmt, dialect="postgresql")
    assert (
        explain
        == 'EXPLAIN FORMAT=json SELECT user_account.id, user_account.name, user_account.fullname \nFROM user_account'
    )


def test_explain_with_sqlalchemy_1x_style(create_sqlite_engine):
    with Session(create_sqlite_engine) as session:
        stmt = session.query(User)
        explain = get_explain_statement(stmt)
    assert (
        explain
        == 'EXPLAIN FORMAT=json SELECT user_account.id, user_account.name, user_account.fullname \nFROM user_account'
    )
