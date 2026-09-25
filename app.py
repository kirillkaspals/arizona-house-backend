import time
from typing import List, Optional, Dict
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Arizona RP Property Tracker")

SECRET_KEY = "usefguIHSFUSDFGUjhjfk88448"

# Хранилище данных в памяти
property_data: Dict[str, dict] = {}

# Pydantic модели для валидации данных от Lua-скрипта
class Entry(BaseModel):
    propType: str
    pd: int
    propId: Optional[int] = None
    pos: Optional[int] = None

class UpdatePayload(BaseModel):
    server: str
    scanner: Optional[str] = "Аноним"
    entries: List[Entry]

# --- API Endpoints ---

@app.post("/update")
async def update_data(payload: UpdatePayload, x_secret_key: Optional[str] = Header(None)):
    if x_secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Secret Key")
    
    server = payload.server
    houses = [e.dict() for e in payload.entries if e.propType == "house"]
    businesses = [e.dict() for e in payload.entries if e.propType == "business"]
    
    current_time = time.strftime("%H:%M:%S", time.localtime())
    
    property_data[server] = {
        "houses": houses,
        "businesses": businesses,
        "scanner": payload.scanner,
        "updatedAt": current_time
    }
    
    print(f"[{current_time}] Обновлен сервер {server}: {len(houses)} домов, {len(businesses)} бизнесов")
    return {"status": "ok", "message": "Data received"}


@app.get("/time")
async def get_time():
    return {"time": int(time.time())}


# --- Веб-интерфейс ---

ALL_SERVERS = [
    "Phoenix", "Tucson", "Scottdale", "Chandler", "Brainburg", "Saint-Rose",
    "Mesa", "Red-Rock", "Yuma", "Surprise", "Prescott", "Glendale",
    "Kingman", "Winslow", "Payson", "Gilbert", "Show Low", "Casa-Grande",
    "Page", "Sun-City", "Queen-Creek", "Sedona", "Holiday", "Wednesday",
    "Yava", "Faraway", "Bumble Bee", "Christmas", "Love", "Mirage", "Drake", "Space"
]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    server_cards_html = ""
    
    for server_name in ALL_SERVERS:
        data = property_data.get(server_name)
        has_houses = data and len(data.get("houses", [])) > 0
        has_businesses = data and len(data.get("businesses", [])) > 0
        has_data = has_houses or has_businesses

        updated_at_html = f'<div class="server-meta"><span class="server-time">Обновлено: {data["updatedAt"]} MSK</span></div>' if data else ''

        if has_data:
            houses_list = ""
            if has_houses:
                items = "".join([
                    f'''<li class="property-item">
                            <span class="property-id">{"Дом №" + str(item["propId"]) if item.get("propId") else f"{idx+1}. Дом"}</span>
                            <span class="property-pd">{item["pd"]} PayDay</span>
                        </li>'''
                    for idx, item in enumerate(data["houses"])
                ])
                houses_list = f'<ul class="property-list">{items}</ul>'
            else:
                houses_list = '<div class="empty-text">Нет домов</div>'

            businesses_list = ""
            if has_businesses:
                items = "".join([
                    f'''<li class="property-item">
                            <span class="property-id">{"Бизнес №" + str(item["propId"]) if item.get("propId") else f"{idx+1}. Бизнес"}</span>
                            <span class="property-pd">{item["pd"]} PayDay</span>
                        </li>'''
                    for idx, item in enumerate(data["businesses"])
                ])
                businesses_list = f'<ul class="property-list">{items}</ul>'
            else:
                businesses_list = '<div class="empty-text">Нет бизнесов</div>'

            body_content = f'''
                <div class="categories-grid">
                    <div class="category-box">
                        <div class="category-title house">
                            <span>🏠 Дома</span>
                            <span>({len(data["houses"])})</span>
                        </div>
                        {houses_list}
                    </div>
                    <div class="category-box">
                        <div class="category-title business">
                            <span>💼 Бизнесы</span>
                            <span>({len(data["businesses"])})</span>
                        </div>
                        {businesses_list}
                    </div>
                </div>
            '''
        else:
            body_content = f'<div class="empty-text">Нет актуальных данных по серверу {server_name}</div>'

        server_cards_html += f'''
        <div class="server-card">
            <div class="server-header">
                <div class="server-title">🌐 Сервер: {server_name}</div>
                {updated_at_html}
            </div>
            {body_content}
        </div>
        '''

    html_content = f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Arizona RP — Мониторинг слетов</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #0b0c10;
                --card-bg: #14161d;
                --box-bg: #1c1f2b;
                --border-color: #2a2e3d;
                --accent-green: #22c55e;
                --accent-blue: #3b82f6;
                --text-main: #f3f4f6;
                --text-muted: #8c93a4;
                --pd-bg: rgba(239, 68, 68, 0.12);
                --pd-color: #f87171;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 30px 15px;
                display: flex;
                justify-content: center;
            }}
            .container {{
                width: 100%;
                max-width: 850px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 10px;
            }}
            .header h1 {{
                font-size: 26px;
                font-weight: 700;
                margin: 0 0 8px 0;
            }}
            .header p {{
                color: var(--text-muted);
                margin: 0;
                font-size: 14px;
            }}
            .server-card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 20px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            }}
            .server-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 14px;
                margin-bottom: 16px;
            }}
            .server-title {{
                font-size: 18px;
                font-weight: 600;
            }}
            .server-time {{
                font-size: 12px;
                color: var(--text-muted);
                background: #1c1f2b;
                padding: 5px 10px;
                border-radius: 6px;
                border: 1px solid var(--border-color);
            }}
            .categories-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }}
            @media (max-width: 640px) {{
                .categories-grid {{ grid-template-columns: 1fr; }}
            }}
            .category-box {{
                background-color: var(--box-bg);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 14px;
            }}
            .category-title {{
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .category-title.house {{ color: var(--accent-green); }}
            .category-title.business {{ color: var(--accent-blue); }}
            .property-list {{
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .property-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--card-bg);
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 14px;
                border: 1px solid rgba(255, 255, 255, 0.03);
            }}
            .property-id {{ font-weight: 500; }}
            .property-pd {{
                font-weight: 600;
                color: var(--pd-color);
                background: var(--pd-bg);
                padding: 3px 8px;
                border-radius: 5px;
                font-size: 13px;
            }}
            .empty-text {{
                color: var(--text-muted);
                font-size: 13px;
                text-align: center;
                padding: 12px 0;
            }}
        </style>
        <script>
            setInterval(() => {{ location.reload(); }}, 15000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Arizona RP — Мониторинг Слетов</h1>
                <p>Списки слетающих домов и бизнесов по серверам</p>
            </div>
            {server_cards_html}
        </div>
    </body>
    </html>
    '''
    return html_content

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
