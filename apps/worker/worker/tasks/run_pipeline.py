import asyncio
import logging
from typing import List

from worker.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


def run_pipeline_task(run_id: str, topics: List[str]):
    """
    RQ task to run the full pipeline
    
    Args:
        run_id: The run ID
        topics: List of topics to search for
    """
    logger.info(f"Starting pipeline task for run {run_id}")
    
    try:
        runner = PipelineRunner(run_id, topics)
        asyncio.run(runner.execute())
        logger.info(f"Pipeline task completed for run {run_id}")
    except Exception as e:
        logger.error(f"Pipeline task failed for run {run_id}: {e}")
        raise
