import { NgFor, NgIf, NgTemplateOutlet } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { DurationConvertPipe } from '../../helpers/duration-pipe';
import { FolderInfo, Media } from '../../models/media';
import { MovieService } from '../../services/movie.service';
import { SeriesService } from '../../services/series.service';

@Component({
  selector: 'app-media-details',
  standalone: true,
  imports: [NgIf, NgFor, FormsModule, DurationConvertPipe, NgTemplateOutlet],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.css'
})
export class MediaDetailsComponent {
  mediaId: number = 0;
  media?: Media = undefined;
  mediaFiles?: FolderInfo = undefined;
  isLoading = true;
  filesLoading = true;
  trailer_url: string = '';
  status = 'Missing';
  mediaService: MovieService | SeriesService = this.seriesService;

  constructor(
    private movieService: MovieService,
    private seriesService: SeriesService,
    private route: ActivatedRoute
  ) { }

  async copyToClipboard(textToCopy: string) {
    if (!navigator.clipboard) {
      // Fallback to the old execCommand() way (for wider browser coverage)
      const tempInput = document.createElement("input");
      tempInput.value = textToCopy;
      document.body.appendChild(tempInput);
      tempInput.select();
      document.execCommand("copy");
      document.body.removeChild(tempInput);
      alert("Copied to clipboard!");
    } else {
      try {
        await navigator.clipboard.writeText(textToCopy);
        alert("Copied to clipboard!");
      } catch (err) {
        alert("Error copying text to clipboard.");
        console.error('Failed to copy: ', err);
      }
    }
    return;
  }

  ngOnInit(): void {
    this.isLoading = true;
    this.filesLoading = true;
    this.route.params.subscribe(params => {
      let type = this.route.snapshot.url[0].path;
      if (type === 'movies') {
        this.mediaService = this.movieService;
      } else {
        this.mediaService = this.seriesService;
      }
      this.mediaId = params['id'];
      this.mediaService.getMediaById(this.mediaId).subscribe((media_res: Media) => {
        this.media = media_res;
        this.trailer_url = media_res.youtube_trailer_id
        this.isLoading = false;
        if (media_res.trailer_exists) {
          this.status = 'Downloaded';
        } else {
          this.status = media_res.monitor ? 'Monitored' : 'Missing';
        }
      });
      this.mediaService.getMediaFiles(this.mediaId).subscribe((files: FolderInfo) => {
        this.mediaFiles = files;
        this.filesLoading = false;
      });
    });
  }

  downloadTrailer() {
    console.log('Downloading trailer');
    this.mediaService.downloadMediaTrailer(this.mediaId, this.trailer_url).subscribe((res: string) => {
      console.log(res);
    });
  }

  monitorSeries() {
    console.log('Toggling Media Monitoring');
    const monitor = !this.media?.monitor;
    this.mediaService.monitorMedia(this.mediaId, monitor).subscribe((res: string) => {
      console.log(res);
      this.media!.monitor = monitor;
    });
  }

  openTrailer(): void {
    if (!this.media?.youtube_trailer_id) {
      return;
    }
    window.open(`https://www.youtube.com/watch?v=${this.media.youtube_trailer_id}`, '_blank');
  }

  deleteTrailer() {
    console.log('Deleting trailer');
    this.mediaService.deleteMediaTrailer(this.mediaId).subscribe((res: string) => {
      console.log(res);
      this.media!.trailer_exists = false;
    });
  }
}
