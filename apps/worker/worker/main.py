import logging
from redis import Redis
from rq import Worker, Queue, Connection
import sys

from worker.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main worker entry point"""
    logger.info("Starting MicroAppFinder Worker")
    
    redis_conn = Redis.from_url(settings.REDIS_URL)
    
    with Connection(redis_conn):
        worker = Worker(
            [Queue('default'), Queue('high'), Queue('low')],
            connection=redis_conn
        )
        logger.info("Worker listening on queues: default, high, low")
        worker.work()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
        sys.exit(0)
