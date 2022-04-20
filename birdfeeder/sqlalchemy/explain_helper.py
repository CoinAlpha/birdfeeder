import importlib
from typing import Union

from sqlalchemy.orm import Query
from sqlalchemy.sql import Select


def get_explain_statement(query: Union[Query, Select], dialect: str = "mysql") -> str:
    """Returns EXPLAIN statement for a SQL query."""
    dialect_ = importlib.import_module(f"sqlalchemy.dialects.{dialect}")
    if isinstance(query, Select):
        # 1.4 style selects
        compiled_query = query.compile(compile_kwargs={"literal_binds": True}, dialect=dialect_.dialect())
    else:
        # 1.3 style when we pass session.query()
        compiled_query = query.statement.compile(compile_kwargs={"literal_binds": True}, dialect=dialect_.dialect())
    statement = f"EXPLAIN FORMAT=json {str(compiled_query)}"
    return statement
