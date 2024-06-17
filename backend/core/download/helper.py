from core.base.database.models.helpers import MediaTrailer
from core.download.trailer import download_trailer
from core.tasks.task_runner import TaskRunner


mediat = MediaTrailer(
    id=142,
    title="Baahubali",
    year=2024,
    yt_id="",
    folder_path="/tmp/Baahubali/",
)

runner = TaskRunner()
runner.run_task(download_trailer, task_args=(mediat, True, False))
# download_trailer(mediat, trailer_folder=True, is_movie=False)
