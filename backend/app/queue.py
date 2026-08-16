from redis import Redis
from rq import Queue

from app.config import REDIS_URL, RENDER_QUEUE_NAME

redis_conn = Redis.from_url(REDIS_URL)
render_queue = Queue(RENDER_QUEUE_NAME, connection=redis_conn)
