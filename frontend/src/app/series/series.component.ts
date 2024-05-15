import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Media } from '../models/media';
import { SeriesService } from '../services/series.service';

@Component({
  selector: 'app-series',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor],
  templateUrl: './series.component.html',
  styleUrl: './series.component.css'
})
export class SeriesComponent {
  title = 'Series';
  all_series: Media[] = [];
  isLoading = true;

  constructor(private seriesService: SeriesService) { }
  
  ngOnInit(): void {
    this.isLoading = true;
    this.seriesService.getSeries().subscribe((series: Media[]) => {
      this.all_series = series;
      this.isLoading = false;
    });
  }
}
