import {Download, isUnknownVideo} from 'src/app/models/media';

export interface UnknownVideoCounts {
  /** The trailers of the profile that are on disk. */
  total: number;
  /** Those among them whose video nobody knows. */
  unknown: number;
}

/** How many trailers of a profile have an unknown video, out of all its
 * trailers on disk. Shown next to Replace Unknown Videos, so the impact is
 * known before the setting is turned on. Reads the downloads map the
 * library already loads, so it costs no request. */
export function countUnknownVideos(downloads: Iterable<Download[]>, profileId: number | undefined): UnknownVideoCounts {
  const counts: UnknownVideoCounts = {total: 0, unknown: 0};
  if (!profileId) return counts;
  for (const list of downloads) {
    for (const download of list) {
      if (!download.file_exists || download.profile_id !== profileId) continue;
      counts.total++;
      if (isUnknownVideo(download.youtube_id)) counts.unknown++;
    }
  }
  return counts;
}

/** The sentence the setting shows for the counts. */
export function unknownVideosNote({total, unknown}: UnknownVideoCounts): string {
  const n = (value: number) => value.toLocaleString();
  if (total === 0) return 'This profile has no trailers on disk yet.';
  if (unknown === 0) {
    return `None of the ${n(total)} trailers of this profile has an unknown video, so this changes nothing today.`;
  }
  const verb = unknown === 1 ? 'has' : 'have';
  return `${n(unknown)} of ${n(total)} trailers of this profile ${verb} an unknown video. Turn this on, and the upgrade replaces them where TMDB lists a trailer.`;
}
