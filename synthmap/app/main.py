import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from synthmap.app.routers.api import apirouter
from synthmap.app.routers.html import htmlrouter
from synthmap.log.logger import getLogger


log = getLogger(__name__)

app = FastAPI()
try:
    app.state.db_path
except AttributeError:
    app.state.db_path = os.environ.get("SYNTHMAP_DB_PATH") or os.path.expanduser(
        "~/.synthmap/main.db"
    )

# Serves the myriad files from a non-minified cljs compile
# app.mount("/js", StaticFiles(directory="C:\\Code\\frontmap\\public\\js\\"), name="js")

# Serves the root html from frontmap output
# @app.get("/index.html", response_class=FileResponse)
# def app_view():
#    return FileResponse("C:\\Code\\frontmap\\public\\index.html")


app.include_router(htmlrouter)
app.include_router(apirouter)
