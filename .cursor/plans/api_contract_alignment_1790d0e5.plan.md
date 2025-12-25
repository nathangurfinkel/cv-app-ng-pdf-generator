---
name: API Contract Alignment
overview: Fix API contract mismatches between frontend, AI service, and PDF generator to ensure all services communicate correctly.
todos:
  - id: remove-dead-pdf-routes
    content: Remove unused app/routes/pdf_routes.py from PDF generator (conflicts with main.py implementation)
    status: pending
  - id: verify-pdf-main-contract
    content: Verify app/main.py PDF generation endpoint matches frontend contract exactly (cv_data, template, frontend_url)
    status: pending
  - id: update-pdf-request-model
    content: Update or deprecate PDFRequest model in cv_models.py to match actual usage or remove if unused
    status: pending
    dependencies:
      - verify-pdf-main-contract
  - id: review-pdf-service
    content: Review app/services/pdf_service.py - determine if WeasyPrint implementation is needed or should be removed (main.py uses Playwright)
    status: pending
    dependencies:
      - verify-pdf-main-contract
  - id: verify-interview-headers
    content: Verify interview routes use proper FastAPI header aliases matching frontend (X-User-Tier, X-User-Provider, X-User-Api-Key)
    status: pending
  - id: verify-job-error-model
    content: Verify JobError model in job_models.py matches frontend expectations (optional code/message when error exists)
    status: pending
  - id: verify-frontend-api-contracts
    content: Verify all API calls in frontend api.ts match backend contracts exactly
    status: pending
    dependencies:
      - verify-pdf-main-contract
      - verify-interview-headers
      - verify-job-error-model
  - id: test-pdf-generation
    content: Test PDF generation end-to-end to ensure contract alignment works
    status: pending
    dependencies:
      - verify-frontend-api-contracts
  - id: test-job-polling
    content: Test job status polling with error responses to ensure error format is correct
    status: pending
    dependencies:
      - verify-job-error-model
---

# API Contract Alig

nment Plan

## Issues Identified

### 1. PDF Generator Request Format Mismatch

**Problem**: The PDF generator has two conflicting implementations:

- `app/routes/pdf_routes.py` defines a route using `PDFRequest` model expecting `{ templateId, data }`
- `app/main.py` has a direct endpoint expecting `{ cv_data, template, frontend_url }`
- The frontend sends `{ cv_data, template, frontend_url }` which matches `main.py`
- `pdf_routes.py` is not included in `main.py`, so it's dead code
- `pdf_service.py` expects `PDFRequest` model but is never called

**Impact**: Confusion, dead code, potential future bugs if someone tries to use `pdf_routes.py`

### 2. PDF Generator Model Mismatch

**Problem**:

- `PDFRequest` model in `cv_models.py` expects `templateId` (camelCase) and `data` (not `cv_data`)
- Frontend and `main.py` use `template` (snake_case) and `cv_data`
- Model is not aligned with actual usage

**Impact**: If `pdf_routes.py` is ever used, it will fail

### 3. Interview Routes Header Case Sensitivity

**Problem**:

- Frontend sends headers: `X-User-Tier`, `X-User-Provider`, `X-User-Api-Key`
- Backend expects: `x_user_tier`, `x_user_provider`, `x_user_api_key` (FastAPI should handle case conversion, but explicit is better)

**Impact**: Potential header parsing issues in some environments

### 4. Job Status Response Error Field

**Problem**:

- Frontend expects `error?: { code?: string; message?: string }` (optional fields)
- Backend returns `error?: { code: string; message: string }` (required fields when error exists)
- This should work but could cause issues if backend returns error with missing fields

**Impact**: Type safety issues, potential runtime errors

## Solution

### Phase 1: Clean Up PDF Generator (Single Source of Truth)

1. **Remove dead code**:

- Delete `app/routes/pdf_routes.py` (not used, conflicts with main.py)
- Keep `app/main.py` as the single implementation (it matches frontend contract)

2. **Update PDFRequest model** (if needed for future use):

- Align `cv_models.py` `PDFRequest` to match actual usage: `{ cv_data, template, frontend_url }`
- OR mark it as deprecated/unused if we're not using models for PDF generation

3. **Update pdf_service.py** (if it's meant to be used):

- Either update it to accept the correct format, or remove it if unused
- Currently `pdf_service.py` uses WeasyPrint but `main.py` uses Playwright - these are two different implementations

### Phase 2: Standardize Header Names

1. **AI Service Interview Routes**:

- Ensure FastAPI header aliases match frontend exactly
- Verify `X-User-Tier`, `X-User-Provider`, `X-User-Api-Key` are properly aliased

2. **Job Routes**:

- Verify all routes use consistent header naming
- Check `X-API-Key` vs `X-User-Api-Key` usage

### Phase 3: Align Error Response Types

1. **Job Status Response**:

- Ensure `JobError` model allows optional `code` and `message` when error exists
- Or ensure backend always provides both fields when error exists

2. **Frontend Type Safety**:

- Update frontend types to match backend reality (both fields required when error exists)

## Implementation Checklist

### PDF Generator (`cv-app-ng-pdf-generator`)

- [ ] Remove `app/routes/pdf_routes.py` (dead code)
- [ ] Verify `app/main.py` endpoint matches frontend contract exactly
- [ ] Update or remove `PDFRequest` model in `cv_models.py` to match reality
- [ ] Decide: keep `pdf_service.py` (WeasyPrint) or remove if unused
- [ ] Document which implementation is canonical (Playwright in main.py)

### AI Service (`cv-app-ng-ai-service`)

- [ ] Verify interview route headers use proper FastAPI aliases
- [ ] Check all job routes use consistent header naming
- [ ] Verify `JobError` model matches frontend expectations
- [ ] Test error responses include both `code` and `message` when error exists

### Frontend (`cv-app-ng-frontend`)

- [ ] Verify `api.ts` sends correct field names for PDF generation
- [ ] Verify header names match backend expectations
- [ ] Update types if needed to match backend reality

## Files to Modify

### `cv-app-ng-pdf-generator`

- `app/routes/pdf_routes.py` - DELETE (dead code)
- `app/models/cv_models.py` - UPDATE `PDFRequest` model or mark deprecated
- `app/services/pdf_service.py` - REVIEW (may be unused, WeasyPrint vs Playwright)
- `app/main.py` - VERIFY contract matches frontend

### `cv-app-ng-ai-service`

- `app/routes/interview_routes.py` - VERIFY header aliases
- `app/routes/jobs_routes.py` - VERIFY header consistency
- `app/models/job_models.py` - VERIFY `JobError` model

### `cv-app-ng-frontend`

- `src/services/api.ts` - VERIFY all contracts match
- `src/types.ts` - VERIFY types match backend

## Testing Strategy

1. **PDF Generation**:

- Test frontend → PDF generator request format
- Verify Playwright rendering works with current contract

2. **Job Status Polling**:

- Test error responses include both code and message
- Test successful responses work correctly

3. **Interview Routes**:

- Test headers are properly parsed
- Test with different tier/provider combinations

## Notes

- The PDF generator currently uses **Playwright** in `main.py`, not WeasyPrint from `pdf_service.py`