import { Component, input, output } from '@angular/core';
import { BoundingBox, DocumentItem } from 'src/app/core/models/audit.models';

@Component({
  selector: 'document-overlay',
  standalone: true,
  templateUrl: './document-overlay.component.html',
  styleUrl: './document-overlay.component.scss',
})
export class DocumentOverlayComponent {
  readonly items = input<DocumentItem[]>([]);
  readonly totalBox = input<BoundingBox | null>(null);
  readonly hoveredIndex = input<number | null>(null);

  readonly boxHovered = output<number | null>();
}