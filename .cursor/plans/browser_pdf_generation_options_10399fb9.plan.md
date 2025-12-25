---
name: Browser PDF Generation Options
overview: "Implement two browser-based PDF generation approaches: (1) Browser Print Dialog using window.print() with print-specific CSS, and (2) React-PDF library for programmatic PDF generation. Add test buttons to the FullPreviewModal to compare both approaches."
todos:
  - id: install-react-pdf
    content: Install @react-pdf/renderer package in package.json
    status: pending
  - id: create-print-browser-page
    content: Create PrintBrowserPage.tsx component with print CSS and auto-trigger window.print()
    status: pending
  - id: add-print-browser-route
    content: Add /print-browser/:id route to App.tsx
    status: pending
    dependencies:
      - create-print-browser-page
  - id: add-browser-print-api
    content: Add generatePDFBrowser() method to ApiService that opens print window
    status: pending
    dependencies:
      - add-print-browser-route
  - id: create-pdf-document-component
    content: Create PDFDocument.tsx component using React-PDF primitives, mirroring LivePreview structure
    status: pending
    dependencies:
      - install-react-pdf
  - id: add-react-pdf-api
    content: Add generatePDFReactPDF() method to ApiService that uses React-PDF to generate blob
    status: pending
    dependencies:
      - create-pdf-document-component
  - id: add-test-buttons
    content: Add two test buttons (Browser Print and React-PDF) to FullPreviewModal header
    status: pending
    dependencies:
      - add-browser-print-api
      - add-react-pdf-api
  - id: test-browser-print
    content: "Test browser print dialog: verify window opens, print dialog appears, PDF is searchable"
    status: pending
    dependencies:
      - add-test-buttons
  - id: test-react-pdf
    content: "Test React-PDF generation: verify PDF downloads, matches preview, is searchable"
    status: pending
    dependencies:
      - add-test-buttons
---

# Browser PDF Generation Implementation Plan

## Overview

Implement two browser-based PDF generation options to test and compare:

1. **Browser Print Dialog** - Uses native `window.print()` with `@media print` CSS
2. **React-PDF** - Uses `@react-pdf/renderer` library for programmatic PDF generation

Both options will be accessible via buttons in the `FullPreviewModal` component.

## Architecture

### Option 1: Browser Print Dialog Flow

```javascript
User clicks "Print (Browser)" button
  → ApiService.generatePDFBrowser() 
  → Stores CV data in sessionStorage
  → Opens new window at /print-browser/:id
  → PrintBrowserPage reads data from sessionStorage
  → Renders LivePreview component
  → Auto-triggers window.print()
  → User saves as PDF in browser dialog
```



### Option 2: React-PDF Flow

```javascript
User clicks "Download PDF (React-PDF)" button
  → ApiService.generatePDFReactPDF()
  → Creates PDFDocument component with React-PDF
  → Renders PDF using pdf() from @react-pdf/renderer
  → Downloads PDF blob automatically
```



## Implementation Details

### 1. Browser Print Dialog Implementation

#### 1.1 Create Print Browser Page Component

**File**: `src/pages/PrintBrowserPage.tsx`

- New component that reads CV data from sessionStorage using route param `:id`
- Renders `LivePreview` component without any UI chrome
- Includes `@media print` CSS to hide all non-CV elements
- Auto-triggers `window.print()` after component mounts and data is loaded
- Handles popup blocking gracefully

**Key features**:

- Uses `useParams` to get print ID from route
- Reads from `sessionStorage.getItem(id)` to get `{ cvData, template }`
- Cleans up sessionStorage after reading
- Includes comprehensive print CSS to hide:
- Cookie banners
- Modals
- Navigation
- Any Mantine UI chrome
- Background colors (force white)

#### 1.2 Add Print Browser Route

**File**: `src/App.tsx`

- Add route: `<Route path="/print-browser/:id" element={<PrintBrowserPage />} />`
- Place after existing `/print/:id` route

#### 1.3 Add Browser Print Utility Function

**File**: `src/services/api.ts`

- Add `static async generatePDFBrowser(cvData: CVData, template: TemplateId): Promise<void>`
- Generates unique ID: `print-${Date.now()}`
- Stores data in sessionStorage: `sessionStorage.setItem(id, JSON.stringify({ cvData, template }))`
- Opens new window: `window.open('/print-browser/${id}', '_blank', 'width=1200,height=800')`
- Handles popup blocking with error message
- Note: The print dialog is triggered by the PrintBrowserPage component, not here

#### 1.4 Add Print-Specific CSS

**File**: `src/pages/PrintBrowserPage.tsx` (inline style tag)

- Comprehensive `@media print` rules:
  ```css
    @media print {
      body > *:not(#root) { display: none !important; }
      body { margin: 0; padding: 0; background: white; }
      [data-mantine-component], .mantine-Modal-root, .cookie-banner, nav, header, footer { display: none !important; }
      #root { width: 100%; height: 100%; margin: 0; padding: 0; }
      /* Ensure LivePreview renders at full size */
      /* Remove any scaling transforms */
    }
  ```




### 2. React-PDF Implementation

#### 2.1 Install React-PDF Package

**File**: `package.json`

- Add dependency: `"@react-pdf/renderer": "^3.x.x"`
- Run `npm install` after adding

#### 2.2 Create PDF Document Component

**File**: `src/components/PDFDocument.tsx`

- New component using React-PDF primitives: `Document`, `Page`, `View`, `Text`, `StyleSheet`
- Mirrors the structure of `LivePreview` component
- Converts Mantine components to React-PDF equivalents:
- `Box` → `View`
- `Text` → `Text`
- `Stack` → `View` with `flexDirection: 'column'`
- `Group` → `View` with `flexDirection: 'row'`
- `Badge` → `View` with styled background
- Maps template styles from `templateStyles.ts` to React-PDF StyleSheet
- Handles all template variants (modern, classic, reverse-chronological, functional, combination)
- Handles pagination (multiple pages if content exceeds A4)

**Key structure**:

```typescript
import { Document, Page, View, Text, StyleSheet } from '@react-pdf/renderer';

export const PDFDocument = ({ cvData, template }: { cvData: CVData, template: TemplateId }) => (
  <Document>
    <Page size="A4" style={styles.page}>
      {/* Convert LivePreview sections to React-PDF */}
    </Page>
  </Document>
);
```

**Style mapping**:

- Convert `templateStyles` object to React-PDF `StyleSheet.create()`
- Map font sizes (px → pt conversion: 1px ≈ 0.75pt)
- Map colors (hex strings work in React-PDF)
- Map spacing (px → pt)
- Handle fonts: React-PDF supports Helvetica, Times-Roman, Courier by default

#### 2.3 Add React-PDF Utility Function

**File**: `src/services/api.ts`

- Add `static async generatePDFReactPDF(cvData: CVData, template: TemplateId): Promise<Blob>`
- Import `pdf` from `@react-pdf/renderer`
- Import `PDFDocument` component
- Generate PDF: `const blob = await pdf(<PDFDocument cvData={cvData} template={template} />).toBlob()`
- Return blob for download

**Note**: React-PDF's `pdf()` function returns a promise that resolves to a PDF instance with `.toBlob()` method.

### 3. Add Test Buttons to FullPreviewModal

**File**: `src/components/FullPreviewModal.tsx`

- Add two new buttons in the header `Group` (next to existing "Download PDF" button):

1. **"Print (Browser)"** button

    - Calls `ApiService.generatePDFBrowser(cvData, selectedTemplate)`
    - Shows loading state while opening window
    - Handles errors (popup blocked, etc.)

2. **"Download PDF (React-PDF)"** button

    - Calls `ApiService.generatePDFReactPDF(cvData, selectedTemplate)`
    - Shows loading state during generation
    - Downloads PDF blob automatically
    - Handles errors gracefully

**Button placement**: Add to the existing button group in the header (lines 138-168)**Icons**:

- Browser Print: `IconPrinter` from `@tabler/icons-react`
- React-PDF: `IconFileTypePdf` or `IconDownload` from `@tabler/icons-react`

### 4. Template Style Conversion for React-PDF

**File**: `src/components/PDFDocument.tsx`

- Create helper function `getReactPDFStyles(template: TemplateId)` that:
- Reads from `templateStyles.ts` (or imports `getTemplateStyles`)
- Converts to React-PDF StyleSheet format
- Handles font size conversion (px → pt)
- Maps font families (Helvetica, Times-Roman work natively)
- Converts all CSS properties to React-PDF equivalents

**Key conversions**:

- `fontSize: '24px'` → `fontSize: 18` (pt)
- `fontWeight: 'bold'` → `fontWeight: 'bold'` (same)
- `color: '#1e40af'` → `color: '#1e40af'` (same)
- `padding: '16px'` → `padding: 12` (pt)
- `flexDirection: 'row'` → `flexDirection: 'row'` (same)
- `borderBottom: '1px solid #2563eb'` → `borderBottom: '1pt solid #2563eb'`

### 5. Handle Pagination in React-PDF

**File**: `src/components/PDFDocument.tsx`

- React-PDF automatically handles page breaks, but we need to:
- Ensure content doesn't overflow A4 page (210mm × 297mm)
- Use `wrap={true}` on Text components for long content
- Consider manual page breaks for sections if needed
- Test with long CVs to ensure proper pagination

## File Changes Summary

### New Files

1. `src/pages/PrintBrowserPage.tsx` - Browser print page component
2. `src/components/PDFDocument.tsx` - React-PDF document component

### Modified Files

1. `src/App.tsx` - Add `/print-browser/:id` route
2. `src/services/api.ts` - Add `generatePDFBrowser()` and `generatePDFReactPDF()` methods
3. `src/components/FullPreviewModal.tsx` - Add two test buttons
4. `package.json` - Add `@react-pdf/renderer` dependency

## Testing Strategy

1. **Browser Print Dialog**:

- Click "Print (Browser)" button
- Verify new window opens with CV preview
- Verify print dialog appears automatically
- Verify no UI chrome is visible in print preview
- Save as PDF and verify it's searchable
- Verify PDF matches preview exactly

2. **React-PDF**:

- Click "Download PDF (React-PDF)" button
- Verify PDF downloads automatically
- Open PDF and verify content matches preview
- Verify PDF is searchable
- Test with different templates (modern, classic, etc.)
- Test with long CVs (multiple pages)

3. **Comparison**:

- Generate PDFs using both methods
- Compare file sizes
- Compare rendering quality
- Compare searchability
- Compare performance (generation time)

## Dependencies

- `@react-pdf/renderer`: ^3.4.0 (latest stable)
- No additional dependencies for browser print (uses native APIs)

## Notes

- Browser Print Dialog requires user interaction (clicking "Save as PDF"), but produces high-quality, searchable PDFs
- React-PDF generates PDFs automatically but requires rebuilding the layout using React-PDF primitives
- Both approaches should produce searchable PDFs (browser print natively, React-PDF with text layer)
- React-PDF may have slight differences in rendering compared to browser print due to different rendering engines