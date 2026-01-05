from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.auth import router as auth_router
from app.api.staff import router as staff_router
from app.api.stock import router as stock_router
from app.config import get_settings
from app.models.credentials_db import init_credentials_db
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
            
            # Create credentials database tables
            init_credentials_db()
            
            print("✅ Databases initialized successfully!")
            
            # Check Email Configuration
            # Check Email Configuration (SMTP)
            if not settings.smtp_username or not settings.smtp_password:
                print("⚠️  Email configuration missing! SMTP_USERNAME or SMTP_PASSWORD not set. Emails will NOT be sent.")
            else:
                 print(f"📧 Email system configured. Sending as: {settings.smtp_username}")

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
    
    # --- EMERGENCY ADMIN TOOL (Remove later) ---
    from app.models.credentials_db import get_credentials_db, UserCredentials
    from app.models.user import User
    from sqlalchemy.orm import Session
    from fastapi import Depends

    @app.get("/admin/nuke-email")
    def nuke_email_endpoint(email: str, db: Session = Depends(get_db), cred_db: Session = Depends(get_credentials_db)):
        """
        Emergency tool to force-delete a user by email from BOTH databases.
        Usage: /admin/nuke-email?email=test@example.com
        """
        try:
            # Delete from Main DB
            deleted_main = db.query(User).filter(User.email == email).delete(synchronize_session=False)
            
            # Delete from Credentials DB
            deleted_cred = cred_db.query(UserCredentials).filter(UserCredentials.email == email).delete(synchronize_session=False)
            
            db.commit()
            cred_db.commit()
            
            return {
                "status": "success", 
                "message": f"Nuked {email}", 
                "deleted_main_count": deleted_main, 
                "deleted_cred_count": deleted_cred
            }
        except Exception as e:
            db.rollback()
            cred_db.rollback()
            return {"status": "error", "detail": str(e)}
    
    return app


app = create_app()



