import { Component, input, signal } from '@angular/core';
import { BadgeComponent } from 'lib-ng-core-components';
import { DecisionHumana, EstadoAuditoria, VarianteAuditoria } from '../../../../core/models/audit.types';

@Component({
    selector: 'auditor-header',
    standalone: true,
    templateUrl: './header.component.html',
    styleUrl: './header.component.scss',
    imports: [BadgeComponent]
})
export class HeaderComponent {
    readonly hasAuditFile = input.required<boolean>();
    readonly auditState = input.required<EstadoAuditoria | undefined>();
    readonly statusVariant = input.required<VarianteAuditoria>();
    readonly finalDecision = input<DecisionHumana | null>();

    isModelCardOpen = signal<boolean>(false);

  toggleModelCard(): void {
    this.isModelCardOpen.update(v => !v);
  }
}