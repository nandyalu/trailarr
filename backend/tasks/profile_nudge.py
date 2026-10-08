"""Tell a person that a profile looks like it downloads extras, not trailers.

Before v0.14.0 the only way to download a featurette or a teaser was a
trailer profile with the word in its search query, its include words or
its folder name. Such a profile still works, and Trailarr does not
change it: a search profile for interviews has no video type to move to,
because TMDB has no interview type. This pass names each such profile
once in the log and suggests the `Video Type` setting (Phase 9,
decision 7). After Phase 11 the nudge becomes an Issue.
"""

from app_logger import ModuleLogger
import database.manager.trailerprofile as trailerprofile_manager
from database.models.video_type import hacky_profile_keyword, is_trailer_type

logger = ModuleLogger("ProfileNudge")


def nudge_extras_profiles() -> int:
    """Log one line for each trailer profile that looks like an extras
    profile.

    Returns:
        int: How many profiles got a nudge.
    """
    count = 0
    for profile in trailerprofile_manager.get_trailerprofiles():
        if not is_trailer_type(profile.video_type):
            continue
        keyword = hacky_profile_keyword(
            profile.search_query,
            profile.file_name,
            profile.folder_name,
            profile.include_words,
        )
        if keyword is None:
            continue
        count += 1
        logger.warning(
            f"The profile '{profile.customfilter.filter_name}' has the word"
            f" '{keyword}' in its settings, and its Video Type is Trailer."
            " Since v0.14.0 a profile can download a teaser, a clip, a"
            " featurette or another extra with the Video Type setting,"
            " from TMDB, or from a search when Search YouTube is on."
            " Trailarr did not change this profile. See the profiles"
            " documentation for the steps."
        )
    if count:
        logger.info(
            f"Trailarr found {count} profiles that look like extras"
            " profiles. The lines above name them."
        )
    return count
