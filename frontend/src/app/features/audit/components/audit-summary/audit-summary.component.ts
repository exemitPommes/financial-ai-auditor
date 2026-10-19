import { Component, computed, input, output } from '@angular/core';
import { AuditResult } from 'src/app/core/models/audit.models';
import { 
  ButtonComponent,
  BadgeComponent,
  CardComponent,
  SkeletonComponent,
  AlertComponent,
} from 'lib-ng-core-components';
import { AuditTableComponent } from '../audit-table/audit-table.component';

@Component({
    selector: 'audit-summary',
    standalone: true,
    templateUrl: './audit-summary.component.html',
    styleUrl: './audit-summary.component.scss',
    imports: [AlertComponent, CardComponent, SkeletonComponent, AuditTableComponent]

})
export class AuditSummaryComponent {
    readonly auditResult = input<AuditResult | null>(null);
    readonly isLoading = input<boolean>(false);
    readonly errorMessage = input<string | null>(null);
    readonly hoveredItemIndex = input<number | null>(null);

    readonly runAudit = output<void>();
    readonly itemHovered = output<number | null>();

    readonly hasAuditFile = computed(() => this.auditResult() !== null);
}