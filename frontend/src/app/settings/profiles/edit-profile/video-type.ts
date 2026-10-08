import {isTrailerType, videoTypeLabel} from 'src/app/models/trailerprofile';

/** The banner at the top of the Search section. Says where the videos of
 * the profile come from, given its type and its Search YouTube setting
 * (Phase 9, decision 5 as amended): with the search off, known videos only;
 * with the search on for a type other than Trailer, a warning that a search
 * result is not checked against TMDB. Empty for a trailer profile with the
 * search on, which is the default. */
export function searchNote(videoType: string | null | undefined, searchYoutube: boolean | null | undefined): string {
  const searchOn = searchYoutube !== false;
  const label = videoTypeLabel(videoType);
  if (!searchOn) {
    return (
      `Search YouTube is off. Trailarr takes the ${label} of a media item from its known videos only` +
      ' (the videos TMDB lists, the id from Radarr or Sonarr, and videos you added), and waits for TMDB when none suits this profile.' +
      ' The search settings do not apply.'
    );
  }
  if (isTrailerType(videoType)) return '';
  return (
    `Search YouTube is on for a ${label} profile. A search result is not checked against TMDB,` +
    ' so aim the Search Query and the Include Words at the videos you want, or turn Search YouTube off to take them from TMDB only.'
  );
}

/** The one-line note that replaces Skip If Plex Has Trailer in the Plex
 * section of a profile that does not download a trailer. Empty for a trailer
 * profile. */
export function nonTrailerPlexNote(videoType: string | null | undefined): string {
  if (isTrailerType(videoType)) return '';
  return `Skip If Plex Has Trailer applies to trailer profiles only. A ${videoTypeLabel(videoType)} downloads even when Plex has a trailer.`;
}
