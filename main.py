from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path

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

DATA_FILE = Path("data.json")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    items = load_data()
    return templates.TemplateResponse("index.html", {"request": request, "items": enumerate(items)})

@app.get("/add", response_class=HTMLResponse)
def add_get(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

@app.post("/add")
def add_post(title: str = Form(...), category: str = Form(...), comment: str = Form(...)):
    items = load_data()
    items.append({"title": title, "category": category, "comment": comment})
    save_data(items)
    return RedirectResponse(url="/", status_code=302)

# 👇 削除機能(POSTで管理)
@app.post("/delete/{item_id}")
def delete_item(item_id: int):
    items = load_data()
    if 0 <= item_id < len(items):
        items.pop(item_id)
        save_data(items)
    return RedirectResponse(url="/", status_code=302)