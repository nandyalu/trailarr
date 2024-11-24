import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Media } from '../models/media';
import { MediaService } from '../services/media.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {
  media_list: Media[] = [];
  isLoading = true;

  constructor(
    private mediaService: MediaService,
  ) { }

  ngOnInit(): void {
    this.isLoading = true;
    this.mediaService.getRecentlyDownloaded(null).subscribe((media_list: Media[]) => {
      this.media_list = [];
      this.isLoading = false;
      media_list.forEach((media, index) => {
        setTimeout(() => {
          this.media_list.push(media);
        }, index * 20); // 20 milliseconds delay for each item
      });
    });
  }
}
