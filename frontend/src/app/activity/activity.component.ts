import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {RouterLink, RouterLinkActive, RouterOutlet} from '@angular/router';
import {RouteEvents, RouteIssues, RouteLogs} from 'src/routing';
import {IssueService} from '../services/issue.service';

@Component({
  selector: 'app-activity',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './activity.component.html',
  styleUrl: './activity.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ActivityComponent {
  protected readonly RouteIssues = RouteIssues;
  protected readonly RouteEvents = RouteEvents;
  protected readonly RouteLogs = RouteLogs;

  private readonly issueService = inject(IssueService);
  protected readonly issueCount = this.issueService.openCount;
}
