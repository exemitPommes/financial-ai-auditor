import { CommonModule } from '@angular/common';
import { Component, computed, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent } from 'lib-ng-core-components';
import { AuditResult, AuditorDecisionResponse } from '../../../../core/models/audit.models';
import { DecisionHumana } from '../../../../core/models/audit.types';
import { AuditApiService } from '../../../../core/services/audit-api.service';

@Component({
    selector: 'audit-decision',
    standalone: true,
    imports: [CommonModule, FormsModule, ButtonComponent],
    templateUrl: './audit-decision.component.html',
    styleUrl: './audit-decision.component.scss',
})
export class AuditDecisionComponent {
    private readonly api = inject(AuditApiService);

    readonly auditResult = input.required<AuditResult>();

    readonly decisionSubmitted = output<DecisionHumana>();

    isSubmitting = signal<boolean>(false);
    selectedAction = signal<DecisionHumana | null>(null);
    comment = signal<string>('');
    successResponse = signal<AuditorDecisionResponse | null>(null);

    isAutoApproved = computed(() => this.auditResult().estado === 'AUTO_APPROVED');

    onDirectApprove(): void {
        this.sendDecision('APROBADO', null);
    }

    onSelectAction(action: DecisionHumana): void {
        this.selectedAction.set(action);
    }

    onConfirmAction(): void {
        const action = this.selectedAction();
        if (!action) return;
        this.sendDecision(action, this.comment());
    }

    onCancelAction(): void {
        this.selectedAction.set(null);
        this.comment.set('');
    }

    private sendDecision(decision: DecisionHumana, comentario: string | null): void {
        this.isSubmitting.set(true);

        const payload = {
            decision,
            comentario: comentario || null,
            auditoria: this.auditResult()
        };

        this.api.submitDecision(payload).subscribe({
            next: (res) => {
                this.isSubmitting.set(false);
                this.successResponse.set(res);
                this.decisionSubmitted.emit(decision);
            },
            error: (err) => {
                console.error('Error al guardar decisión:', err);
                this.isSubmitting.set(false);
            }
        });
    }
}