def trailer_cleanup():
    """
    Cleanup failed downloads and remove files older than 7 days.
    """
    pass


# TODO: Create a cleanup task to remove Media that doesn't exist in Arr
# Get data from Arr, get all Media from database and verify if they exist in Arr
# For each media in database, check if it exists in Arr by matching Arr id and txdb_id
# If media doesn't exist in Arr, delete it from database
# This task should run once a day


def cleanup_task():
    """
    Cleanup task to remove Media that doesn't exist in Arr.
    """

    pass
