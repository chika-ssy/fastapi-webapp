from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form

app = FastAPI()

# Setting up staticFiles and tamplateFolders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# データを一時的に保存するリスト(メモリ上)
items = []

#Sample data
sample_data = [
    {"title": "吾輩は猫である", "category": "書籍", "review": "ユーモアがある", "rating": 4},
    {"title": "千と千尋の神隠し", "category": "映画", "review": "映像が美しい", "rating": 5},
    {"title": "Breaking Bad", "category": "ドラマ", "review": "展開が熱い", "rating": 5}
]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "items": items})

@app.post("/add", response_class=HTMLResponse)
async def add_item(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    review: str = Form(...),
    rating: int = Form(...)
):
    items.append({
        "title": title,
        "category": category,
        "review": review,
        "rating": rating
    })
    return templates.TemplateResponse("index.html", {"request": request, "items": items})
