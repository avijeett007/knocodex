#!/usr/bin/env python3
"""
Redis utilities for Knocodex
"""

import os
import subprocess
import logging
import time
import platform
from redis import Redis
from rq import Queue

logger = logging.getLogger("knocodex.utils.redis_utils")

def check_redis_running():
    """Check if Redis server is running"""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except Exception as e:
        logger.error(f"Failed to check Redis server: {e}")
        return False

def start_redis():
    """Start Redis server"""
    if check_redis_running():
        logger.info("Redis server is already running")
        return True
    
    try:
        if platform.system() == "Darwin":
            subprocess.run(
                ["brew", "services", "start", "redis"],
                check=True,
            )
            logger.info("Redis server started successfully")
            return True
        else:
            logger.error("Automatic starting of Redis is only supported on macOS")
            logger.info("Please start Redis manually")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Redis server: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to start Redis server: {e}")
        return False

def stop_redis():
    """Stop Redis server"""
    if not check_redis_running():
        logger.info("Redis server is not running")
        return True
    
    try:
        if platform.system() == "Darwin":
            subprocess.run(
                ["brew", "services", "stop", "redis"],
                check=True,
            )
            logger.info("Redis server stopped successfully")
            return True
        else:
            logger.error("Automatic stopping of Redis is only supported on macOS")
            logger.info("Please stop Redis manually")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop Redis server: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to stop Redis server: {e}")
        return False

def get_redis_queue(redis_url="redis://localhost:6379", queue_name="knocodex"):
    """Get a Redis queue"""
    try:
        redis_conn = Redis.from_url(redis_url)
        queue = Queue(queue_name, connection=redis_conn)
        return queue
    except Exception as e:
        logger.error(f"Failed to get Redis queue: {e}")
        return None

def enqueue_task(queue, func, *args, **kwargs):
    """Enqueue a task in the Redis queue"""
    try:
        job = queue.enqueue(
            func,
            *args,
            **kwargs,
            job_timeout="2h",  # Long timeout for complex tasks
            result_ttl=86400,  # Keep results for 24 hours
            ttl=86400,         # Job can wait in queue for up to 24 hours
        )
        logger.info(f"Enqueued job with ID: {job.id}")
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e}")
        return None
