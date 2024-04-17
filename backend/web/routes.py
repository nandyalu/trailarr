import pathlib

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


web_router = APIRouter()

parent_path = pathlib.Path(__file__).parent
templates_dir = pathlib.Path(parent_path, "templates")

templates = Jinja2Templates(directory=templates_dir)


@web_router.get("/")
async def serve_homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
