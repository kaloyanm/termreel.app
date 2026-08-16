"""RQ worker process entrypoint.

Run with:  uv run python -m app.worker
"""
from rq import Worker

from app.db import init_db
from app.queue import redis_conn, render_queue

if __name__ == "__main__":
    init_db()
    worker = Worker([render_queue], connection=redis_conn)
    worker.work()
