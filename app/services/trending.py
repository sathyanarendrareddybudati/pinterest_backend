import redis
from app.core.config import settings
import datetime

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def record_pin_save(pin_id):
    """
    Record a pin save event using Redis sorted sets.
    pin_id is a UUID or string. Score is the current timestamp.
    """
    try:
        now = datetime.datetime.now().timestamp()
        r.zadd("trending_pins", {str(pin_id): now})
        
        # Remove saves older than 1 hour (3600 seconds)
        one_hour_ago = now - 3600
        r.zremrangebyscore("trending_pins", "-inf", one_hour_ago)
    except Exception as e:
        print(f"Redis save failed: {e}")

def get_trending_pins(limit=10):
    """
    Retrieve trending pins based on recent saves (UUID strings).
    """
    try:
        trending = r.zrevrange("trending_pins", 0, limit - 1)
        return trending
    except Exception as e:
        print(f"Redis get failed: {e}")
        return []