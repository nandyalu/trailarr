import {isTrailerType, videoTypeLabel} from 'src/app/models/trailerprofile';

/** The banner at the top of the Search section of a profile that does not
 * download a trailer. Every type except Trailer comes from TMDB only, so the
 * search settings do nothing for it (Phase 9, decision 5). Empty for a
 * trailer profile. */
export function nonTrailerSearchNote(videoType: string | null | undefined): string {
  if (isTrailerType(videoType)) return '';
  const label = videoTypeLabel(videoType);
  return (
    `This profile downloads a ${label}. Trailarr takes it from the videos that TMDB lists` +
    ' and does not fall back to a YouTube search. The search settings do not apply.'
  );
}

/** The one-line note that replaces Skip If Plex Has Trailer in the Plex
 * section of a profile that does not download a trailer. Empty for a trailer
 * profile. */
export function nonTrailerPlexNote(videoType: string | null | undefined): string {
  if (isTrailerType(videoType)) return '';
  return `Skip If Plex Has Trailer applies to trailer profiles only. A ${videoTypeLabel(videoType)} downloads even when Plex has a trailer.`;
}
