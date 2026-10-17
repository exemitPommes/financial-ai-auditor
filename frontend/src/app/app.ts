import { Component, inject } from '@angular/core';
import { ButtonComponent, DropzoneComponent } from 'lib-ng-core-components';
import { AuditApiService } from './core/services/audit-api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ButtonComponent, DropzoneComponent],
  templateUrl: './app.html'

})
export class AppComponent {
  private readonly auditApiCore = inject(AuditApiService);

  fileTransfered: File | null = null;

  public fichero(trasferedFile: File): void {
    this.fileTransfered = trasferedFile;
    console.log('Se ha transferido 1 fichero: ', this.fileTransfered);
  }

  public audit(): void {
    if (!this.fileTransfered) {
      console.log('dog, we need a file first');
      return;
    } else {
      this.auditApiCore.auditDocument(this.fileTransfered).subscribe({
        next: (res) => console.log('Resultado del backend:', res),
        error: (err) => console.error('Error HTTP:', err),
      });
    }
  }
}