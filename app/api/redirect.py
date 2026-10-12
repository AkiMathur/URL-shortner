from fastapi import APIRouter,Depends,Request,BackgroundTasks,HTTPException
from datetime import datetime, timezone
import json
import hashlib
from fastapi.responses import RedirectResponse

from app.database import SessionLocal
from app.models import link_model, clicks_model
from app.core.rate_limit import rate_limit
from app.core.deps import db_dependency

router = APIRouter(tags=["redirect"])



def log_click(link_id: int, ip_hash: str | None = None, user_agent: str | None = None):
    with SessionLocal() as db:
        db.add(clicks_model.Clicks(
            link_id=link_id,
            clicked_at=datetime.now(timezone.utc),
            ip_hash=ip_hash,
            user_agent=user_agent
        ))
        db.commit()


@router.get("/{shorturl:path}", dependencies=[Depends(rate_limit(limit=60, window=60, scope="redirect"))])
def get_link(shorturl: str, request: Request, background_tasks: BackgroundTasks, db: db_dependency):
    key = f"link:{shorturl}"

    cached = request.app.state.redis.get(key)
    if cached:
        data = json.loads(cached)
    else:
        db_link = db.query(link_model.Link).filter(link_model.Link.short_code == shorturl).first()
        if not db_link:
            raise HTTPException(status_code=404, detail="ShortURL not found")
        data = {"id":db_link.id, "url":db_link.original_url}

        request.app.state.redis.setex(key,3600,json.dumps(data))

    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    user_agent = request.headers.get("user-agent", "unknown")

    background_tasks.add_task(log_click, data['id'], ip_hash, user_agent)
    return RedirectResponse(url=data['url'], status_code=307)