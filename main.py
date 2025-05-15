from fastapi import FastAPI, Request, Form, Query,HTTPException
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import math
import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime
from jinja2 import pass_context

# 日時フィルター
@pass_context
def format_datetime(context, value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return value

# テンプレート設定
templates = Jinja2Templates(directory="templates")
templates.env.filters["format_datetime"] = format_datetime

# アプリ設定
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FILE = Path("data/items.json")
TRASH_FILE = Path("data/trash.json")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def write_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_trash():
    if TRASH_FILE.exists():
        with open(TRASH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def write_trash(data):
    with open(TRASH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/add-form", response_class=HTMLResponse)
def add_form(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

@app.get("/TrashBox-form", response_class=HTMLResponse)
def show_trash(request: Request):
    trash = read_trash()
    return templates.TemplateResponse("trashbox.html", {
        "request": request,
        "trash_items": trash
    })

@app.post("/add")
async def add_item(
    title: str = Form(default=None),
    category: str = Form(default=None),
    comment: str = Form(default=None)
):
    items = load_data()
    new_item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "category": category,
        "comment": comment,
        "created_at": datetime.now().isoformat(),
        "updated_at": None
    }
    items.insert(0, new_item)
    write_data(items)
    return RedirectResponse(url="/?page=1&sort=desc", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort: str = Query("desc"),
    page: int = 1
):
    items = load_data()

    if category:
        items = [item for item in items if item["category"] == category]

    if keyword:
        keyword_lower = keyword.lower()
        items = [item for item in items if keyword_lower in item["title"].lower() or keyword_lower in item["comment"].lower()]

    def parse_dt(item):
        return datetime.fromisoformat(item["created_at"])

    items.sort(key=parse_dt, reverse=(sort != "asc"))

    per_page = 10
    total_pages = max(math.ceil(len(items) / per_page), 1)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": list(enumerate(paginated_items)),
        "category": category,
        "keyword": keyword,
        "sort": sort,
        "current_page": page,
        "total_pages": total_pages
    })

@app.get("/edit/{item_id}", response_class=HTMLResponse, name="edit")
async def edit_form(request: Request, item_id: str):
    items = load_data()
    for item in items:
        if item["id"] == item_id:
            return templates.TemplateResponse("edit.html", {
                "request": request,
                "item": item,
                "item_id": item_id
            })
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/edit/{item_id}", name="update_item")
async def update_item(item_id: str, title: str = Form(...), category: str = Form(...), comment: str = Form(...)):
    items = load_data()
    for item in items:
        if item["id"] == item_id:
            item["title"] = title
            item["category"] = category
            item["comment"] = comment
            item["updated_at"] = datetime.now().isoformat()
            write_data(items)
            return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/delete/{item_id}", name="delete_item")
async def delete_item(item_id: str):
    items = load_data()
    new_items = []
    deleted_item = None

    for item in items:
        if item["id"] == item_id:
            deleted_item = item
        else:
            new_items.append(item)

    if deleted_item:
        write_data(new_items)
        trash = read_trash()
        trash.insert(0, deleted_item)
        write_trash(trash)
        return RedirectResponse(url="/", status_code=303)

    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/restore/{item_id}", name="restore_item")
async def restore_item(item_id: str):
    trash = read_trash()
    items = load_data()

    new_trash = []
    restored_item = None

    for item in trash:
        if item["id"] == item_id:
            restored_item = item
        else:
            new_trash.append(item)

    if restored_item:
        items.insert(0, restored_item)
        write_data(items)
        write_trash(new_trash)
        return RedirectResponse(url="/TrashBox-form", status_code=303)

    raise HTTPException(status_code=404, detail="Item not found")
