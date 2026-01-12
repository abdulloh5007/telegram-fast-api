from .commands import router as commands_router
from .auth import router as auth_router
from .twofa import router as twofa_router
from .admin import router as admin_router
from .settings import router as settings_router

routers = [commands_router, auth_router, twofa_router, admin_router, settings_router]

