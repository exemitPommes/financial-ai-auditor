import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditResult } from '../models/audit.models';

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

}