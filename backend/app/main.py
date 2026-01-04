from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.auth import router as auth_router
from app.api.staff import router as staff_router
from app.api.stock import router as stock_router
from app.config import get_settings
from app.models.database import engine, Base
from app.models import *  # Import all models to register them


def create_app() -> FastAPI:
    """
    Application factory for SmartStock 360.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance ready for mounting.
    """

    settings = get_settings()

    app = FastAPI(
        title="SmartStock 360 API",
        description="Backend services for inventory, billing, and intelligence.",
        version="0.1.0",
    )

    # CORS middleware - MUST BE FIRST
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "https://my-bussiness-manager.vercel.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_exceptions_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            import traceback
            error_details = traceback.format_exc()
            print(f"CRITICAL ERROR CAUGHT: {error_details}")
            with open("error.log", "a") as f:
                f.write(f"\n--- ERROR at {request.url} ---\n")
                f.write(error_details)
                f.write("\n----------------------------\n")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "traceback": error_details}
            )

    # Mount static files
    from fastapi.staticfiles import StaticFiles
    import os
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Initialize databases on startup
    @app.on_event("startup")
    async def startup_event():
        """Initialize database tables on application startup."""
        try:
            # Create main database tables
            Base.metadata.create_all(bind=engine)
            
            print("✅ Databases initialized successfully!")
            
            # Check Email Configuration
            if not settings.smtp_username or not settings.smtp_password:
                print("⚠️  Email configuration missing! SMTP_USERNAME or SMTP_PASSWORD not set. Emails will NOT be sent.")
            else:
                 print(f"📧 Email system configured. Sending as: {settings.smtp_from_email}")

        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")

    app.include_router(auth_router, prefix="/api")
    app.include_router(staff_router, prefix="/api")
    app.include_router(stock_router, prefix="/api")
    from app.api.billing import router as billing_router
    app.include_router(billing_router, prefix="/api")
    from app.api.settings import router as settings_router
    app.include_router(settings_router, prefix="/api")
    from app.api.business_setup import router as business_setup_router
    app.include_router(business_setup_router, prefix="/api")
    from app.api.accounts import router as accounts_router

    app.include_router(accounts_router, prefix="/api")

    app.include_router(api_router, prefix="/api")

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """
        Basic health endpoint used by monitors and deployment probes.

        Returns
        -------
        dict[str, str]
            Status payload.
        """

        return {"status": "ok"}
    
    return app


app = create_app()



