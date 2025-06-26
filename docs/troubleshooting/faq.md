## Does this work with Plex, Emby, Jellyfin?
Yes, this works with Plex, Emby, and Jellyfin. Trailarr downloads trailers for Movies and Series, and saves them in their respective media folder. Plex, Emby, and Jellyfin can pick up these trailers and display them along with the Movie or Series.


## How can I watch the trailers?
You can watch the trailers in the Movie or Series details in Plex, Emby, or Jellyfin. Trailers downloaded by Trailarr are saved in the same folder as the Movie or Series, for Plex, Emby, and Jellyfin to recognize and display them along with the Movie or Series.


## Can I use Tailarr without Radarr or Sonarr?
No, Trailarr relies on data from Radarr and Sonarr to monitor Movies and Series. You need to have Radarr and/or Sonarr setup and connected to Trailarr to download trailers.


## Can I use Trailarr with multiple Radarr or Sonarr instances?
Yes, you can connect multiple Radarr and Sonarr instances to Trailarr. Trailarr will monitor Movies and Series from all connected Radarr and Sonarr instances and download trailers for them.


## Trailarr is not downloading trailers for some Movies or Series. Why?
Trailarr monitors the Movies and Series from connected Radarr and Sonarr instances based on the Monitor Type set. Make sure you have correct Monitor Types set for the Movies and Series you want Trailarr to download trailers for.

More info about [Monitor Types here](../setup/connections.md#monitor-types).


## How can I change the Monitor Type for a Movie or Series?
You can open up a Movie or Series details in Trailarr and click on the `Monitor` button to change the Monitor Type for that Movie or Series. Trailarr will download a trailer for that in the next schedule.


## Trailarr downloaded an incorrect trailer for a Movie or Series. How can I fix it?
Movies: Radarr provides a youtube trailer link for Movies that it gets from TMDB. Trailarr will attempt to download that trailer first, if that fails or not set, Trailarr downloads trailers based on the Movie title and year. If Trailarr downloaded an incorrect trailer, you can manually search on youtube and update the youtube trailer link in Movie details page in Trailarr.

Series: Sonarr does not provide a youtube trailer link for Series. Trailarr will search for the Series trailer based on the Series title and year. If Trailarr downloaded an incorrect trailer, you can manually search on youtube and update the youtube trailer link in Series details page in Trailarr.


!!! info
    Trailarr will not delete the trailer that was already downloaded. You have to manually click on `Delete` button to delete the trailer.

## Trailarr not downloading the specified youtube video, but downloading a different video. Why?
Trailarr uses yt-dlp to download youtube videos. Some videos have restrictions on downloading, and yt-dlp might not be able to download them. The solution is to supply a cookie file (`Yt-dlp Cookies Path`) in `Settings > Trailer > Advanced` to download restricted videos. See [Settings](../setup/settings.md) for more info.


## Can I download multiple trailers for a Movie or Series?
Trailarr will not download multiple trailers for same Movie or Series automatically. You can manually update the youtube trailer link and click `Download` to download another trailer. Trailarr will download and save the new trailer in the Movie or Series folder along with the old trailer.

## App is stuck on "Downloading" status for a long time. What should I do?
Trailarr downloads the best available video in the selected resolution, and then use ffmpeg to convert to selected audio and video codecs. This process can take some time based on the video size and your server hardware. 

The amount of time it takes to convert a 3 minute video usually takes around 1-2 minutes on latest hardware (like i3-12100 or Ryzen 5 5600X). 

If you are using a Raspberry Pi or a low powered server, it might take longer to convert the video. You can check the (debug) logs to see the progress of the conversion process.

!!! info
    YouTube trailers are usually in `vp9` video codec and `opus` audio codec, so setting theses codecs in Trailarr settings will prevent conversion. Most modern players support these codecs, so you can use these codecs in Trailarr settings to speed up the process.