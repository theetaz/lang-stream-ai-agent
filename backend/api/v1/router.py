from api.v1.auth.routes import router as auth_router
from api.v1.chat.routes import router as chat_router
from api.v1.user.routes import router as user_router
from api.v1.files.routes import router as files_router
from fastapi.routing import APIRouter

# set api router prefixes
api_v1_router = APIRouter(prefix="/api/v1")

# add routers to api router
api_v1_router.include_router(auth_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(files_router)
