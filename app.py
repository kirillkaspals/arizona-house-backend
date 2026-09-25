import time
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone

# Секретный ключ (должен совпадать с SECRET_KEY в Lua-скрипте)
SECRET_KEY = "usefguIHSFUSDFGUjhjfk88448"

# База данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./tracker.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ----------------------------------------------------
# Модели БД
# ----------------------------------------------------
class PropertyRecord(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    server = Column(String, index=True)
    scanner = Column(String)
    prop_type = Column(String)  # house / business
    prop_id = Column(Integer, nullable=True)
    pd = Column(Integer)
    pos = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

# ----------------------------------------------------
# FastAPI App & Шаблоны
# ----------------------------------------------------
app = FastAPI(title="Arizona RP Property Tracker API")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------
# Pydantic Модели (схемы входящих JSON)
# ----------------------------------------------------
class EntryItem(BaseModel):
    propType: str
    pd: int
    propId: Optional[int] = None
    pos: Optional[int] = None

class UpdatePayload(BaseModel):
    server: str
    scanner: Optional[str] = "unknown"
    entries: List[EntryItem]

# ----------------------------------------------------
# API Эндпоинты для Lua-скрипта
# ----------------------------------------------------

@app.get("/time")
def get_time():
    """Возвращает текущее время UTC серверу для синхронизации."""
    return {"time": int(time.time())}

@app.post("/update")
def update_tracker(
    payload: UpdatePayload, 
    x_secret_key: Optional[str] = Header(None, alias="X-Secret-Key"),
    db: Session = Depends(get_db)
):
    """Принимает сканы имущества от MoonLoader скрипта."""
    if x_secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid Secret Key")

    # Сохраняем полученные объекты в БД
    for item in payload.entries:
        record = PropertyRecord(
            server=payload.server,
            scanner=payload.scanner or "unknown",
            prop_type=item.propType,
            prop_id=item.propId,
            pd=item.pd,
            pos=item.pos or 0
        )
        db.add(record)
    
    db.commit()
    return {"status": "ok", "saved": len(payload.entries)}

# ----------------------------------------------------
# Веб-интерфейс для сайта
# ----------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def view_dashboard(request: Request, server: Optional[str] = None, db: Session = Depends(get_db)):
    """Отображение таблицы со сканами на веб-странице."""
    query = db.query(PropertyRecord)
    if server:
        query = query.filter(PropertyRecord.server == server)
    
    # Получаем последние 100 записей
    records = query.order_by(PropertyRecord.created_at.desc()).limit(100).all()
    
    # Список всех серверов для фильтра
    servers = [r[0] for r in db.query(PropertyRecord.server).distinct().all()]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "records": records,
        "servers": servers,
        "selected_server": server
    })
