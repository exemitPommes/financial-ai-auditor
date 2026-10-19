import { Component, input, output } from '@angular/core';
import { DocumentItem } from 'src/app/core/models/audit.models';

@Component({
    selector: 'audit-table',
    standalone: true,
    templateUrl: './audit-table.component.html',
    styleUrl: './audit-table.component.scss',

})
export class AuditTableComponent {
    readonly items = input<DocumentItem[] | null>(null);
    readonly hoveredItemIndex = input<number | null>(null);

    readonly itemHovered = output<number | null>();
}