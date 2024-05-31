import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from AI_match.router import AI_match_router
from Admin.router import admin_router
from Fach.router import fach_router
from Order.router import orders_router
from Profiles.router import profiles_router
from Database.database import DB
from users.PIN.router import pin_router
# 每个模块的路由导入
from users.router import user_router

app = FastAPI()

# CORS中间件设置，增加安全性
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 根据实际需求配置允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 或者只列出你需要的方法，如["GET", "POST"]
    allow_headers=["*"],
)
app.mount("/backend_static", StaticFiles(directory="static"), name="static")

# 初始化 OrderManager 实例
# order_manager = None
@app.on_event("startup")
async def startup_event():
    await DB.initialize('mongodb://admin:Xiangyunduan2024@82.157.124.237:27017/', 'Weg')


@app.on_event("shutdown")
async def shutdown_event():
    await DB.close_mongo_connection()


# 用户模块
app.include_router(user_router, prefix="/api/users", tags=["用户"])
app.include_router(pin_router, prefix="/api/pin", tags=["验证码"])


# 专业相关模块
app.include_router(fach_router, prefix="/api/majors", tags=["专业"])

# AI智能匹配模块
app.include_router(AI_match_router, prefix="/api/ai_matching", tags=["AI匹配"])

# 订单模块
app.include_router(orders_router, prefix="/api/orders", tags=["订单"])

# 后台管理模块
app.include_router(admin_router, prefix="/api/admin", tags=["管理"])

# 个人中心模块
app.include_router(profiles_router, prefix="/api/profiles", tags=["个人中心"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
