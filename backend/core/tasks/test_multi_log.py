"""
Created some methods to test the TaskRunner class, and the logging functionality.
Since the TaskRunner class is designed to run tasks in parallel using multiprocessing,
and python's logging is not process-safe, the logging module is configured to use a
multiprocessing queue handler to send log records to the main process, where they are
processed and logged. This is done by calling the config_logging() function from the
app_logger module, which sets up the logging configuration and starts the logging.
For this to work from multiprocessing processes, the queue must be passed to
the child processes, and child process need to write it's log records to the queue.

However, it's working without doing any of that, just by using the multiprocessing queue,
without actually passing it to the child processes!!!
"""

import asyncio
import logging
import time

from backend.app_logger import config_logging
from backend.core.tasks.task_runner import TaskRunner


def reg_task1():
    n = 10
    logging.info("Task 1: Starting!")
    while n > 0:
        logging.info(f"Task 1: {n} seconds remaining")
        n -= 1
        time.sleep(1)
    logging.info("Task 1: Completed!")


async def reg_task2():
    n = 12
    logging.info("Task 2: Starting!")
    while n > 0:
        logging.info(f"Task 2: {n} seconds remaining")
        n -= 1
        await asyncio.sleep(1)
    logging.info("Task 2: Completed!")


if __name__ == "__main__":
    config_logging()
    logging.info("Starting tasks")
    runner = TaskRunner()
    runner.run_task(reg_task1)
    runner.run_task(reg_task2)
    runner.run_task(reg_task1)
    runner.schedule_task("reg_task1", 5, reg_task1)
    runner.schedule_task("reg_task2", 8, reg_task2)
    logging.info("All tasks completed!")
