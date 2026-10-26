import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditResult, AuditorDecisionRequest, AuditorDecisionResponse } from '../models/audit.models';
import { environment } from '../../../environments/environment';

@Injectable({
    providedIn: 'root',
})
export class AuditApiService {
    private readonly http = inject(HttpClient);
    private readonly baseUrl = environment.apiBaseUrl;

    auditDocument(file: File): Observable<AuditResult> {
        const formData = new FormData();
        formData.append('file', file);

        return this.http.post<AuditResult>(`${this.baseUrl}/audit`, formData);
    }

    submitDecision(payload: AuditorDecisionRequest): Observable<AuditorDecisionResponse> {
        return this.http.post<AuditorDecisionResponse>(`${this.baseUrl}/decision`, payload);
    }
}