// API Base detection (supports file:// scheme double-clicks and server routing)
const API_BASE = (window.location.protocol === 'file:' || window.location.origin === 'null') 
    ? 'http://127.0.0.1:8000' 
    : window.location.origin;

// Local application state
let state = {
    documents: [],
    activeDocumentId: null,
    activeDocument: null,
};

// DOM Cache
const dom = {
    groqApiKeyInput: document.getElementById('groq-api-key-input'),
    historyList: document.getElementById('history-list'),
    btnShowUpload: document.getElementById('btn-show-upload'),
    activeFilename: document.getElementById('active-filename'),
    activeFileBadge: document.getElementById('active-file-badge'),
    workspaceTabs: document.getElementById('workspace-tabs'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    viewUpload: document.getElementById('view-upload'),
    uploadZone: document.getElementById('upload-zone'),
    fileInput: document.getElementById('file-input'),
    progressContainer: document.getElementById('progress-container'),
    progressBarFill: document.getElementById('progress-bar-fill'),
    progressText: document.getElementById('progress-text'),
    summaryTextContainer: document.getElementById('summary-text-container'),
    btnDownloadPdf: document.getElementById('btn-download-pdf'),
    btnDownloadDocx: document.getElementById('btn-download-docx'),
    btnRegenerateSummary: document.getElementById('btn-regenerate-summary'),
    analyticsError: document.getElementById('analytics-error'),
    analyticsContent: document.getElementById('analytics-content'),
    statRows: document.getElementById('stat-rows'),
    statCols: document.getElementById('stat-cols'),
    statNumericCount: document.getElementById('stat-numeric-count'),
    schemaTableBody: document.getElementById('schema-table-body'),
    chartsViewerContainer: document.getElementById('charts-viewer-container'),
    chatHistoryLog: document.getElementById('chat-history-log'),
    chatPromptInput: document.getElementById('chat-prompt-input'),
    btnSendChat: document.getElementById('btn-send-chat'),
    toast: document.getElementById('toast'),
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    // Load saved Groq API key
    const savedGroqKey = localStorage.getItem('groq_api_key');
    if (savedGroqKey) {
        dom.groqApiKeyInput.value = savedGroqKey;
    }

    // Save key to local storage on change
    dom.groqApiKeyInput.addEventListener('change', () => {
        localStorage.setItem('groq_api_key', dom.groqApiKeyInput.value.trim());
        showToast('Groq API key saved successfully', 'info');
    });

    // Sidebar: show upload click
    dom.btnShowUpload.addEventListener('click', showUploadView);

    // Load documents list
    loadHistory();

    // Setup file pickers & drag-drop
    setupUploadEvents();

    // Setup Workspace Tabs
    setupTabEvents();

    // Setup Q&A send events
    setupChatEvents();

    // Setup Export download handlers
    setupExportEvents();
});

// Toast popup utility
function showToast(message, type = 'success') {
    dom.toast.textContent = message;
    dom.toast.className = `toast ${type} show`;
    setTimeout(() => {
        dom.toast.className = `toast ${type}`;
    }, 3000);
}

// Fetch historical documents
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/history/`);
        if (!response.ok) throw new Error('Failed to load uploads history');
        state.documents = await response.json();
        renderHistoryList();
    } catch (err) {
        console.error(err);
        showToast('Could not load upload history', 'error');
    }
}

// Render Sidebar upload items
function renderHistoryList() {
    if (state.documents.length === 0) {
        dom.historyList.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); margin-top: 2rem; font-size: 0.9rem;">
                No documents uploaded yet
            </div>`;
        return;
    }

    dom.historyList.innerHTML = state.documents.map(doc => {
        const dateStr = new Date(doc.uploaded_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        const activeClass = state.activeDocumentId === doc.id ? 'active' : '';
        return `
            <div class="history-item ${activeClass}" data-id="${doc.id}">
                <div class="history-item-details">
                    <div class="history-item-name">${escapeHTML(doc.filename)}</div>
                    <div class="history-item-meta">${escapeHTML(doc.file_type.toUpperCase())} &bull; ${dateStr}</div>
                </div>
                <button class="btn-delete-history" title="Delete document">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        `;
    }).join('');

    // Attach click listeners to history items
    dom.historyList.querySelectorAll('.history-item').forEach(item => {
        const docId = parseInt(item.getAttribute('data-id'));
        item.addEventListener('click', (e) => {
            if (e.target.closest('.btn-delete-history')) {
                deleteDocument(docId, e);
            } else {
                selectDocument(docId);
            }
        });
    });
}

// Select active document and load its data
async function selectDocument(id) {
    state.activeDocumentId = id;
    renderHistoryList();

    try {
        const response = await fetch(`${API_BASE}/api/history/${id}`);
        if (!response.ok) throw new Error('Document details not found');
        
        const doc = await response.json();
        state.activeDocument = doc;

        // Update header info
        dom.activeFilename.textContent = doc.filename;
        dom.activeFileBadge.textContent = doc.file_type;
        dom.activeFileBadge.style.display = 'inline-block';

        // Hide upload panel, show tabs
        dom.viewUpload.classList.remove('active');
        dom.workspaceTabs.style.display = 'flex';

        // Switch to Summary Tab
        switchTab('tab-summary');

        // Populate tabs
        renderSummaryTab();
        renderAnalyticsTab();
        renderChatTab();

    } catch (err) {
        console.error(err);
        showToast('Error loading active document details', 'error');
    }
}

// Delete Document handler
async function deleteDocument(id, event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this document and all its data?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Delete failed');

        showToast('Document deleted');
        
        if (state.activeDocumentId === id) {
            showUploadView();
        }
        
        loadHistory();
    } catch (err) {
        console.error(err);
        showToast('Failed to delete document', 'error');
    }
}

// Reset workspace view to uploading screen
function showUploadView() {
    state.activeDocumentId = null;
    state.activeDocument = null;
    renderHistoryList();

    dom.activeFilename.textContent = "No Document Active";
    dom.activeFileBadge.style.display = 'none';
    dom.workspaceTabs.style.display = 'none';

    // Show upload pane, hide others
    dom.tabPanes.forEach(pane => pane.classList.remove('active'));
    dom.viewUpload.classList.add('active');
}

// Drag & Drop / File Input setup
function setupUploadEvents() {
    dom.uploadZone.addEventListener('click', () => dom.fileInput.click());

    dom.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dom.uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dom.uploadZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dom.uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dom.uploadZone.classList.remove('dragover');
        }, false);
    });

    dom.uploadZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
}

// Perform AJAX file upload
async function handleFileUpload(file) {
    // Show loading indicators
    dom.progressContainer.style.display = 'block';
    dom.progressBarFill.style.width = '10%';
    dom.progressText.textContent = 'Uploading file...';

    const formData = new FormData();
    formData.append('file', file);

    const headers = {};
    const customGroqKey = dom.groqApiKeyInput.value.trim();
    if (customGroqKey) {
        headers['X-Groq-API-Key'] = customGroqKey;
    }

    try {
        dom.progressBarFill.style.width = '40%';
        dom.progressText.textContent = 'Parsing content and generating AI Summary...';

        const response = await fetch(`${API_BASE}/api/upload/`, {
            method: 'POST',
            body: formData,
            headers: headers
        });

        if (!response.ok) {
            const errDetails = await response.json();
            throw new Error(errDetails.detail || 'Upload process failed');
        }

        dom.progressBarFill.style.width = '100%';
        dom.progressText.textContent = 'Upload complete!';
        
        const data = await response.json();
        if (data.summary_error) {
            showToast('Groq unavailable; local summary generated.', 'info');
        } else {
            showToast('Document successfully processed!');
        }

        // Refresh lists and select newly uploaded doc
        await loadHistory();
        selectDocument(data.id);

    } catch (err) {
        console.error(err);
        showToast(err.message, 'error');
    } finally {
        // Reset progress bar UI
        setTimeout(() => {
            dom.progressContainer.style.display = 'none';
            dom.progressBarFill.style.width = '0%';
        }, 1000);
    }
}

// Workspace tab switching logic
function setupTabEvents() {
    dom.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    dom.tabBtns.forEach(b => {
        if (b.getAttribute('data-tab') === tabId) b.classList.add('active');
        else b.classList.remove('active');
    });

    dom.tabPanes.forEach(pane => {
        if (pane.id === tabId) pane.classList.add('active');
        else pane.classList.remove('active');
    });

    // Auto-scroll chat history bottom on switching to Chat tab
    if (tabId === 'tab-chat') {
        setTimeout(() => {
            dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;
        }, 50);
    }
}

// Render summary markdown view
function renderSummaryTab() {
    const doc = state.activeDocument;
    if (!doc) return;

    dom.summaryTextContainer.innerHTML = markdownToHTML(doc.summary);
}

// Render Analytics schema and Matplotlib charts
function renderAnalyticsTab() {
    const doc = state.activeDocument;
    if (!doc) return;

    const stats = doc.doc_metadata;
    if (!stats || !stats.is_tabular) {
        dom.analyticsError.style.display = 'block';
        dom.analyticsContent.style.display = 'none';
        return;
    }

    dom.analyticsError.style.display = 'none';
    dom.analyticsContent.style.display = 'block';

    const tStats = stats.tabular_stats;
    dom.statRows.textContent = tStats.row_count.toLocaleString();
    dom.statCols.textContent = tStats.column_count.toLocaleString();
    dom.statNumericCount.textContent = tStats.numeric_columns.length;

    // Render Schema Table
    dom.schemaTableBody.innerHTML = tStats.columns.map(col => {
        const type = tStats.column_types[col] || 'unknown';
        const missing = tStats.missing_values[col] !== undefined ? tStats.missing_values[col] : 0;
        return `
            <tr>
                <td style="font-weight: 550; color: var(--text-primary);">${escapeHTML(col)}</td>
                <td><code style="background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.85rem;">${escapeHTML(type)}</code></td>
                <td>${missing.toLocaleString()}</td>
            </tr>
        `;
    }).join('');

    // Render Charts
    if (doc.charts && doc.charts.length > 0) {
        dom.chartsViewerContainer.innerHTML = doc.charts.map((chart, idx) => `
            <div class="chart-card glass-panel">
                <h3>Visualization Plot #${idx + 1}</h3>
                <img src="${API_BASE}/charts/${chart}" class="chart-img" alt="Analytical Chart Visualization">
            </div>
        `).join('');
    } else {
        dom.chartsViewerContainer.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;">
                No analysis charts generated for this document.
            </div>`;
    }
}

// Setup chat interaction
function setupChatEvents() {
    dom.btnSendChat.addEventListener('click', sendChatMessage);
    dom.chatPromptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// Render existing chat history in dashboard
async function renderChatTab() {
    const id = state.activeDocumentId;
    dom.chatHistoryLog.innerHTML = `<div class="spinner"></div>`;

    try {
        const response = await fetch(`${API_BASE}/api/chat/${id}/history`);
        if (!response.ok) throw new Error('Could not get chat log');

        const history = await response.json();
        
        if (history.length === 0) {
            dom.chatHistoryLog.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); margin-top: 4rem;">
                    Start chatting! Ask any question about this document's contents.
                </div>`;
            return;
        }

        dom.chatHistoryLog.innerHTML = history.map(msg => {
            const senderName = msg.role === 'user' ? 'You' : 'Summarizerr AI';
            const bubbleContent = markdownToHTML(msg.content);
            return `
                <div class="message ${msg.role}">
                    <div class="message-sender">${senderName}</div>
                    <div class="message-bubble">${bubbleContent}</div>
                </div>
            `;
        }).join('');
        
        dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;
    } catch (err) {
        console.error(err);
        dom.chatHistoryLog.innerHTML = `<div style="text-align: center; color: var(--danger); padding: 2rem;">Failed to load chat history.</div>`;
    }
}

// Send chat message to API
async function sendChatMessage() {
    const id = state.activeDocumentId;
    const prompt = dom.chatPromptInput.value.trim();
    if (!prompt) return;

    // Clear input & append user message bubble to view immediately
    dom.chatPromptInput.value = '';
    
    // Remove blank welcome text if first msg
    if (dom.chatHistoryLog.querySelector('[style*="text-align: center"]')) {
        dom.chatHistoryLog.innerHTML = '';
    }

    dom.chatHistoryLog.innerHTML += `
        <div class="message user">
            <div class="message-sender">You</div>
            <div class="message-bubble"><p>${escapeHTML(prompt)}</p></div>
        </div>
    `;
    dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;

    // Append loading bubble
    const loadingId = 'chat-loading-' + Date.now();
    dom.chatHistoryLog.innerHTML += `
        <div class="message model" id="${loadingId}">
            <div class="message-sender">Summarizerr AI</div>
            <div class="message-bubble"><div class="spinner" style="margin: 0.5rem auto; width: 20px; height: 20px; border-width: 2px;"></div></div>
        </div>
    `;
    dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;

    const headers = { 'Content-Type': 'application/json' };
    const customGroqKey = dom.groqApiKeyInput.value.trim();
    if (customGroqKey) {
        headers['X-Groq-API-Key'] = customGroqKey;
    }

    try {
        const response = await fetch(`${API_BASE}/api/chat/${id}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ message: prompt })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to retrieve AI response');
        }

        const data = await response.json();
        
        // Remove typing indicator, append response
        const loaderBubble = document.getElementById(loadingId);
        if (loaderBubble) loaderBubble.remove();

        dom.chatHistoryLog.innerHTML += `
            <div class="message model">
                <div class="message-sender">Summarizerr AI</div>
                <div class="message-bubble">${markdownToHTML(data.response)}</div>
            </div>
        `;
        dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;

    } catch (err) {
        console.error(err);
        const loaderBubble = document.getElementById(loadingId);
        if (loaderBubble) loaderBubble.remove();
        
        showToast('Chat failed: ' + err.message, 'error');
        dom.chatHistoryLog.innerHTML += `
            <div class="message model" style="color: var(--danger);">
                <div class="message-sender">System</div>
                <div class="message-bubble"><p>Error: ${escapeHTML(err.message)}</p></div>
            </div>
        `;
        dom.chatHistoryLog.scrollTop = dom.chatHistoryLog.scrollHeight;
    }
}

// Download actions setup
function setupExportEvents() {
    dom.btnDownloadPdf.addEventListener('click', () => {
        window.open(`${API_BASE}/api/download/${state.activeDocumentId}/pdf`, '_blank');
    });

    dom.btnDownloadDocx.addEventListener('click', () => {
        window.open(`${API_BASE}/api/download/${state.activeDocumentId}/docx`, '_blank');
    });

    // Summary regeneration trigger
    dom.btnRegenerateSummary.addEventListener('click', async () => {
        const id = state.activeDocumentId;
        dom.btnRegenerateSummary.disabled = true;
        dom.summaryTextContainer.innerHTML = `<div class="spinner"></div><p style="text-align: center; color: var(--text-secondary);">Regenerating summary with Groq...</p>`;

        const headers = {};
        const customGroqKey = dom.groqApiKeyInput.value.trim();
        if (customGroqKey) {
            headers['X-Groq-API-Key'] = customGroqKey;
        }

        try {
            const response = await fetch(`${API_BASE}/api/summarize/${id}/regenerate`, {
                method: 'POST',
                headers: headers
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Summary regeneration failed');
            }

            const data = await response.json();
            if (data.summary_error) {
                showToast('Groq unavailable; local summary generated.', 'info');
            } else {
                showToast('Summary regenerated successfully!');
            }
            state.activeDocument.summary = data.summary;
            renderSummaryTab();
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
            // Restore previous summary
            renderSummaryTab();
        } finally {
            dom.btnRegenerateSummary.disabled = false;
        }
    });
}

// Basic markdown to HTML renderer
function markdownToHTML(md) {
    if (!md) return "";

    // Escape code blocks first to protect formatting
    let codeBlocks = [];
    md = md.replace(/```([\s\S]*?)```/g, (match, code) => {
        codeBlocks.push(code.trim());
        return `__CODE_BLOCK_PLACEHOLDER_${codeBlocks.length - 1}__`;
    });

    // Inline bolding & italics
    md = md.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    md = md.replace(/\*(.*?)\*/g, "<em>$1</em>");
    md = md.replace(/`(.*?)`/g, "<code style='background: rgba(255,255,255,0.06); padding: 0.1rem 0.3rem; border-radius: 4px;'>$1</code>");

    let lines = md.split('\n');
    let html = [];
    let listOpen = false;
    let tableOpen = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();

        // Code block placeholders
        if (line.includes('__CODE_BLOCK_PLACEHOLDER_')) {
            const idx = parseInt(line.match(/__CODE_BLOCK_PLACEHOLDER_(\d+)__/)[1]);
            html.push(`<pre style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 1rem 0; font-family: monospace; border: 1px solid var(--border-card);">${escapeHTML(codeBlocks[idx])}</pre>`);
            continue;
        }

        // List check
        if (line.startsWith('- ') || line.startsWith('* ')) {
            if (tableOpen) { html.push('</table>'); tableOpen = false; }
            if (!listOpen) {
                html.push('<ul style="margin-left: 1.5rem; margin-bottom: 1.5rem; list-style-type: disc;">');
                listOpen = true;
            }
            html.push(`<li style="margin-bottom: 0.4rem;">${line.substring(2)}</li>`);
            continue;
        }

        // Close list if line is not a list item
        if (listOpen && !line.startsWith('- ') && !line.startsWith('* ')) {
            html.push('</ul>');
            listOpen = false;
        }

        // Headers
        if (line.startsWith('#')) {
            if (tableOpen) { html.push('</table>'); tableOpen = false; }
            let level = 0;
            while (line[level] === '#') level++;
            let text = line.substring(level).trim();
            // Restrict headers styles
            html.push(`<h${level} style="color: var(--text-primary); margin: 1.5rem 0 0.8rem 0; font-weight: 700;">${text}</h${level}>`);
            continue;
        }

        // Tables
        if (line.startsWith('|')) {
            if (line.includes('---')) {
                continue; // Skip separation borders
            }
            let cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
            if (!tableOpen) {
                html.push('<table class="stats-table" style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">');
                tableOpen = true;
                html.push('<tr style="background: rgba(255, 255, 255, 0.04); font-weight: 600;">' + cells.map(c => `<th style="padding: 0.75rem 1rem; border: 1px solid var(--border-card); text-align: left;">${c}</th>`).join('') + '</tr>');
            } else {
                html.push('<tr>' + cells.map(c => `<td style="padding: 0.75rem 1rem; border: 1px solid var(--border-card); text-align: left;">${c}</td>`).join('') + '</tr>');
            }
            continue;
        }

        // Close table
        if (tableOpen && !line.startsWith('|')) {
            html.push('</table>');
            tableOpen = false;
        }

        // Empty spacer line
        if (line === "") {
            html.push('<br style="content: \'\'; display: block; margin: 0.5rem 0;">');
            continue;
        }

        // Normal paragraph
        html.push(`<p style="margin-bottom: 1.2rem; line-height: 1.6;">${line}</p>`);
    }

    if (listOpen) html.push('</ul>');
    if (tableOpen) html.push('</table>');

    return html.join('\n');
}

// Helpers
function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
