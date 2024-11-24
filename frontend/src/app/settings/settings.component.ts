import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-settings',
    imports: [RouterLink, RouterLinkActive, RouterOutlet],
    templateUrl: './settings.component.html',
    styleUrl: './settings.component.css'
})
export class SettingsComponent {

}
