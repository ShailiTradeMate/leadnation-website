"""LeadNation API — thin entrypoint. Domain logic lives in routers + brain/."""
import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from core import client, db  # noqa: F401  (db kept for shell/debug)

# Domain routers
import reference, engines, search, leads, trade_tools, ai, content, services, admin, analytics, customs, auth, trade_intel, duty_engine, compile_engine, accounts
from admin import CMS_COLLECTIONS, _seed_collection
from auth import seed_settings
from firebase_auth import init_firebase

# Brain (Phase 7 intelligence layer)
from brain.routes import router as brain_router
from brain.admin_routes import router as brain_admin_router
from brain.knowledge import seed_knowledge_base

app = FastAPI(title="LeadNation — Global Trade Intelligence API")

api_router = APIRouter(prefix="/api")
for mod in (reference, engines, search, leads, trade_tools, ai, content, services, admin, analytics, customs, auth, trade_intel, duty_engine, compile_engine, accounts):
    api_router.include_router(mod.router)
api_router.include_router(brain_router)
api_router.include_router(brain_admin_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=__import__("os").environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def _startup():
    init_firebase()
    for name, source in CMS_COLLECTIONS.items():
        try:
            await _seed_collection(name, source)
        except Exception as exc:
            logging.warning("Seed failed for %s: %s", name, exc)
    try:
        await seed_knowledge_base()
    except Exception as exc:
        logging.warning("Knowledge base seed failed: %s", exc)
    try:
        await seed_settings()
    except Exception as exc:
        logging.warning("Settings seed failed: %s", exc)
    try:
        await duty_engine.seed_rodtep()
        duty_engine.start_scheduler()
    except Exception as exc:
        logging.warning("Duty engine init failed: %s", exc)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
