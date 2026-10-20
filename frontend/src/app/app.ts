import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  ButtonComponent, 
  DropzoneComponent,
  BadgeComponent,
  CardComponent,
  SkeletonComponent,
  AlertComponent,
  SplitterComponent, 
} from 'lib-ng-core-components';
import { DocumentViewerComponent } from './features/audit/components/document-viewer/document-viewer.component';
import { AuditSummaryComponent } from './features/audit/components/audit-summary/audit-summary.component';
import { AuditApiService } from './core/services/audit-api.service';
import { AuditResult } from './core/models/audit.models';
import { VarianteAuditoria } from './core/models/audit.types';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    AlertComponent,
    BadgeComponent,
    ButtonComponent, 
    CardComponent,
    DropzoneComponent,
    SkeletonComponent,
    SplitterComponent,
    DocumentViewerComponent,
    AuditSummaryComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class AppComponent {
  private readonly auditApi = inject(AuditApiService);

  selectedFile = signal<File | null>(null);
  previewUrl = signal<string | null>(null);
  isLoading = signal<boolean>(false);
  auditResult = signal<AuditResult | null>(null);
  dropzoneErrorMessage = signal<string | null>(null);
  auditErrorMessage = signal<string | null>(null);
  hoveredItemIndex = signal<number | null>(null);

  hasFile = computed(() => this.selectedFile() !== null);
  hasAuditFile = computed(() => this.auditResult() !== null);

  statusVariant = computed<VarianteAuditoria>(() => {
    const auditoria = this.auditResult();
    if (!auditoria) {
      return 'warning';
    }
    return auditoria.estado === 'AUTO_APPROVED' ? 'success' : 'danger';
  });

  public onUploadFile(file: File): void {
    this.selectedFile.set(file);
    console.log('Se ha transferido 1 fichero: ', this.selectedFile());
    this.auditResult.set(null);
    this.auditErrorMessage.set(null);
    this.dropzoneErrorMessage.set(null);

    if (file.type.startsWith('image/')) {
      this.previewUrl.set(URL.createObjectURL(file));
    } else {
      this.previewUrl.set(null);
    }
  }

  public onRunAudit(): void {
    const file = this.selectedFile();
    if (!file) {
      console.log('dog, we need a file first');
      return;
    } else {
      this.isLoading.set(true);
      this.auditErrorMessage.set(null);
      this.auditApi.auditDocument(file).subscribe({
        next: (result) => {
          this.auditResult.set(result);
          if (result.preview_image_base64) {
            this.previewUrl.set(result.preview_image_base64);
          }
          this.isLoading.set(false);
        },
        error: (error) => {
          console.error('Error al auditar:', error)
          this.auditErrorMessage.set('Error al conectar con el servidor de auditoría.');
          this.isLoading.set(false);
        }
      });
    }
  }

  onReset(): void {
    this.selectedFile.set(null);
    this.previewUrl.set(null);
    this.auditResult.set(null);
    this.auditErrorMessage.set(null);
    this.dropzoneErrorMessage.set(null);
  }
  
  displayError(alerta: string): void {
    this.dropzoneErrorMessage.set(alerta);
  }
}