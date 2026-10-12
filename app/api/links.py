from fastapi import APIRouter, HTTPException, Query, Request
from datetime import datetime, timezone, date

from app.core.deps import db_dependency, user_dependency
from app.schemas.link_schema import LinkCreateReq, LinkResponse, LinkUpdateReq
from app.models import link_model, clicks_model
from app.services.shortcode import url_to_shortcode

router = APIRouter(tags=["links"])


#Future feature: temp db for storing links with expiry date, and a background task to delete expired links. For now, we will just store the links in the database without any expiry date for shorturl without login.

@router.post("/create_link")
async def create_link(link_req: LinkCreateReq, db: db_dependency, token_user: user_dependency, request: Request):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.original_url == link_req.original_url).first()
    if db_link:
        return {
            "message": "Link already exists",
            "short_code": db_link.short_code,
            "Short Url": db_link.short_code,
            "Short Link": str(request.base_url) + db_link.short_code
        }
    
    if link_req.custom_alias:
        short_code = f"{token_user['token_username']}/{link_req.custom_alias}"
        if db.query(link_model.Link).filter(link_model.Link.short_code == short_code).first():
            raise HTTPException(status_code=409, detail="Custom alias already taken")
    else:
        short_code=url_to_shortcode(token_user["token_username"])

    new_shortcode = link_model.Link(
        short_code=short_code,
        original_url=link_req.original_url,
        owner_id=token_user["token_userid"],
        created_at=date.today()
    )
    db.add(new_shortcode)
    db.commit()

    short_code_link = str(request.base_url) + short_code
    return {
        "message": "Link created successfully",
        "short_code": short_code,
        "Short Url": short_code,
        "Short Link": short_code_link
    }

@router.get("/user/all_links")
def get_all_links(token_user: user_dependency,db: db_dependency, limit: int = Query(default=20, ge=1, le=100),offset: int = Query(default=0, ge=0)) -> list[LinkResponse]:
    db_links = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"]).offset(offset).limit(limit).all()

    return [LinkResponse(
        original_url=link.original_url,
        short_code=link.short_code,
        created_at=link.created_at
    ) for link in db_links]

@router.get("/user/link/clicks/stats/count/{shorturl:path}")
async def get_clicks_count(shorturl: str, db: db_dependency, token_user: user_dependency):
    db_clicks = db.query(clicks_model.Clicks).join(link_model.Link).filter(link_model.Link.short_code == shorturl, link_model.Link.owner_id == token_user["token_userid"]).count()
    if not db_clicks:
        raise HTTPException(status_code=404, detail="No clicks found for this shorturl")
    return db_clicks

@router.get("/user/link/clicks/stats/history/{shorturl:path}")
async def get_clicks_history(shorturl: str, db: db_dependency, token_user: user_dependency):
    db_clicks = db.query(clicks_model.Clicks).join(link_model.Link).filter(link_model.Link.short_code == shorturl, link_model.Link.owner_id == token_user["token_userid"]).all()
    if not db_clicks:
        raise HTTPException(status_code=404, detail="No clicks found for this shorturl")
    return db_clicks


@router.put("/shorturl_update/{shorturl:path}/")
async def update_shorturl(shorturl: str, req: LinkUpdateReq, db: db_dependency, token_user: user_dependency, request: Request):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.short_code == shorturl).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Short URL not found")

    db_url_check = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.original_url == req.original_url).first()
    if db_url_check:
        return {"message": "Link already exists", "short_link": str(request.base_url) + db_url_check.short_code}
    
    else:
        db_link.original_url = req.original_url
        db.commit()

        key = f"link:{shorturl}"
        request.app.state.redis.delete(key)

        return {"message": "URL updated successfully", "new_url": req.original_url, "short_url": shorturl, "short_link":str(request.base_url) + shorturl}

@router.delete("/shorturl_delete/{shorturl:path}/")
async def delete_shorturl(shorturl: str, db: db_dependency, token_user: user_dependency, request: Request):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.short_code == shorturl).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="URL not found")

    key = f"link:{shorturl}"
    request.app.state.redis.delete(key)

    db.delete(db_link)
    db.commit()
    return {"message": "Shorturl deleted successfully", "short_url": shorturl}