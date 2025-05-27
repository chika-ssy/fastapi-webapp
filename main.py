from fastapi import FastAPI, Request, Form, Query, HTTPException, Depends
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

from fastapi import FastAPI

import logging

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



# 日時文字列を "YYYY-MM-DD HH:MM" 形式に整形(Jinja2用フィルター)
@pass_context
def format_datetime(context, value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return value

templates = Jinja2Templates(directory="templates")
templates.env.filters["format_datetime"] = format_datetime


DATA_FILE = Path("data/items.json")

# item.jsonからデータ読み込み
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def read_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def write_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 登録日時によるソート
def parse_dt(item):
    return datetime.fromisoformat(item["created_at"])

# データ追加フォームを表示するルート
@app.get("/add-form", response_class=HTMLResponse)
def add_form(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

# ごみ箱内を表示するルート（削除済みデータ一覧）
@app.get("/TrashBox-form", response_class=HTMLResponse)
def show_trash(request: Request):
    trash = read_trash()
    return templates.TemplateResponse("trashbox.html", {
        "request": request,
        "trash_items": trash
    })

# フォーム送信による追加処理
@app.post("/add")
async def add_item(
    title: str = Form(...),
    category: str = Form(...),
    comment: str = Form("")
):
    items = load_data()
    new_item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "category": category,
        "comment": comment,
        "created_at": datetime.now().isoformat()
    }
    items.insert(0, new_item)
    write_data(items)
    return RedirectResponse(url="/?page=1&sort=desc", status_code=303)

# 分類処理
@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort: str = Query("desc"),
    page: int = 1
):
    items = load_data()

    # カテゴリフィルター
    if category:
        items = [item for item in items if item["category"] == category]

    # キーワードフィルター
    if keyword:
        keyword_lower = keyword.lower()
        items = [
            item for item in items
            if keyword_lower in item["title"].lower() or keyword_lower in item["comment"].lower()
        ]



    items.sort(key=parse_dt, reverse=(sort != "asc"))
    templates.env.filters["format_datetime"] = format_datetime

    # ページネーション処理
    per_page = 10
    total_pages = max(math.ceil(len(items) / per_page), 1)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]


    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": list(enumerate(paginated_items)),
            "category": category,
            "keyword": keyword,
            "sort": sort,
            "current_page": page,
            "total_pages": total_pages
        }
    )


# # 編集フォーム表示
# @app.get("/edit/{item_id}", response_class=HTMLResponse, name="edit")
# def edit_item_form(request: Request, item_id: str):
#     items = load_data()
#     item = next((item for item in items if item["id"] == item_id), None)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")

#     return templates.TemplateResponse("edit.html", {
#         "request": request,
#         "item_id": item_id,
#         "item": item
#     })

# # 編集データの更新処理
# @app.post("/edit/{item_id}")
# def update_item(item_id: str,
#                 title: str = Form(...),
#                 category: str = Form(...),
#                 comment: str = Form(...)):
#     items = load_data()
#     for item in items:
#         if item["id"] == item_id:
#             item["title"] = title
#             item["category"] = category
#             item["comment"] = comment
#             item["updated_at"] = datetime.now().isoformat()
#             break
#     else:
#         raise HTTPException(status_code=404, detail="Item not found")
#     # 更新日時を追記
#     write_data(items)
#     return RedirectResponse("/", status_code=303)

# # 削除処理(ソフト削除)
# @app.post("/delete/{item_id}", name="delete_item")
# def delete_item(request: Request, item_id: str):
#     data = read_data()  # data.json から読み込み
#     trash = read_trash()  # trash.json から読み込み

#     item_to_delete = None
#     for item in data:
#         if item["id"] == item_id:
#             item_to_delete = item
#             break

#     if item_to_delete:
#         data.remove(item_to_delete)
#         trash.append(item_to_delete)
#         write_data(data)
#         write_trash(trash)

    # return RedirectResponse(url="/", status_code=303)
    
# trash.json から削除データを読み込む
def read_trash():
    if os.path.exists("trash.json"):
        with open("trash.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []
# trash.json に削除データを書き込む
def write_trash(data):
    with open("trash.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# '''
# # データを一時的に保存するリスト(メモリ上)
# items = []

# #Sample data
# sample_data = [
#     {"title": "吾輩は猫である", "category": "書籍", "review": "ユーモアがある", "rating": 4},
#     {"title": "千と千尋の神隠し", "category": "映画", "review": "映像が美しい", "rating": 5},
#     {"title": "Breaking Bad", "category": "ドラマ", "review": "展開が熱い", "rating": 5}
# ]
# '''