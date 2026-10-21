import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditResult, AuditorDecisionRequest, AuditorDecisionResponse } from '../models/audit.models';

@Injectable({
    providedIn: 'root',
})
export class AuditApiService {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = 'http://localhost:8000/api/v1/audit';

    auditDocument(file: File): Observable<AuditResult> {
        const formData = new FormData();
        formData.append('file', file);

        return this.http.post<AuditResult>(this.apiUrl, formData);
    }

    submitDecision(payload: AuditorDecisionRequest): Observable<AuditorDecisionResponse> {
        const url = 'http://localhost:8000/api/v1/decision';
        return this.http.post<AuditorDecisionResponse>(url, payload);
    }
}