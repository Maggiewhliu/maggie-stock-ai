# src/cache.py (增強版本)
import os, json, time, pathlib, contextlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    import redis
except Exception:
    redis=None

REDIS_URL = os.getenv('REDIS_URL')
FILECACHE_DIR = os.path.abspath(os.getenv('FILECACHE_DIR', 'data/filecache'))
pathlib.Path(FILECACHE_DIR).mkdir(parents=True, exist_ok=True)

def _r():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True) if (REDIS_URL and redis) else None

def get_json(key: str) -> Optional[Dict[str,Any]]:
    r = _r()
    if r:
        v = r.get(key)
        return json.loads(v) if v else None
    p = pathlib.Path(FILECACHE_DIR)/(key.replace(':','_')+'.json')
    if p.exists():
        data=json.loads(p.read_text('utf-8'))
        if data.get('_file_expires_at') and time.time()>data['_file_expires_at']:
            return None
        return data
    return None

def set_json(key: str, payload: Dict[str,Any], ttl: int=300):
    data = json.dumps(payload, ensure_ascii=False)
    r=_r()
    if r:
        r.set(key, data, ex=ttl); return
    payload2=dict(payload); payload2['_file_expires_at']=time.time()+ttl
    p = pathlib.Path(FILECACHE_DIR)/(key.replace(':','_')+'.json')
    p.write_text(json.dumps(payload2, ensure_ascii=False), 'utf-8')

@contextlib.contextmanager
def lock(key: str, ttl: int=30):
    r=_r(); lkey=f'{key}.lock'
    if not r:
        yield; return
    ok=r.set(lkey,'1',nx=True,ex=ttl)
    try:
        yield
    finally:
        if ok:
            try: r.delete(lkey)
            except: pass

# 新增：CacheManager 類，提供高級快取功能
class CacheManager:
    """高級快取管理器，專為股票機器人設計"""
    
    def __init__(self):
        self.default_ttl = {
            'stock_data': 300,      # 股票數據 5分鐘
            'options_chain': 600,   # 期權鏈 10分鐘
            'ipo_data': 3600,       # IPO數據 1小時
            'analysis_result': 300,  # 分析結果 5分鐘
            'user_limits': 86400,   # 用戶限制 24小時
        }
        
        logger.info(f"快取管理器初始化 - 使用 {'Redis' if _r() else '文件快取'}")
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取數據"""
        try:
            return get_json(key)
        except Exception as e:
            logger.error(f"獲取快取失敗 {key}: {str(e)}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """設置快取數據"""
        try:
            if ttl is None:
                # 根據 key 前綴自動設置 TTL
                for prefix, default_ttl in self.default_ttl.items():
                    if key.startswith(prefix):
                        ttl = default_ttl
                        break
                else:
                    ttl = 300  # 預設 5分鐘
            
            set_json(key, data, ttl)
            logger.debug(f"快取設置成功 {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"設置快取失敗 {key}: {str(e)}")
            return False
    
    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取股票數據快取"""
        return self.get(f"stock_data_{symbol}")
    
    def set_stock_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """設置股票數據快取"""
        return self.set(f"stock_data_{symbol}", data, self.default_ttl['stock_data'])
    
    def get_analysis_result(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取分析結果快取"""
        return self.get(f"analysis_result_{symbol}")
    
    def set_analysis_result(self, symbol: str, result: Dict[str, Any]) -> bool:
        """設置分析結果快取"""
        return self.set(f"analysis_result_{symbol}", result, self.default_ttl['analysis_result'])
    
    def get_user_limits(self, user_id: int, date: str) -> Optional[Dict[str, Any]]:
        """獲取用戶限制快取"""
        return self.get(f"user_limits_{user_id}_{date}")
    
    def set_user_limits(self, user_id: int, date: str, limits: Dict[str, Any]) -> bool:
        """設置用戶限制快取"""
        return self.set(f"user_limits_{user_id}_{date}", limits, self.default_ttl['user_limits'])
    
    def get_ipo_data(self) -> Optional[List[Dict[str, Any]]]:
        """獲取 IPO 數據快取"""
        return self.get("ipo_data")
    
    def set_ipo_data(self, data: List[Dict[str, Any]]) -> bool:
        """設置 IPO 數據快取"""
        return self.set("ipo_data", data, self.default_ttl['ipo_data'])
    
    def invalidate_stock(self, symbol: str) -> bool:
        """清除特定股票的所有快取"""
        try:
            keys_to_clear = [
                f"stock_data_{symbol}",
                f"analysis_result_{symbol}",
                f"options_chain_{symbol}"
            ]
            
            success_count = 0
            for key in keys_to_clear:
                try:
                    r = _r()
                    if r:
                        r.delete(key)
                    else:
                        # 文件快取清除
                        file_path = pathlib.Path(FILECACHE_DIR) / (key.replace(':', '_') + '.json')
                        if file_path.exists():
                            file_path.unlink()
                    success_count += 1
                except Exception as e:
                    logger.warning(f"清除快取失敗 {key}: {str(e)}")
            
            logger.info(f"清除 {symbol} 快取: {success_count}/{len(keys_to_clear)} 成功")
            return success_count == len(keys_to_clear)
            
        except Exception as e:
            logger.error(f"清除股票快取失敗 {symbol}: {str(e)}")
            return False
    
    def clear_expired_cache(self) -> int:
        """清除過期的文件快取（僅文件快取需要）"""
        if _r():
            return 0  # Redis 自動處理過期
        
        try:
            cleared_count = 0
            cache_dir = pathlib.Path(FILECACHE_DIR)
            
            for cache_file in cache_dir.glob("*.json"):
                try:
                    data = json.loads(cache_file.read_text('utf-8'))
                    if data.get('_file_expires_at') and time.time() > data['_file_expires_at']:
                        cache_file.unlink()
                        cleared_count += 1
                except Exception as e:
                    logger.warning(f"清除過期快取失敗 {cache_file}: {str(e)}")
            
            if cleared_count > 0:
                logger.info(f"清除了 {cleared_count} 個過期快取文件")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"清除過期快取失敗: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計信息"""
        try:
            r = _r()
            if r:
                # Redis 統計
                info = r.info()
                return {
                    'type': 'Redis',
                    'connected': True,
                    'memory_used': info.get('used_memory_human', 'N/A'),
                    'keys_count': r.dbsize(),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                }
            else:
                # 文件快取統計
                cache_dir = pathlib.Path(FILECACHE_DIR)
                cache_files = list(cache_dir.glob("*.json"))
                total_size = sum(f.stat().st_size for f in cache_files)
                
                return {
                    'type': '文件快取',
                    'connected': True,
                    'cache_dir': str(cache_dir),
                    'files_count': len(cache_files),
                    'total_size_mb': round(total_size / 1024 / 1024, 2),
                }
                
        except Exception as e:
            logger.error(f"獲取快取統計失敗: {str(e)}")
            return {
                'type': '未知',
                'connected': False,
                'error': str(e)
            }
    
    def health_check(self) -> bool:
        """快取健康檢查"""
        try:
            test_key = "health_check"
            test_data = {"timestamp": time.time()}
            
            # 寫入測試
            if not self.set(test_key, test_data, 60):
                return False
            
            # 讀取測試
            result = self.get(test_key)
            if not result or result.get("timestamp") != test_data["timestamp"]:
                return False
            
            logger.info("快取健康檢查通過")
            return True
            
        except Exception as e:
            logger.error(f"快取健康檢查失敗: {str(e)}")
            return False

# 全局快取管理器實例
cache_manager = CacheManager()

# 向後兼容的函數
def get_cached_data(key: str) -> Optional[Any]:
    """向後兼容函數"""
    return cache_manager.get(key)

def set_cached_data(key: str, data: Any, ttl: int = 300) -> bool:
    """向後兼容函數"""
    return cache_manager.set(key, data, ttl)
