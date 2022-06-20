from fastapi import Request


def db_conn(request: Request):
    return request.app.state.db_path
