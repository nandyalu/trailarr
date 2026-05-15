import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {Issue} from '../../models/issue';
import {IssueService} from '../../services/issue.service';
import {RouteConnections, RouteSettings} from 'src/routing';

@Component({
  selector: 'app-issues',
  imports: [RouterLink, DatePipe],
  templateUrl: './issues.component.html',
  styleUrl: './issues.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IssuesComponent {
  private readonly issueService = inject(IssueService);

  protected readonly issues = this.issueService.issuesResource.value;
  protected readonly isLoading = this.issueService.issuesResource.isLoading;

  protected readonly connectionIssues = computed(() =>
    this.issues().filter((i) => i.issue_type === 'connection_failed' || i.issue_type === 'token_invalid'),
  );
  protected readonly fileIssues = computed(() =>
    this.issues().filter((i) => i.issue_type === 'file_deleted' || i.issue_type === 'folder_missing'),
  );

  protected readonly RouteSettings = RouteSettings;
  protected readonly RouteConnections = RouteConnections;

  issueIcon(issue: Issue): string {
    switch (issue.issue_type) {
      case 'connection_failed': return 'wifi_off';
      case 'token_invalid': return 'key_off';
      case 'file_deleted': return 'delete_forever';
      case 'folder_missing': return 'folder_off';
      default: return 'warning';
    }
  }

  issueLabel(issue: Issue): string {
    switch (issue.issue_type) {
      case 'connection_failed': return 'Connection Failed';
      case 'token_invalid': return 'Invalid API Token';
      case 'file_deleted': return 'Trailer File Deleted';
      case 'folder_missing': return 'Folder Missing';
      default: return issue.issue_type;
    }
  }

  async dismiss(issue: Issue): Promise<void> {
    await this.issueService.dismissIssue(issue.id);
  }
}
