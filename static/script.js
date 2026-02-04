/* ============================================
   Sinhala-English Idiom Translator JavaScript
   ============================================ */

// API Base URL
const API_URL = '';

// Translation direction state
let translationDirection = 'en-si'; // 'en-si' or 'si-en'

const LANGUAGES = {
    en: {
        code: 'en',
        name: 'English',
        flag: 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f1ec-1f1e7.svg',
        placeholder: 'Enter English text...'
    },
    si: {
        code: 'si',
        name: 'Sinhala (සිංහල)',
        flag: 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f1f1-1f1f0.svg',
        placeholder: 'සිංහල පෙළ ඇතුළත් කරන්න...'
    }
};

// ============================================
// Section Navigation
// ============================================

function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    
    // Show selected section
    document.getElementById(`${section}-section`).classList.add('active');
    event.target.classList.add('active');
    
    // Load idiom list if needed
    if (section === 'idiom-list') {
        loadIdiomList();
    }
}

// ============================================
// Language Swap Function
// ============================================

function swapLanguages() {
    // Toggle direction
    translationDirection = translationDirection === 'en-si' ? 'si-en' : 'en-si';
    
    // Get current source and target
    const sourceLang = translationDirection === 'en-si' ? 'en' : 'si';
    const targetLang = translationDirection === 'en-si' ? 'si' : 'en';
    
    // Update UI
    const sourceContainer = document.getElementById('source-lang-container');
    const targetContainer = document.getElementById('target-lang-container');
    
    // Update source language button
    const sourceLangInfo = LANGUAGES[sourceLang];
    sourceContainer.querySelector('.lang-btn').setAttribute('data-lang', sourceLang);
    sourceContainer.querySelector('.logo-icon').src = sourceLangInfo.flag;
    sourceContainer.querySelector('.lang-text').textContent = sourceLangInfo.name;
    
    // Update target language button
    const targetLangInfo = LANGUAGES[targetLang];
    targetContainer.querySelector('.lang-btn').setAttribute('data-lang', targetLang);
    targetContainer.querySelector('.logo-icon').src = targetLangInfo.flag;
    targetContainer.querySelector('.lang-text').textContent = targetLangInfo.name;
    
    // Update placeholder
    const sourceTextArea = document.getElementById('source-text');
    sourceTextArea.placeholder = sourceLangInfo.placeholder;
    
    // Swap text content if both boxes have content
    const outputDiv = document.getElementById('translation-output');
    const outputText = outputDiv.textContent.trim();
    
    if (sourceTextArea.value.trim() && outputText && outputText !== 'Translation will appear here...') {
        const temp = sourceTextArea.value;
        sourceTextArea.value = outputText;
        outputDiv.innerHTML = temp;
        
        // Update char count
        document.getElementById('char-count').textContent = sourceTextArea.value.length;
    }
    
    // Clear idioms and method badges
    document.getElementById('detected-idioms').classList.add('hidden');
    document.getElementById('method-badge').classList.add('hidden');
    
    showToast(`Switched to ${sourceLangInfo.name} → ${targetLangInfo.name}`);
}

// ============================================
// Translation Functions
// ============================================

async function doTranslate() {
    const sourceText = document.getElementById('source-text').value.trim();
    
    if (!sourceText) {
        showToast('Please enter text to translate');
        return;
    }
    
    // Show loading state
    const btn = document.getElementById('translate-btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btn.disabled = true;
    btnText.textContent = 'Translating...';
    btnLoader.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: sourceText,
                direction: translationDirection 
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle HTTP errors (400, 500, etc.)
            const errorMsg = data.error || `Translation failed (${response.status})`;
            showToast(errorMsg, 5000);
            return;
        }
        
        if (data.success) {
            // Show translation
            displayTranslation(data);
        } else {
            showToast(data.error || 'Translation failed', 5000);
        }
    } catch (error) {
        console.error('Translation error:', error);
        showToast('Connection error. Make sure the server is running.', 5000);
    } finally {
        // Reset button
        btn.disabled = false;
        btnText.textContent = 'Translate';
        btnLoader.classList.add('hidden');
    }
}

function displayTranslation(data) {
    // Show translation
    const output = document.getElementById('translation-output');
    output.innerHTML = data.translation;
    
    // Show detected idioms
    const idiomsContainer = document.getElementById('detected-idioms');
    const idiomTags = document.getElementById('idiom-tags');
    
    if (data.idioms && data.idioms.length > 0) {
        idiomsContainer.classList.remove('hidden');
        idiomTags.innerHTML = data.idioms.map(idiom => `
            <span class="idiom-tag">
                <span class="english">${idiom.english}</span>
                <span class="arrow">→</span>
                <span class="sinhala">${idiom.sinhala}</span>
            </span>
        `).join('');
    } else {
        idiomsContainer.classList.add('hidden');
    }
    
    // Show method badge
    const methodBadge = document.getElementById('method-badge');
    methodBadge.classList.remove('hidden');
    methodBadge.textContent = data.method === 'hybrid' ? '🔀 Hybrid' : '🤖 NLLB';
    
    // Show accuracy badge
    const accuracyBadge = document.getElementById('accuracy-badge');
    if (data.idioms && data.idioms.length > 0) {
        accuracyBadge.classList.remove('hidden');
        // const accuracy = Math.round(data.idiom_accuracy * 100);
        // accuracyBadge.textContent = `✓ ${accuracy}% Idiom Accuracy`;
    } else {
        accuracyBadge.classList.add('hidden');
    }
}

// ============================================
// Idiom Detection (Real-time)
// ============================================

let detectTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
    const sourceText = document.getElementById('source-text');
    
    sourceText.addEventListener('input', () => {
        // Update character count
        const count = sourceText.value.length;
        document.getElementById('char-count').textContent = count;
        
        // Debounced idiom detection
        clearTimeout(detectTimeout);
        detectTimeout = setTimeout(() => {
            detectIdioms(sourceText.value);
        }, 500);
    });
    
    // Enter key to translate
    sourceText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            translate();
        }
    });
});

async function detectIdioms(text) {
    if (!text.trim()) {
        document.getElementById('detected-idioms').classList.add('hidden');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/detect-idioms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        if (data.success && data.idioms.length > 0) {
            const idiomsContainer = document.getElementById('detected-idioms');
            const idiomTags = document.getElementById('idiom-tags');
            
            idiomsContainer.classList.remove('hidden');
            idiomTags.innerHTML = data.idioms.map(idiom => `
                <span class="idiom-tag">
                    <span class="english">${idiom.english}</span>
                    <span class="arrow">→</span>
                    <span class="sinhala">${idiom.sinhala}</span>
                </span>
            `).join('');
        } else {
            document.getElementById('detected-idioms').classList.add('hidden');
        }
    } catch (error) {
        // Silently fail for detection
        console.log('Idiom detection not available');
    }
}

// ============================================
// Utility Functions
// ============================================

function clearInput() {
    document.getElementById('source-text').value = '';
    document.getElementById('char-count').textContent = '0';
    document.getElementById('detected-idioms').classList.add('hidden');
    document.getElementById('translation-output').innerHTML = '<span class="placeholder-text">Translation will appear here...</span>';
    document.getElementById('method-badge').classList.add('hidden');
    document.getElementById('accuracy-badge').classList.add('hidden');
}

function copyTranslation() {
    const output = document.getElementById('translation-output');
    const text = output.innerText;
    
    if (!text || text === 'Translation will appear here...') {
        showToast('Nothing to copy');
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(() => {
        showToast('Failed to copy');
    });
}

function useExample(button) {
    const text = button.textContent.trim();
    document.getElementById('source-text').value = text;
    document.getElementById('char-count').textContent = text.length;
    detectIdioms(text);
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, duration);
}

// ============================================
// Idiom Dictionary
// ============================================

let allIdioms = [];

async function loadIdiomList() {
    const container = document.getElementById('idiom-dictionary');
    
    if (allIdioms.length > 0) {
        renderIdiomList(allIdioms);
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/idiom-list`);
        const data = await response.json();
        
        if (data.success) {
            allIdioms = data.idioms;
            renderIdiomList(allIdioms);
        } else {
            container.innerHTML = '<p class="loading">Failed to load idioms</p>';
        }
    } catch (error) {
        container.innerHTML = '<p class="loading">Error loading idioms. Make sure the server is running.</p>';
    }
}

function renderIdiomList(idioms) {
    const container = document.getElementById('idiom-dictionary');
    
    if (idioms.length === 0) {
        container.innerHTML = '<p class="loading">No idioms found</p>';
        return;
    }
    
    container.innerHTML = idioms.map(idiom => `
        <div class="idiom-card">
            <span class="english">${idiom.english}</span>
            <span class="arrow">→</span>
            <span class="sinhala">${idiom.sinhala}</span>
        </div>
    `).join('');
}

function filterIdioms() {
    const search = document.getElementById('idiom-search').value.toLowerCase();
    
    if (!search) {
        renderIdiomList(allIdioms);
        return;
    }
    
    const filtered = allIdioms.filter(idiom => 
        idiom.english.toLowerCase().includes(search) ||
        idiom.sinhala.includes(search)
    );
    
    renderIdiomList(filtered);
}
