---
name: Chrome Extension - Job Scraper & Tracker
overview: |
  Build a Manifest V3 Chrome extension that scrapes job descriptions from LinkedIn, Indeed,
  and other job boards, sanitizes them with Readability.js, and syncs them to the web app's
  encrypted vault for semantic matching and tracking.
todos:
  - id: decide-extension-scope
    content: Decide which job boards to support in MVP (LinkedIn, Indeed, or both).
    status: pending
  - id: scaffold-mv3-extension
    content: Scaffold Manifest V3 extension with content scripts, service worker, and popup UI.
    status: pending
  - id: implement-dom-scraping-linkedin
    content: Implement content script for LinkedIn job pages (detect selectors, extract job description HTML).
    status: pending
    dependencies:
      - scaffold-mv3-extension
  - id: add-readabilityjs-sanitization
    content: Integrate Readability.js to extract clean job description text from noisy HTML.
    status: pending
    dependencies:
      - implement-dom-scraping-linkedin
  - id: implement-extension-to-webapp-bridge
    content: Implement secure message bridge (postMessage) from extension to web app with origin validation.
    status: pending
    dependencies:
      - add-readabilityjs-sanitization
  - id: add-job-storage-in-vault
    content: Store scraped jobs in encrypted Dexie vault (reuse schema from local-first_vault plan).
    status: pending
    dependencies:
      - implement-extension-to-webapp-bridge
  - id: create-extension-popup-ui
    content: Create extension popup UI (Save Job button, job count, status indicator).
    status: pending
  - id: add-chrome-web-store-listing
    content: Prepare Chrome Web Store listing (icons, screenshots, description, privacy policy).
    status: pending
---

# Chrome Extension: Job Scraper & Tracker

## Goal

Build a **Manifest V3 Chrome extension** that:
1. Detects when the user is viewing a job posting on LinkedIn, Indeed, etc.
2. Scrapes the job description HTML
3. Sanitizes it with **Readability.js** (removes ads, navigation, tracking scripts)
4. Sends the clean job data to the main web app via secure `postMessage`
5. Stores the job in the user's encrypted vault for semantic matching and tracking

**Key Differentiator**: Most resume builders require manual copy-paste of job descriptions. This extension **automates** it, saving users time and ensuring they don't miss critical keywords.

## Source References

- **Implementation Basis**: `cv-app-ng-frontend/docs/implementation-plan/03-resume-intelligence-parsing.md` § 3.2 "Job Description Extraction Architecture"
- **Related Plans**:
  - `local-first_vault_c7381a99.plan.md` (provides encrypted storage for jobs)
  - `client-side_resume_matcher_b2c6885f.plan.md` (uses scraped jobs for matching)
  - `10_product_tiers_and_packaging.plan.md` (extension is a BYOK/Managed feature)

## Manifest V3 Architecture

### Why Manifest V3?

- **Required**: Google deprecated Manifest V2 (Jan 2023)
- **Security**: Stricter CSP (Content Security Policy), no arbitrary code execution
- **Performance**: Service workers replace persistent background pages (lower memory)

**Key Differences from MV2**:
- ❌ No `background.html` → ✅ `service_worker.js` (ephemeral, event-driven)
- ❌ No `executeScript()` → ✅ Declarative content scripts
- ❌ No `webRequest` blocking → ✅ `declarativeNetRequest` (not needed for our use case)

### Extension Structure

```
resumint-job-scraper/
  manifest.json                  ← MV3 manifest
  service-worker.js              ← Background tasks (ephemeral)
  content-scripts/
    linkedin-scraper.js          ← Runs on linkedin.com/jobs/*
    indeed-scraper.js            ← Runs on indeed.com/viewjob/*
    readability.min.js           ← Bundled Readability.js
  popup/
    popup.html                   ← Extension popup UI
    popup.js                     ← Popup logic
    popup.css                    ← Styling
  icons/
    icon-16.png
    icon-48.png
    icon-128.png
  _locales/
    en/
      messages.json              ← Internationalization
```

### Manifest V3 Config

**File**: `manifest.json`

```json
{
  "manifest_version": 3,
  "name": "ResuMint Job Tracker",
  "version": "1.0.0",
  "description": "Save job descriptions from LinkedIn and Indeed to your ResuMint vault for semantic matching.",
  "permissions": [
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "https://*.linkedin.com/*",
    "https://*.indeed.com/*"
  ],
  "background": {
    "service_worker": "service-worker.js"
  },
  "content_scripts": [
    {
      "matches": ["https://*.linkedin.com/jobs/*"],
      "js": ["content-scripts/readability.min.js", "content-scripts/linkedin-scraper.js"],
      "run_at": "document_idle"
    },
    {
      "matches": ["https://*.indeed.com/viewjob*"],
      "js": ["content-scripts/readability.min.js", "content-scripts/indeed-scraper.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  "icons": {
    "16": "icons/icon-16.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  }
}
```

## Content Script: LinkedIn Scraper

**File**: `content-scripts/linkedin-scraper.js`

```javascript
/**
 * LinkedIn job scraper content script.
 * Detects job posting pages and extracts job description HTML.
 */

(function() {
  console.log('[ResuMint] LinkedIn scraper loaded');
  
  // Detect if we're on a job posting page
  function isJobPage() {
    return window.location.pathname.startsWith('/jobs/view/');
  }
  
  // Extract job data
  function scrapeJobData() {
    // LinkedIn job selectors (as of 2025; may change)
    const titleEl = document.querySelector('.job-details-jobs-unified-top-card__job-title');
    const companyEl = document.querySelector('.job-details-jobs-unified-top-card__company-name');
    const locationEl = document.querySelector('.job-details-jobs-unified-top-card__bullet');
    const descriptionEl = document.querySelector('.jobs-description__content');
    
    if (!titleEl || !descriptionEl) {
      console.warn('[ResuMint] Could not find job elements');
      return null;
    }
    
    // Use Readability.js to extract clean HTML
    const documentClone = document.cloneNode(true);
    const reader = new Readability(documentClone, {
      keepClasses: false,
      nbTopCandidates: 1
    });
    
    const article = reader.parse();
    
    return {
      title: titleEl.textContent.trim(),
      company: companyEl?.textContent.trim() || 'Unknown Company',
      location: locationEl?.textContent.trim() || 'Unknown Location',
      url: window.location.href,
      description: article?.textContent || descriptionEl.textContent.trim(),
      scrapedAt: new Date().toISOString(),
      source: 'linkedin'
    };
  }
  
  // Inject "Save to ResuMint" button
  function injectSaveButton() {
    if (document.getElementById('resumint-save-btn')) return; // Already injected
    
    const targetContainer = document.querySelector('.jobs-details__main-content');
    if (!targetContainer) return;
    
    const button = document.createElement('button');
    button.id = 'resumint-save-btn';
    button.textContent = '💾 Save to ResuMint';
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      padding: 12px 24px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    
    button.addEventListener('click', async () => {
      button.textContent = '⏳ Saving...';
      button.disabled = true;
      
      const jobData = scrapeJobData();
      
      if (!jobData) {
        button.textContent = '❌ Failed';
        setTimeout(() => {
          button.textContent = '💾 Save to ResuMint';
          button.disabled = false;
        }, 2000);
        return;
      }
      
      // Send to service worker
      chrome.runtime.sendMessage({ action: 'saveJob', data: jobData }, (response) => {
        if (response?.success) {
          button.textContent = '✅ Saved!';
          setTimeout(() => {
            button.textContent = '💾 Save to ResuMint';
            button.disabled = false;
          }, 2000);
        } else {
          button.textContent = '❌ Failed';
          setTimeout(() => {
            button.textContent = '💾 Save to ResuMint';
            button.disabled = false;
          }, 2000);
        }
      });
    });
    
    document.body.appendChild(button);
  }
  
  // Initialize
  if (isJobPage()) {
    // Wait for DOM to settle
    setTimeout(injectSaveButton, 1000);
  }
  
  // Watch for SPA navigation (LinkedIn is a React app)
  let lastUrl = window.location.href;
  const observer = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      if (isJobPage()) {
        setTimeout(injectSaveButton, 1000);
      }
    }
  });
  
  observer.observe(document.body, { childList: true, subtree: true });
})();
```

## Service Worker: Job Storage Bridge

**File**: `service-worker.js`

```javascript
/**
 * Background service worker for ResuMint extension.
 * Handles job data storage and communication with web app.
 */

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveJob') {
    handleSaveJob(request.data, sendResponse);
    return true; // Keep message channel open for async response
  }
});

async function handleSaveJob(jobData, sendResponse) {
  try {
    // Store in chrome.storage.local (ephemeral storage for extension)
    await chrome.storage.local.set({
      [`job_${Date.now()}`]: jobData
    });
    
    // Forward to web app (if open)
    await forwardToWebApp(jobData);
    
    sendResponse({ success: true });
  } catch (error) {
    console.error('Failed to save job:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function forwardToWebApp(jobData) {
  /**
   * Send job data to the main web app via postMessage.
   * The web app listens for messages with origin validation.
   */
  
  // Find open ResuMint tabs
  const tabs = await chrome.tabs.query({ url: 'https://resumint.dev/*' });
  
  if (tabs.length === 0) {
    console.log('[ResuMint] Web app not open; job stored locally');
    return;
  }
  
  // Send message to first matching tab
  await chrome.tabs.sendMessage(tabs[0].id, {
    type: 'RESUMINT_JOB_SAVED',
    payload: jobData
  });
}
```

## Web App Integration (`cv-app-ng-frontend`)

### 1. Add Extension Message Listener

**File**: `src/services/extensionBridge.ts`

```typescript
/**
 * Bridge for receiving job data from Chrome extension.
 */

export interface ExtensionJobData {
  title: string;
  company: string;
  location: string;
  url: string;
  description: string;
  scrapedAt: string;
  source: 'linkedin' | 'indeed';
}

export class ExtensionBridgeService {
  private listeners: Set<(job: ExtensionJobData) => void> = new Set();
  
  constructor() {
    this.initMessageListener();
  }
  
  private initMessageListener() {
    window.addEventListener('message', (event) => {
      // Validate origin (only accept from extension)
      if (event.source !== window) return;
      
      if (event.data.type === 'RESUMINT_JOB_SAVED') {
        this.handleJobReceived(event.data.payload);
      }
    });
    
    // Also listen for chrome.runtime messages (if extension injects into page)
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.onMessage.addListener((request) => {
        if (request.type === 'RESUMINT_JOB_SAVED') {
          this.handleJobReceived(request.payload);
        }
      });
    }
  }
  
  private handleJobReceived(jobData: ExtensionJobData) {
    console.log('[ResuMint] Job received from extension:', jobData.title);
    
    // Notify all listeners
    this.listeners.forEach(listener => listener(jobData));
  }
  
  /**
   * Register a callback to be notified when jobs are scraped.
   */
  onJobScraped(callback: (job: ExtensionJobData) => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback); // Cleanup function
  }
}

export const extensionBridge = new ExtensionBridgeService();
```

### 2. Store Scraped Jobs in Vault

**File**: `src/contexts/JobLibraryContext.tsx`

```typescript
import React, { createContext, useContext, useEffect } from 'react';
import { db } from '../db/ResuMintDB';
import { extensionBridge, ExtensionJobData } from '../services/extensionBridge';
import { useLiveQuery } from 'dexie-react-hooks';

interface JobLibraryContextValue {
  jobs: ExtensionJobData[];
  addJob: (job: ExtensionJobData) => Promise<void>;
}

const JobLibraryContext = createContext<JobLibraryContextValue | undefined>(undefined);

export const JobLibraryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const jobs = useLiveQuery(() => db.jobs.toArray(), []) || [];
  
  useEffect(() => {
    // Listen for jobs from extension
    const unsubscribe = extensionBridge.onJobScraped(async (job) => {
      await addJob(job);
      // Show toast notification
      console.log('Job saved to vault:', job.title);
    });
    
    return unsubscribe;
  }, []);
  
  const addJob = async (job: ExtensionJobData) => {
    await db.jobs.add({
      ...job,
      id: undefined, // Auto-increment
      status: 'active'
    });
  };
  
  return (
    <JobLibraryContext.Provider value={{ jobs, addJob }}>
      {children}
    </JobLibraryContext.Provider>
  );
};

export const useJobLibrary = () => {
  const context = useContext(JobLibraryContext);
  if (!context) {
    throw new Error('useJobLibrary must be used within JobLibraryProvider');
  }
  return context;
};
```

## Extension Popup UI

**File**: `popup/popup.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <h1>🎯 ResuMint Job Tracker</h1>
    <div class="stats">
      <div class="stat">
        <span class="stat-value" id="job-count">0</span>
        <span class="stat-label">Jobs Saved</span>
      </div>
    </div>
    <div class="actions">
      <button id="open-webapp">Open ResuMint</button>
      <button id="settings">Settings</button>
    </div>
    <p class="hint">
      Navigate to a job posting on LinkedIn or Indeed and click "Save to ResuMint".
    </p>
  </div>
  <script src="popup.js"></script>
</body>
</html>
```

**File**: `popup/popup.js`

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  // Load job count from storage
  const storage = await chrome.storage.local.get(null);
  const jobCount = Object.keys(storage).filter(k => k.startsWith('job_')).length;
  document.getElementById('job-count').textContent = jobCount;
  
  // Open web app
  document.getElementById('open-webapp').addEventListener('click', () => {
    chrome.tabs.create({ url: 'https://resumint.dev/app/dashboard' });
  });
  
  // Settings
  document.getElementById('settings').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});
```

## Chrome Web Store Listing

### Metadata

- **Name**: ResuMint Job Tracker
- **Short Description**: "Save job descriptions from LinkedIn and Indeed to your ResuMint vault for AI-powered resume matching."
- **Category**: Productivity
- **Privacy Policy**: https://resumint.dev/privacy
- **Support URL**: https://resumint.dev/support

### Screenshots (1280x800)

1. Extension button on LinkedIn job page
2. "Save to ResuMint" button in action
3. Popup UI showing saved jobs
4. Web app dashboard with scraped jobs

### Icons

- **16x16**: Toolbar icon
- **48x48**: Extensions page
- **128x128**: Chrome Web Store listing

## Security Considerations

### 1. Origin Validation

**Problem**: Malicious sites could send fake job data to the web app.

**Solution**: Validate message origin in `extensionBridge.ts`:

```typescript
if (event.origin !== 'https://resumint.dev') return;
```

### 2. Content Sanitization

**Problem**: Scraped HTML could contain XSS payloads.

**Solution**: Use Readability.js (strips all scripts) + DOMPurify (optional) to sanitize HTML.

### 3. Permission Minimization

**Permissions Requested**:
- ✅ `storage`: Store scraped jobs locally
- ✅ `activeTab`: Access current tab (only when user clicks extension icon)
- ✅ `host_permissions`: Access LinkedIn/Indeed pages

**Permissions NOT Requested**:
- ❌ `tabs`: Not needed (we use `activeTab` for better privacy)
- ❌ `webRequest`: Not needed (no network interception)

## Non-Goals (This Plan)

- ❌ Supporting non-Chromium browsers (Firefox extension is a separate effort)
- ❌ Scraping job boards beyond LinkedIn/Indeed (can add later)
- ❌ Auto-applying to jobs (out of scope)

## Acceptance Criteria

- ✅ Extension is published on Chrome Web Store
- ✅ "Save to ResuMint" button appears on LinkedIn job pages
- ✅ Readability.js successfully extracts clean job description text
- ✅ Jobs are forwarded to web app via secure postMessage
- ✅ Jobs are stored in encrypted Dexie vault
- ✅ Extension popup shows job count
- ✅ Feature is gated to BYOK/Managed tiers

## Open Questions

1. **Job deduplication**: How do we handle users saving the same job twice? (Suggestion: hash URL and check for duplicates)
2. **Scraping reliability**: LinkedIn often changes their DOM structure. How do we handle breakage? (Suggestion: add fallback selectors + user feedback mechanism)
3. **Multi-browser support**: Should we also build a Firefox extension? (Suggestion: yes, but defer to Phase 4)

## Implementation Checklist

- [ ] **`decide-extension-scope`**: Finalize supported job boards (LinkedIn + Indeed for MVP)
- [ ] **`scaffold-mv3-extension`**: Create extension folder structure and manifest.json
- [ ] **`implement-dom-scraping-linkedin`**: Implement LinkedIn content script
- [ ] **`add-readabilityjs-sanitization`**: Integrate Readability.js for HTML sanitization
- [ ] **`implement-extension-to-webapp-bridge`**: Implement postMessage bridge with origin validation
- [ ] **`add-job-storage-in-vault`**: Integrate with Dexie vault (reuse `local-first_vault` schema)
- [ ] **`create-extension-popup-ui`**: Build popup HTML/CSS/JS
- [ ] **`add-chrome-web-store-listing`**: Prepare assets and submit for review

## Related Plans

- **`local-first_vault_c7381a99.plan.md`**: Provides encrypted storage for scraped jobs
- **`client-side_resume_matcher_b2c6885f.plan.md`**: Uses scraped jobs for semantic matching
- **`10_product_tiers_and_packaging.plan.md`**: Extension is a BYOK/Managed feature

