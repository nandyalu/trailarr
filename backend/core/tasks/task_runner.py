import asyncio
from datetime import datetime, timedelta, timezone
import inspect
import json
import logging
import multiprocessing
import os
import time
import threading
from typing import Callable, NoReturn

# from app_logger import logger
# logging = logging.getLogger(__name__)
# Honestly, at this point I don't know why logging is working even when done inside sub-processes!


class TaskRunner:
    """TaskRunner class to run tasks in background. \n
    Each task will run in a separate process with a 3 second delay. \n
    This class is a Singleton class. \n
    Usage: \n
    Running a task in background::
        runner = TaskRunner()
        runner.run_task(task, *args)

    Scheduling a task to run at intervals::

        runner = TaskRunner()
        runner.schedule_task(tag, interval, task, *args)
        runner.cancel_task(tag) \n
    """

    _instance = None

    def __init__(self):
        self._tasks: dict[str, multiprocessing.Process] = {}
        self._task_list: dict[str, dict] = self._read_info_from_file()
        self._queue_list: dict[str, dict] = self._read_info_from_file(is_task=False)

    def __new__(cls) -> "TaskRunner":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # def _get_logger(self, main_queue):
    #     """Get a logger to work within a seperate process. \n
    #     Idea from python docs! >Logging to a single file from multiple processes Variant 2 \n
    #     https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes

    #     The idea is that when this class is initiated or called, it will import the queue \
    #     from `backend.logger`, and whenever a `run_task` or `schedule_task` is called, \
    #     it will send that main thread queue to the new process, which will be added to \
    #     the logger instance inside the process, so that all of the logs will then be \
    #     handled by the main process queue.\n
    #     """
    #     # import logging
    #     # import logging.handlers

    #     # new_logger = logging.getLogger()
    #     # new_logger.setLevel(logging.INFO)
    #     # new_logger.addHandler(logging.handlers.QueueHandler(main_queue))

    #     return logger

    def _run_task_in_process(
        self,
        task: Callable,
        task_args: tuple = (),
        delay: int = 0,
        timeout: int = 0,
    ) -> None:
        """Runs given task in a separate process. \n
        If the task is an async task, it will run in a separate event loop. \n
        Will not return until the task is finished or timeout is reached. \n
        Args:
            task (Callable): The task to run in background.
            task_args (tuple) [optional]: The arguments to pass to the task, if any.
            delay (int, >3) [optional]: The delay in seconds before starting the task.
            timeout (int, >10) [optional]: The timeout in seconds after which \
                to terminate the task. Task will run until finished if not specified. \n
        Returns:
            None
        Note:

            -->> This is an internal method, do not call directly! <<--\n
            -->> Use `run_task` or `schedule_task` to run tasks in background! <<--\n
            -->> This is a blocking method, will not return until task is finished or timeout! <<--
        """

        def run_async() -> None:
            """Run the async task in a separate event loop."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(task(*task_args))
            new_loop.close()
            return

        def save_queue_info(terminated=False):
            """Save Queue info to file."""
            _end_time = datetime.now(timezone.utc)
            # Save Queue details to file
            self._read_info_from_file(is_task=False)
            if terminated:
                self._queue_list[f"{current_pid}"]["status"] = "Terminated"
            else:
                self._queue_list[f"{current_pid}"]["status"] = "Completed"
            self._queue_list[f"{current_pid}"]["end"] = f"{_end_time}"
            _duration = _end_time - _start
            self._queue_list[f"{current_pid}"]["duration"] = f"{_duration}"
            self._write_info_to_file(is_task=False)
            return

        # Save Queue details to file
        current_pid = multiprocessing.current_process().pid
        if not current_pid:
            logging.info("TaskRunner: Unable to get current Mprocess ID!")
            current_pid = os.getpid()
        self._read_info_from_file(is_task=False)
        self._queue_list[f"{current_pid}"] = {
            "name": task.__name__.replace("_", " ").strip().title(),
            "status": "Queued",
            "queued": f"{datetime.now(timezone.utc)}",
            "start": None,
            "end": None,
            "duration": 0,
        }
        self._write_info_to_file(is_task=False)
        # Start the task in a new thread with a minimum 3 second delay
        delay = max(3, delay)
        time.sleep(delay)
        logging.info(f"TaskRunner: '{task.__name__}' started running in background")
        _start = datetime.now(timezone.utc)
        self._read_info_from_file(is_task=False)
        self._queue_list[f"{current_pid}"]["status"] = "Running"
        self._queue_list[f"{current_pid}"]["start"] = f"{_start}"
        self._write_info_to_file(is_task=False)

        # If the provided task is an async task, run in an event loop
        if inspect.iscoroutinefunction(task):
            logging.info(
                f"TaskRunner: '{task.__name__}' is an async task, will run in an event loop!"
            )
            task_process = multiprocessing.Process(target=run_async)
        else:  # Normal task, run directly in subprocess
            task_process = multiprocessing.Process(target=task, args=task_args)
        task_process.start()

        # Check if a timeout is specified, minimum 10 seconds
        timeout = max(9, timeout)
        if timeout == 9:
            # No timeout, Wait for the task to finish
            task_process.join()
            _time_took = datetime.now(timezone.utc) - _start
            logging.info(f"TaskRunner: '{task.__name__}' run finished in {_time_took}")
            save_queue_info()
            return

        # Timeout specified, create a thread to terminate the task after timeout
        timeout_thread = threading.Thread(target=time.sleep, args=(timeout,))
        timeout_thread.start()
        # Wait until the task or timeout to finish
        while task_process.is_alive() and timeout_thread.is_alive():
            time.sleep(1)  # ?Change to 1 to make timeout even precise!
        # If task is finished, return
        if not task_process.is_alive():
            _time_took = datetime.now(timezone.utc) - _start
            logging.info(f"TaskRunner: '{task.__name__}' run finished in {_time_took}")
            save_queue_info()
            return
        # If timeout is reached, terminate the task
        if task_process.is_alive():
            logging.warning(
                f"TaskRunner: '{task.__name__}' Timeout reached, "
                "Task is still running, terminating it now!"
            )
            task_process.terminate()
            _time_took = datetime.now(timezone.utc) - _start
            logging.info(
                f"TaskRunner: '{task.__name__}' run terminated after {_time_took}"
            )
            save_queue_info(terminated=True)
        return

    def run_task(
        self,
        task: Callable,
        *,
        task_args: tuple = (),
        delay: int = 0,
        timeout: int = 0,
    ) -> None:
        """Run a task in background. Only runs once! \n
        Creates a new process to run the task. \n
        Returns immediately after starting the task. \n
        Args:
            task (Callable): The task to run in background.
            task_args (tuple): The arguments to pass to the task, if any.
            delay (int, >3) [optional]: The delay in seconds before starting the task.
            timeout (int, >10) [optional]: The timeout in seconds after which \
                to terminate the task. Task will run until finished if not specified. \n
        Returns:
            None"""
        process = multiprocessing.Process(
            target=self._run_task_in_process, args=(task, task_args, delay, timeout)
        )
        process.start()

    def _create_schedule_task(
        self,
        interval: int,
        task: Callable,
        task_args: tuple = (),
        delay: int = 0,
        timeout: int = 0,
    ) -> NoReturn:
        """Create a task that runs at intervals. Runs forever or until cancelled or timed out. \n
        This function is called in a separate process. \n
        Args:
            interval (int): The interval in seconds to run the task.
            task (Callable): The task to run in background.
            task_args (Any): The arguments to pass to the task, if any.
            delay (int, >3) [optional]: The delay in seconds before starting the task.
            timeout (int, >10) [optional]: The timeout in seconds after which \
                to terminate the task. Task will run until finished if not specified. \n
        Returns:
            NoReturn"""
        current_pid = multiprocessing.current_process().pid
        if not current_pid:
            logging.info("TaskRunner: Unable to get current Mprocess ID!")
            current_pid = os.getpid()
        self._read_info_from_file()
        self._task_list[f"{current_pid}"] = {
            "name": task.__name__.replace("_", " ").strip().title(),
            "interval": interval,
            "last_run_status": "Not Run Yet",
            "last_run_start": None,
            "last_run_duration": 0,
            "next_run": f"{datetime.now(timezone.utc) + timedelta(seconds=delay)}",
        }
        self._write_info_to_file()
        if delay > 3:
            time.sleep(delay)
        while True:
            _start_time = datetime.now(timezone.utc)
            _next_run = _start_time + timedelta(seconds=interval)
            _next_run = f"{_next_run}"
            self._read_info_from_file()
            self._task_list[f"{current_pid}"]["last_run_start"] = f"{_start_time}"
            self._task_list[f"{current_pid}"]["last_run_status"] = "Running"
            self._task_list[f"{current_pid}"]["next_run"] = _next_run
            self._write_info_to_file()
            self._run_task_in_process(task, task_args, delay=0, timeout=timeout)
            _duration = datetime.now(timezone.utc) - _start_time
            logging.info(
                f"TaskRunner: '{task.__name__}' Next run in {interval} seconds"
            )
            self._read_info_from_file()
            _next_run = datetime.now(timezone.utc) + timedelta(seconds=interval)
            _next_run = f"{_next_run}"
            self._task_list[f"{current_pid}"]["last_run_status"] = "Completed"
            self._task_list[f"{current_pid}"]["last_run_duration"] = f"{_duration}"
            self._task_list[f"{current_pid}"]["next_run"] = _next_run
            self._write_info_to_file()
            time.sleep(interval)

    def schedule_task(
        self,
        tag: str,
        interval: int,
        task: Callable,
        *,
        task_args: tuple = (),
        delay: int = 0,
        timeout: int = 0,
    ) -> None:
        """Schedule a task to run at intervals. Runs forever or until cancelled! \n
        Creates a new process to run the task. \n
        Returns immediately after starting the task. \n
        `tag` should be unique for each task, otherwise task will NOT be scheduled! \n
        `tag` can be later used to cancel future runs of the task. \n
        Args:
            tag (str): A [unique] tag to identify the task.
            interval (int): The interval in seconds to run the task.
            task (Callable): The task to run in background.
            task_args (tuple): The arguments to pass to the task, if any.
            delay (int, >3) [optional]: The delay in seconds before starting the task.
            timeout (int, >10) [optional]: The timeout in seconds after which \
                to terminate the task. Task will run until finished if not specified. \
                Timeout is applied to every run of the task. \n
        Returns:
            None"""
        if tag in self._tasks:
            logging.error(
                f"TaskRunner: Task with tag {tag} already exists, {task.__name__} not scheduled!"
            )
            return
        logging.info(
            f"TaskRunner: '{task.__name__}' scheduled to run every {interval} seconds"
        )
        process = multiprocessing.Process(
            target=self._create_schedule_task,
            args=(interval, task, task_args, delay, timeout),
        )
        process.start()
        self._tasks[tag] = process

    def cancel_task(self, tag: str) -> bool:
        """Cancel a scheduled task using the `tag`. \n
        Terminates the task process. \n
        Needs to be `awaited`, as it waits for task to close. \n
        Args:
            tag (str): The tag of the task to cancel. \n
        Returns:
            bool: A flag indicating if task was cancelled!\n"""
        if tag not in self._tasks:
            logging.info(
                f"TaskRunner: Task with tag: '{tag}' not found! Cannot cancel!"
            )
            return False
        logging.info(f"TaskRunner: '{tag}' Cancelling task with tag")
        process = self._tasks[tag]
        logging.debug(f"TaskRunner: '{tag}' Task: sending SIGTERM to terminate it!")
        process.terminate()
        if process.is_alive():
            logging.debug(
                f"TaskRunner: '{tag}' Task is still running, will check again in a few seconds"
            )
        count = 6
        while process.is_alive() and count > 0:
            time.sleep(1)
            count -= 1

        if process.is_alive():
            logging.debug(
                f"TaskRunner: '{tag}' Task is still running, sending SIGKILL to kill it!"
            )
            process.kill()
        if process.is_alive():
            logging.error(
                f"TaskRunner: '{tag}' Task is still running, unable to cancel it!"
            )
            return False
        logging.info(f"TaskRunner: '{tag}' Task cancelled successfully!")
        del self._tasks[tag]
        return True

    def _write_info_to_file(self, is_task=True) -> None:
        """Writes task information to a JSON file."""
        if is_task:
            _file = "task_info.json"
            _list = self._task_list
        else:
            _file = "queue_info.json"
            _list = self._queue_list
            # Keep only last 10 items
            if len(_list) > 10:
                _list = dict(list(_list.items())[-10:])
        # Wait until the lock file is removed
        while os.path.exists(f"{_file}.lock"):
            time.sleep(1)
        # Create a lock file to prevent multiple reads/writes
        with open(f"{_file}.lock", "w") as f:
            f.write("lock")
        with open(_file, "w") as f:
            json.dump(_list, f, indent=4)
        # Remove the lock file
        if os.path.exists(f"{_file}.lock"):
            os.remove(f"{_file}.lock")
            if os.path.exists(f"{_file}.lock"):
                logging.info("TaskRunner: Unable to remove lock file!")

    def _read_info_from_file(self, is_task=True) -> dict:
        """Reads task information from a JSON file (or empty dict if not found)."""
        if is_task:
            _file = "task_info.json"
        else:
            _file = "queue_info.json"
        try:
            # Wait until the lock file is removed
            while os.path.exists(f"{_file}.lock"):
                time.sleep(1)
            # Create a lock file to prevent multiple reads/writes
            with open(f"{_file}.lock", "w") as f:
                f.write("lock")
            with open(_file, "r") as f:
                res = json.load(f)
                if is_task:
                    self._task_list = res
                else:
                    self._queue_list = res
            # Remove the lock file
            if os.path.exists(f"{_file}.lock"):
                os.remove(f"{_file}.lock")
                if os.path.exists(f"{_file}.lock"):
                    logging.info("TaskRunner: Unable to remove lock file!")
            return res
        except FileNotFoundError:
            os.remove(f"{_file}.lock")
            return {}
        except Exception:
            os.remove(f"{_file}.lock")
            return {}

    def cleanup_tasks(self) -> None:
        """Cleanup tasks and queues."""
        files = [
            "task_info.json",
            "queue_info.json",
            "task_info.json.lock",
            "queue_info.json.lock",
        ]
        for file in files:
            if os.path.exists(file):
                os.remove(file)
        self._tasks = {}
        self._task_list = {}
        self._queue_list = {}
        return
