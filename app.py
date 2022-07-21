import re
import httpcore
from pymongo import MongoClient
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, RedirectResponse, JSONResponse
from starlette.routing import Route
from secret_keys import MONGO_URI
from pydantic import BaseModel, HttpUrl, ValidationError


class URL(BaseModel):
    url: HttpUrl


def increment(chars: str) -> str:
    char_list = [ord(char) for char in chars]

    for i in range(len(char_list) - 1, -1, -1):
        if char_list[i] == 57:
            char_list[i] = 97
            break
        elif char_list[i] == 122:
            char_list[i] = 65
            break
        elif char_list[i] == 90:
            if i != 0:
                char_list[i] = 48
            else:
                char_list[i] = 48
                char_list.append(48)
        else:
            char_list[i] += 1
            break

    return "".join(chr(char) for char in char_list)


async def index(request: Request) -> FileResponse:
    return FileResponse("./index.html", media_type="text/html")


async def add_link(request: Request) -> JSONResponse | HTTPException:
    body = await request.json()

    try:
        URL.parse_obj(body)
    except ValidationError:
        # Add better error message using pydantic
        raise HTTPException(400)

    url = body["url"]

    # Tests if domain is registered
    try:
        await http.request("GET", url)
    except httpcore.ConnectError:
        raise HTTPException(400)

    # This would be replaced with a transaction to make it more efficient
    key = counter.find_one_and_update(
        {"_id": 0}, {"$set": {"key": increment(counter.find_one({"_id": 0})["key"])}}
    )["key"]

    col.insert_one({"_id": key, "url": url})

    return JSONResponse({"key": key})


async def get_link(request: Request) -> RedirectResponse:
    key = request.path_params["key"]

    if not r.fullmatch(key):
        raise HTTPException(404)

    link = col.find_one({"_id": key})

    if link is None:
        raise HTTPException(404)
    else:
        return RedirectResponse(link["url"], 301)


async def startup():
    global r, http, col, counter
    r = re.compile("^[\\da-zA-Z][\\da-zA-Z-]{2,62}[\\da-zA-Z]$")
    http = httpcore.AsyncConnectionPool()

    client = MongoClient(MONGO_URI)
    col = client["link_shortner"]["links"]
    counter = client["link_shortner"]["counter"]


async def shutdown():
    await http.aclose()


routes = [
    Route("/", index),
    Route("/add-link", add_link, methods=["POST"]),
    # Benchmark
    # Route('/{key:str}', get_link),
    Route("/{key}", get_link),
]

app = Starlette(routes=routes, on_startup=[startup], on_shutdown=[shutdown])
