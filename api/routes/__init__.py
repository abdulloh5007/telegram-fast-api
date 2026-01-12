from .sessions import router as sessions_router
from .user import router as user_router
from .dialogs import router as dialogs_router
from .messages import router as messages_router
from .photos import router as photos_router
from .backup import router as backup_router
from .export import router as export_router
from .admin import router as admin_router
from .web_login import router as web_login_router
from .qr_login import router as qr_login_router

routers = [sessions_router, user_router, dialogs_router, messages_router, photos_router, backup_router, export_router, admin_router, web_login_router, qr_login_router]



