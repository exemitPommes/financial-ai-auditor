import { Component, computed, input, output } from '@angular/core';
import { AlertComponent } from 'lib-ng-core-components';
import { AuditResult } from 'src/app/core/models/audit.models';
import { DecisionHumana } from 'src/app/core/models/audit.types';
import { AuditDecisionComponent } from '../audit-decision/audit-decision.component';
import { AuditIntroductionComponent } from '../audit-introduction/audit-introduction.component';
import { AuditTableComponent } from '../audit-table/audit-table.component';

@Component({
    selector: 'audit-summary',
    standalone: true,
    templateUrl: './audit-summary.component.html',
    styleUrl: './audit-summary.component.scss',
    imports: [AlertComponent, AuditTableComponent, AuditDecisionComponent, AuditIntroductionComponent]

})
export class AuditSummaryComponent {
    readonly auditResult = input<AuditResult | null>(null);
    readonly isLoading = input<boolean>(false);
    readonly errorMessage = input<string | null>(null);
    readonly hoveredItemIndex = input<number | null>(null);

    readonly runAudit = output<void>();
    readonly itemHovered = output<number | null>();
    readonly decisionSubmitted = output<DecisionHumana>();

    readonly hasAuditFile = computed(() => this.auditResult() !== null);
}