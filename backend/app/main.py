import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.auth import router as auth_router
from app.api.quotes import router as quotes_router
from app.api.advisor import router as advisor_router
from app.api.kyc import router as kyc_router
from app.api.orders import router as orders_router
from app.api.operations import router as operations_router
from app.api.recommendations import router as recommendations_router
from app.api.leads import router as leads_router
from app.api.catalog import router as catalog_router
from app.api.feasibility import router as feasibility_router

from app.database import create_session_factory
from app.services.eligibility.engine import EligibilityEngine
from app.services.advisor.conversation import ConversationService
from app.services.kyc import KycService
from app.services.catalogue.loader import load_catalogue
from app.services.orders import OrderService
from app.services.analytics import AnalyticsService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_PATH = PROJECT_ROOT / "YTL_TrackA_Udyam_Digital_Data" / "product_catalogue.csv"

app = FastAPI(title="Accel BizFlow Product Engine", version="0.1.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
catalogue = load_catalogue(CATALOGUE_PATH)
app.state.catalogue = catalogue
app.state.eligibility = EligibilityEngine(catalogue)
app.state.db_session = create_session_factory(PROJECT_ROOT / "backend" / "bizflow.sqlite3")
app.state.conversations_service = ConversationService(app)
app.state.kyc = KycService(
    PROJECT_ROOT / "YTL_TrackA_Udyam_Digital_Data",
    app.state.db_session,
)
app.state.orders = OrderService(
    app.state.db_session,
    catalogue,
    app.state.kyc.feasibility,
)
app.state.analytics = AnalyticsService(
    PROJECT_ROOT / "YTL_TrackA_Udyam_Digital_Data",
    app.state.db_session,
)

app.include_router(auth_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(advisor_router, prefix="/api")
app.include_router(kyc_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(feasibility_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "catalogue_products": len(catalogue)}
