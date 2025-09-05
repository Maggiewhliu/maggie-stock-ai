import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
import httpx
from telegram import Update
from telegram.ext import Application

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境變數配置（生產環境不要硬寫 Token）
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN 環境變數未設置！")
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

BASE_URL = os.getenv("BASE_URL", "https://maggie-stock-ai.onrender.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"{BASE_URL}/webhook")

# 創建 FastAPI 應用
app = FastAPI(
    title="Maggie's Stock AI Bot",
    description="專業股票分析機器人 API",
    version="1.0.0"
)

# 建立 Telegram Application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# 匯入並註冊 handlers
try:
    from src.bot import register_handlers
    register_handlers(application)
    logger.info("Bot handlers 註冊成功")
except ImportError as e:
    logger.error(f"導入 bot handlers 失敗: {str(e)}")
    raise

# 全局變數追蹤
webhook_status = {
    "is_set": False,
    "url": None,
    "last_update": None
}

stats = {
    "total_updates": 0,
    "successful_updates": 0,
    "failed_updates": 0,
    "start_time": datetime.now()
}

@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("🚀 Maggie's Stock AI Bot 正在啟動...")
    
    # 檢查快取系統
    try:
        from src.cache import cache_manager
        if cache_manager.health_check():
            logger.info("✅ 快取系統健康檢查通過")
        else:
            logger.warning("⚠️ 快取系統健康檢查失敗")
    except Exception as e:
        logger.error(f"❌ 快取系統初始化失敗: {str(e)}")
    
    # 測試 Yahoo Finance 連接
    try:
        from src.provider_yahoo import YahooProvider
        provider = YahooProvider()
        if provider.test_connection():
            logger.info("✅ Yahoo Finance 連接測試通過")
        else:
            logger.warning("⚠️ Yahoo Finance 連接測試失敗")
    except Exception as e:
        logger.error(f"❌ Yahoo Finance 測試失敗: {str(e)}")
    
    logger.info("🎉 Maggie's Stock AI Bot 啟動完成")

@app.get("/")
async def root():
    """根路徑 - 服務狀態"""
    uptime = datetime.now() - stats["start_time"]
    
    return {
        "service": "Maggie's Stock AI Bot",
        "status": "運行中",
        "version": "1.0.0",
        "webhook_url": WEBHOOK_URL,
        "webhook_status": webhook_status,
        "uptime_seconds": uptime.total_seconds(),
        "stats": {
            "total_updates": stats["total_updates"],
            "successful_updates": stats["successful_updates"],
            "failed_updates": stats["failed_updates"],
            "success_rate": f"{(stats['successful_updates']/max(1, stats['total_updates'])*100):.1f}%"
        }
    }

@app.get("/health")
async def health():
    """健康檢查端點"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # 檢查 Telegram Bot
    try:
        bot_info = await application.bot.get_me()
        health_status["services"]["telegram_bot"] = {
            "status": "healthy",
            "bot_name": bot_info.username,
            "bot_id": bot_info.id
        }
    except Exception as e:
        health_status["services"]["telegram_bot"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # 檢查快取系統
    try:
        from src.cache import cache_manager
        cache_stats = cache_manager.get_cache_stats()
        health_status["services"]["cache"] = {
            "status": "healthy" if cache_stats.get("connected") else "unhealthy",
            "type": cache_stats.get("type"),
            "details": cache_stats
        }
    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/set-webhook")
async def set_webhook(url: str = None):
    """設置 Telegram webhook"""
    target = url or WEBHOOK_URL
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                params={"url": target},
            )
            
        result = response.json()
        
        if result.get("ok"):
            webhook_status.update({
                "is_set": True,
                "url": target,
                "last_update": datetime.now().isoformat()
            })
            logger.info(f"✅ Webhook 設置成功: {target}")
        else:
            logger.error(f"❌ Webhook 設置失敗: {result}")
            
        return result
        
    except Exception as e:
        logger.error(f"設置 webhook 時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"設置 webhook 失敗: {str(e)}")

@app.get("/delete-webhook")
async def delete_webhook(drop_pending_updates: bool = True):
    """刪除 Telegram webhook"""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook",
                params={"drop_pending_updates": json.dumps(drop_pending_updates).lower()},
            )
            
        result = response.json()
        
        if result.get("ok"):
            webhook_status.update({
                "is_set": False,
                "url": None,
                "last_update": datetime.now().isoformat()
            })
            logger.info("✅ Webhook 刪除成功")
        else:
            logger.error(f"❌ Webhook 刪除失敗: {result}")
            
        return result
        
    except Exception as e:
        logger.error(f"刪除 webhook 時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除 webhook 失敗: {str(e)}")

@app.get("/webhook-info")
async def get_webhook_info():
    """獲取當前 webhook 資訊"""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取 webhook 資訊失敗: {str(e)}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook 處理端點"""
    stats["total_updates"] += 1
    
    try:
        # 獲取請求數據
        data = await request.json()
        
        # 解析 Telegram Update
        update = Update.de_json(data, application.bot)
        
        if not update:
            stats["failed_updates"] += 1
            logger.warning("收到無效的 Telegram update")
            raise HTTPException(status_code=400, detail="Invalid update")
        
        # 記錄收到的 update
        user_id = None
        message_text = None
        
        if update.message:
            user_id = update.message.from_user.id if update.message.from_user else None
            message_text = update.message.text
        elif update.callback_query:
            user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
            message_text = update.callback_query.data
        
        logger.info(f"收到 update - User: {user_id}, Message: {message_text}")
        
        # 處理 update
        await application.process_update(update)
        
        stats["successful_updates"] += 1
        return {"ok": True}
        
    except json.JSONDecodeError:
        stats["failed_updates"] += 1
        logger.error("無法解析 webhook 請求的 JSON 數據")
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    except Exception as e:
        stats["failed_updates"] += 1
        logger.error(f"處理 webhook 時發生錯誤: {str(e)}")
        # 不拋出異常，避免 Telegram 重複發送
        return {"ok": False, "error": str(e)}

@app.get("/stats")
async def get_stats():
    """獲取服務統計信息"""
    uptime = datetime.now() - stats["start_time"]
    
    # 獲取快取統計
    cache_stats = {}
    try:
        from src.cache import cache_manager
        cache_stats = cache_manager.get_cache_stats()
    except Exception as e:
        cache_stats = {"error": str(e)}
    
    return {
        "uptime": {
            "seconds": uptime.total_seconds(),
            "human_readable": str(uptime)
        },
        "telegram": stats,
        "webhook": webhook_status,
        "cache": cache_stats,
        "environment": {
            "base_url": BASE_URL,
            "webhook_url": WEBHOOK_URL,
            "has_redis": bool(os.getenv('REDIS_URL'))
        }
    }

@app.get("/test")
async def test_functionality():
    """測試核心功能"""
    test_results = {}
    
    # 測試 Yahoo Finance
    try:
        from src.provider_yahoo import YahooProvider
        provider = YahooProvider()
        test_data = await provider.get_stock_data("AAPL")
        test_results["yahoo_finance"] = {
            "status": "success" if test_data else "failed",
            "data": bool(test_data)
        }
    except Exception as e:
        test_results["yahoo_finance"] = {
            "status": "error",
            "error": str(e)
        }
    
    # 測試分析器
    try:
        from src.analyzers_integration import StockAnalyzer
        analyzer = StockAnalyzer()
        test_results["analyzer"] = {
            "status": "success",
            "loaded": True
        }
    except Exception as e:
        test_results["analyzer"] = {
            "status": "error",
            "error": str(e)
        }
    
    return test_results

# 如果直接運行這個文件
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"啟動服務器 - Host: {host}, Port: {port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        log_level="info",
        reload=False  # 生產環境關閉 reload
    )
