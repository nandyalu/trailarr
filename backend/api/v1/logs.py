import collections
import logging
import aiofiles
from aiofiles import os
from fastapi import APIRouter


logs_router = APIRouter(prefix="/logs", tags=["Logs"])


@logs_router.get("/")
async def get_logs(page: int = 1, limit: int = 100) -> list[str]:
    # Read logs from file and send it back
    logs_dir = "/data/logs"
    # logs: list[str] = []
    logs: collections.deque = collections.deque(maxlen=limit)
    if not await os.path.exists(logs_dir):
        logging.info("Logs directory does not exist")
        return ["No logs found"]
    for log_file in await os.listdir(logs_dir):
        if log_file.endswith(".log"):
            # logging.info(f"Reading logs from {log_file}")
            # with open(f"{logs_dir}/{log_file}", "r") as f:
            #     for line in f:
            #         logs.append(line)
            file = await aiofiles.open(f"{logs_dir}/{log_file}", mode="r")
            async for line in file:
                logs.append(line)

    logs.reverse()
    return list(logs)
    # logs_filtered = logs[(page - 1) * limit : page * limit]
    # return logs_filtered
