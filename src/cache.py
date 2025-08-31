import os, json, time, pathlib, contextlib
from typing import Optional, Dict, Any
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
