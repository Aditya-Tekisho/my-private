// WhatsApp Automation App JavaScript

const API_BASE = '';

// State
let contacts = [];
let messages = [];
let isAuthenticated = false;
let currentFilter = 'all';

// DOM Elements
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    messageForm: document.getElementById('messageForm'),
    contactInput: document.getElementById('contactInput'),
    contactSuggestions: document.getElementById('contactSuggestions'),
    messageInput: document.getElementById('messageInput'),
    scheduleCheck: document.getElementById('scheduleCheck'),
    scheduleOptions: document.getElementById('scheduleOptions'),
    scheduleDate: document.getElementById('scheduleDate'),
    scheduleBtn: document.getElementById('scheduleBtn'),
    contactSearch: document.getElementById('contactSearch'),
    contactsList: document.getElementById('contactsList'),
    refreshContacts: document.getElementById('refreshContacts'),
    messageList: document.getElementById('messageList'),
    connectBtn: document.getElementById('connectBtn'),
    disconnectBtn: document.getElementById('disconnectBtn'),
    qrModal: document.getElementById('qrModal'),
    qrImage: document.getElementById('qrImage'),
    qrStatus: document.getElementById('qrStatus'),
    closeQr: document.getElementById('closeQr'),
    toastContainer: document.getElementById('toastContainer'),
};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthStatus();
    setupEventListeners();
    setupNavigation();
    startAuthPolling();
});

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        isAuthenticated = data.is_authenticated;
        updateConnectionStatus();
    } catch (error) {
        console.error('Failed to check auth status:', error);
    }
}

// Update connection status display
function updateConnectionStatus() {
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');
    
    if (isAuthenticated) {
        statusDot.className = 'status-dot connected';
        statusText.textContent = 'Connected';
        elements.connectBtn.style.display = 'none';
        elements.disconnectBtn.style.display = 'inline-flex';
        loadContacts();
        loadMessageHistory();
    } else {
        statusDot.className = 'status-dot disconnected';
        statusText.textContent = 'Disconnected';
        elements.connectBtn.style.display = 'inline-flex';
        elements.disconnectBtn.style.display = 'none';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Message form
    elements.messageForm.addEventListener('submit', handleSendMessage);
    elements.scheduleBtn.addEventListener('click', handleScheduleMessage);
    
    // Schedule checkbox
    elements.scheduleCheck.addEventListener('change', (e) => {
        elements.scheduleOptions.style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Contact input
    elements.contactInput.addEventListener('input', handleContactInput);
    elements.contactInput.addEventListener('focus', () => {
        if (contacts.length > 0) {
            showContactSuggestions();
        }
    });
    elements.contactInput.addEventListener('blur', () => {
        setTimeout(() => {
            elements.contactSuggestions.classList.remove('show');
        }, 200);
    });
    
    // Contact search
    elements.contactSearch.addEventListener('input', handleContactSearch);
    elements.refreshContacts.addEventListener('click', loadContacts);
    
    // Filter tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFilter = tab.dataset.filter;
            renderMessages();
        });
    });
    
    // QR modal
    elements.connectBtn.addEventListener('click', showQRModal);
    elements.closeQr.addEventListener('click', hideQRModal);
    elements.disconnectBtn.addEventListener('click', handleDisconnect);
    
    elements.qrModal.addEventListener('click', (e) => {
        if (e.target === elements.qrModal) {
            hideQRModal();
        }
    });
}

// Setup navigation
function setupNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view');
    
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const viewId = btn.dataset.view + 'View';
            
            // Update active state
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show appropriate view
            views.forEach(view => {
                view.classList.remove('active');
            });
            document.getElementById(viewId).classList.add('active');
            
            // Load data for view
            if (btn.dataset.view === 'contacts') {
                loadContacts();
            } else if (btn.dataset.view === 'history') {
                loadMessageHistory();
            }
        });
    });
}

// Auth polling
let authPollInterval;
function startAuthPolling() {
    authPollInterval = setInterval(async () => {
        if (!isAuthenticated) {
            await checkAuthStatus();
        }
    }, 5000);
}

// Handle send message
async function handleSendMessage(e) {
    e.preventDefault();
    
    if (!isAuthenticated) {
        showToast('Please connect to WhatsApp first', 'error');
        return;
    }
    
    const phone = elements.contactInput.value.trim();
    const message = elements.messageInput.value.trim();
    
    if (!phone || !message) {
        showToast('Please enter both phone and message', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, message }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Message sent successfully!', 'success');
            elements.messageForm.reset();
            loadMessageHistory();
        } else {
            showToast(data.message || 'Failed to send message', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Handle schedule message
async function handleScheduleMessage() {
    if (!isAuthenticated) {
        showToast('Please connect to WhatsApp first', 'error');
        return;
    }
    
    const phone = elements.contactInput.value.trim();
    const message = elements.messageInput.value.trim();
    const scheduledAt = elements.scheduleDate.value;
    
    if (!phone || !message) {
        showToast('Please enter both phone and message', 'error');
        return;
    }
    
    if (!scheduledAt) {
        showToast('Please select a date and time', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/messages/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone,
                message,
                scheduled_at: new Date(scheduledAt).toISOString(),
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Message scheduled!', 'success');
            elements.messageForm.reset();
            elements.scheduleCheck.checked = false;
            elements.scheduleOptions.style.display = 'none';
            loadMessageHistory();
        } else {
            showToast(data.message || 'Failed to schedule message', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Handle contact input
function handleContactInput(e) {
    const query = e.target.value.toLowerCase();
    
    if (query.length < 1) {
        elements.contactSuggestions.classList.remove('show');
        return;
    }
    
    const filtered = contacts.filter(c =>
        c.name.toLowerCase().includes(query) ||
        c.phone.includes(query)
    );
    
    if (filtered.length > 0) {
        renderContactSuggestions(filtered);
        elements.contactSuggestions.classList.add('show');
    } else {
        elements.contactSuggestions.classList.remove('show');
    }
}

// Show contact suggestions
function showContactSuggestions() {
    if (contacts.length > 0) {
        renderContactSuggestions(contacts.slice(0, 10));
        elements.contactSuggestions.classList.add('show');
    }
}

// Render contact suggestions
function renderContactSuggestions(contactList) {
    elements.contactSuggestions.innerHTML = contactList.map(c => `
        <div class="contact-suggestion" data-phone="${c.phone}" data-name="${c.name}">
            <div class="name">${c.name}</div>
            <div class="phone">${c.phone}</div>
        </div>
    `).join('');
    
    // Add click handlers
    elements.contactSuggestions.querySelectorAll('.contact-suggestion').forEach(el => {
        el.addEventListener('click', () => {
            elements.contactInput.value = el.dataset.phone;
            elements.contactSuggestions.classList.remove('show');
        });
    });
}

// Handle contact search
function handleContactSearch(e) {
    const query = e.target.value.toLowerCase();
    
    if (!query) {
        renderContacts();
        return;
    }
    
    const filtered = contacts.filter(c =>
        c.name.toLowerCase().includes(query) ||
        c.phone.includes(query)
    );
    
    renderContacts(filtered);
}

// Load contacts
async function loadContacts() {
    if (!isAuthenticated) return;
    
    try {
        const response = await fetch('/api/contacts');
        contacts = await response.json();
        renderContacts();
    } catch (error) {
        console.error('Failed to load contacts:', error);
    }
}

// Render contacts
function renderContacts(contactList = contacts) {
    if (contactList.length === 0) {
        elements.contactsList.innerHTML = '<p class="empty-state">No contacts found</p>';
        return;
    }
    
    elements.contactsList.innerHTML = contactList.map(c => `
        <div class="contact-item" data-phone="${c.phone}">
            <div class="contact-avatar">${c.name.charAt(0).toUpperCase()}</div>
            <div class="contact-info">
                <div class="contact-name">${c.name}</div>
                <div class="contact-phone">${c.phone}</div>
            </div>
        </div>
    `).join('');
    
    // Add click handlers
    elements.contactsList.querySelectorAll('.contact-item').forEach(el => {
        el.addEventListener('click', () => {
            elements.contactInput.value = el.dataset.phone;
            // Switch to compose view
            document.querySelector('[data-view="compose"]').click();
        });
    });
}

// Load message history
async function loadMessageHistory() {
    try {
        const response = await fetch('/api/messages/history');
        messages = await response.json();
        renderMessages();
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

// Render messages
function renderMessages() {
    let filtered = messages;
    
    if (currentFilter !== 'all') {
        filtered = messages.filter(m => m.status === currentFilter);
    }
    
    if (filtered.length === 0) {
        elements.messageList.innerHTML = '<p class="empty-state">No messages yet</p>';
        return;
    }
    
    elements.messageList.innerHTML = filtered.map(m => `
        <div class="message-item">
            <div class="message-header">
                <span class="message-to">${m.contact_name}</span>
                <span class="message-status ${m.status}">${m.status}</span>
            </div>
            <div class="message-content">${m.content}</div>
            <div class="message-time">${formatDate(m.created_at)}</div>
        </div>
    `).join('');
}

// Show QR modal
async function showQRModal() {
    elements.qrModal.classList.add('show');
    elements.qrStatus.textContent = 'Fetching QR code...';
    elements.qrImage.innerHTML = '<div class="spinner"></div>';
    
    try {
        const response = await fetch('/api/auth/qr', { method: 'POST' });
        const data = await response.json();
        
        if (data.qr_code) {
            elements.qrImage.innerHTML = `<img src="data:image/png;base64,${data.qr_code}" alt="QR Code">`;
            elements.qrStatus.textContent = 'Scan with WhatsApp';
            startQRPolling();
        } else if (data.is_authenticated) {
            hideQRModal();
            isAuthenticated = true;
            updateConnectionStatus();
            showToast('Already connected!', 'success');
        }
    } catch (error) {
        elements.qrStatus.textContent = 'Error: ' + error.message;
    }
}

// Hide QR modal
function hideQRModal() {
    elements.qrModal.classList.remove('show');
    stopQRPolling();
}

// QR polling
let qrPollInterval;
function startQRPolling() {
    qrPollInterval = setInterval(checkQRStatus, 3000);
}

function stopQRPolling() {
    if (qrPollInterval) {
        clearInterval(qrPollInterval);
        qrPollInterval = null;
    }
}

// Check QR status
async function checkQRStatus() {
    try {
        const response = await fetch('/api/auth/check', { method: 'POST' });
        const data = await response.json();
        
        if (data.is_authenticated) {
            isAuthenticated = true;
            hideQRModal();
            updateConnectionStatus();
            showToast('Connected to WhatsApp!', 'success');
            stopQRPolling();
        }
    } catch (error) {
        console.error('QR check error:', error);
    }
}

// Handle disconnect
async function handleDisconnect() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        isAuthenticated = false;
        contacts = [];
        messages = [];
        updateConnectionStatus();
        showToast('Disconnected from WhatsApp', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

// Show toast
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
        <span class="toast-message">${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}