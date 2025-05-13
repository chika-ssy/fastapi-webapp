from fastapi import FastAPI, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from typing import Optional
from pathlib import Path
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


'''
# データを一時的に保存するリスト(メモリ上)
items = []

#Sample data
sample_data = [
    {"title": "吾輩は猫である", "category": "書籍", "review": "ユーモアがある", "rating": 4},
    {"title": "千と千尋の神隠し", "category": "映画", "review": "映像が美しい", "rating": 5},
    {"title": "Breaking Bad", "category": "ドラマ", "review": "展開が熱い", "rating": 5}
]
'''

DATA_FILE = Path("data/items.json")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/add-form", response_class=HTMLResponse)
def add_form(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def index(request: Request, category: Optional[str] = Query(None)):
    items = load_data()
    if category:
        items = [item for item in items if item["category"] == category]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": list(enumerate(items)),
            "category": category,
        }
    )

from fastapi import HTTPException

@app.get("/edit/{item_id}", response_class=HTMLResponse)
def edit_item_form(request: Request, item_id: int):
    items = load_data()
    if not (0 <= item_id < len(items)):
        raise HTTPException(status_code=404, detail="Item not found")

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "item_id": item_id,
        "item": items[item_id]
    })

@app.post("/edit/{item_id}")
def update_item(item_id: int,
                title: str = Form(...),
                category: str = Form(...),
                comment: str = Form(...)):
    items = load_data()
    if not (0 <= item_id < len(items)):
        raise HTTPException(status_code=404, detail="Item not found")

    items[item_id]["title"] = title
    items[item_id]["category"] = category
    items[item_id]["comment"] = comment
    items[item_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_data(items)
    return RedirectResponse("/", status_code=303)


@app.post("/add")
async def add_item(
    title: str = Form(...),
    category: str = Form(...),
    comment: str = Form(...)
):
    item = {
        "title": title,
        "category": category,
        "comment": comment,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    items = load_data()  # ここを活用
    items.append(item)
    save_data(items)     # 同様に関数を活用

    return RedirectResponse("/", status_code=303)

# 👇 削除機能(POSTで管理)
@app.post("/delete/{item_id}")
def delete_item(item_id: int):
    items = load_data()
    if 0 <= item_id < len(items):
        items.pop(item_id)
        save_data(items)
    return RedirectResponse(url="/", status_code=302)