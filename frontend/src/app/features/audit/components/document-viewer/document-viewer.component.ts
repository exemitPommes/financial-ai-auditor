import { Component, input, output } from '@angular/core';
import { BoundingBox, DocumentItem } from 'src/app/core/models/audit.models';
import { 
  ButtonComponent, 
  DropzoneComponent,
  BadgeComponent,
  CardComponent,
  SkeletonComponent,
  AlertComponent,
  SplitterComponent, 
} from 'lib-ng-core-components';
import { DocumentOverlayComponent } from '../document-overlay/document-overlay.component';

@Component({
    selector: 'document-viewer',
    standalone: true,
    templateUrl: './document-viewer.component.html',
    styleUrl: './document-viewer.component.scss',
    imports: [ButtonComponent, DocumentOverlayComponent]
})
export class DocumentViewerComponent {
    readonly file = input<File | null>(null);
    readonly previewUrl = input<string | null>(null);
    readonly items = input<DocumentItem[]>([]);
    readonly totalBox = input<BoundingBox | null>(null);
    readonly hoveredItemIndex = input<number | null>(null);
    readonly isLoading = input<boolean>(false);
    readonly hasAuditFile = input<boolean>(false);
    
    readonly fileSelected = output<File>();
    readonly reset = output<void>();
    readonly runAudit = output<void>();
    readonly itemHovered = output<number | null>();

}