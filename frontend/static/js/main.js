/* ==================== */
/* Main JavaScript */
/* ==================== */

// State Management
const AppState = {
    user: null,
    language: localStorage.getItem('language') || 'en',
    theme: localStorage.getItem('theme') || 'light',
    currentPage: 'home'
};

// ==================== */
// Centralized Language Config
// ==================== */

// Maps app language codes to BCP-47 speech codes (used by SpeechRecognition + SpeechSynthesis)
const LANGUAGE_MAP = {
    en: 'en-US',
    hi: 'hi-IN',
    te: 'te-IN',
    ta: 'ta-IN',
    kn: 'kn-IN',
    ml: 'ml-IN'
};

// Translations
const translations = {
    en: {
        'nav.home': 'Home',
        'nav.schemes': 'Schemes',
        'nav.eligibility': 'Eligibility',
        'nav.apply': 'Apply',
        'nav.documents': 'Documents',
        'nav.dashboard': 'Dashboard',
        'nav.profile': 'My Profile',
        'nav.chat': 'AI Assistant',
        'nav.about': 'About',
        'nav.contact': 'Contact',
        'nav.login': 'Login',
        'nav.logout': 'Logout',
        'btn.getStarted': 'Get Started',
        'btn.learnMore': 'Learn More',
        'hero.title': 'Find government schemes in your language',
        'hero.subtitle': 'Your AI-powered multilingual assistant for discovering and applying to government welfare schemes.'
    },
    hi: {
        'nav.home': 'होम',
        'nav.schemes': 'योजनाएं',
        'nav.eligibility': 'पात्रता',
        'nav.apply': 'आवेदन',
        'nav.documents': 'दस्तावेज',
        'nav.dashboard': 'डैशबोर्ड',
        'nav.profile': 'मेरी प्रोफाइल',
        'nav.chat': 'AI सहायक',
        'nav.about': 'हमारे बारे में',
        'nav.contact': 'संपर्क',
        'nav.login': 'लॉगिन',
        'nav.logout': 'लॉगआउट',
        'btn.getStarted': 'शुरू करें',
        'btn.learnMore': 'और जानें',
        'hero.title': 'अपनी भाषा में सरकारी योजनाएं खोजें',
        'hero.subtitle': 'सरकारी कल्याणकारी योजनाओं की खोज और आवेदन के लिए आपका AI-संचालित बहुभाषी सहायक।'
    },
    ta: {
        'nav.home': 'முகப்பு',
        'nav.schemes': 'திட்டங்கள்',
        'nav.eligibility': 'தகுதி',
        'nav.apply': 'விண்ணப்பி',
        'nav.documents': 'ஆவணங்கள்',
        'nav.dashboard': 'டாஷ்போர்டு',
        'nav.profile': 'என் சுயவிவரம்',
        'nav.chat': 'AI உதவியாளர்',
        'nav.about': 'எங்களை பற்றி',
        'nav.contact': 'தொடர்பு',
        'nav.login': 'உள்நுழை',
        'nav.logout': 'வெளியேறு',
        'btn.getStarted': 'தொடங்கு',
        'btn.learnMore': 'மேலும் அறிக',
        'hero.title': 'உங்கள் மொழியில் அரசு திட்டங்களைக் கண்டறியவும்',
        'hero.subtitle': 'அரசு நல்வாழ்வுத் திட்டங்களைக் கண்டறிந்து விண்ணப்பிப்பதற்கு உங்கள் AI-இயக்கப்படும் பல மொழி உதவியாளர்.'
    },
    te: {
        'nav.home': 'హోమ్',
        'nav.schemes': 'పథకాలు',
        'nav.eligibility': 'అర్హత',
        'nav.apply': 'దరఖాస్తు',
        'nav.documents': 'పత్రాలు',
        'nav.dashboard': 'డాష్‌బోర్డ్',
        'nav.profile': 'నా ప్రొఫైల్',
        'nav.chat': 'AI సహాయకుడు',
        'nav.about': 'మా గురించి',
        'nav.contact': 'సంప్రదించండి',
        'nav.login': 'లాగిన్',
        'nav.logout': 'లాగ్అవుట్',
        'btn.getStarted': 'ప్రారంభించండి',
        'btn.learnMore': 'మరింత తెలుసుకోండి',
        'hero.title': 'మీ భాషలో ప్రభుత్వ పథకాలను కనుగొనండి',
        'hero.subtitle': 'ప్రభుత్వ సంక్షేమ పథకాలను కనుగొనడానికి మరియు దరఖాస్తు చేయడానికి మీ AI ఆధారిత బహుభాషా సహాయకుడు.'
    },
    kn: {
        'nav.home': 'ಮುಖಪುಟ',
        'nav.schemes': 'योजनाएं',
        'nav.eligibility': 'ಅರ್ಹತೆ',
        'nav.apply': 'ಅರ್ಜಿ ಸಲ್ಲಿಸಿ',
        'nav.documents': 'ದಾಖಲೆಗಳು',
        'nav.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
        'nav.profile': 'ನನ್ನ ಪ್ರೊಫೈಲ್',
        'nav.chat': 'AI ಸಹಾಯಕ',
        'nav.about': 'ನಮ್ಮ ಬಗ್ಗೆ',
        'nav.contact': 'ಸಂಪರ್ಕಿಸಿ',
        'nav.login': 'ಲಾಗಿನ್',
        'nav.logout': 'ಲಾಗ್ಔಟ್',
        'btn.getStarted': 'ಪ್ರಾರಂಭಿಸಿ',
        'btn.learnMore': 'ಇನ್ನಷ್ಟು ತಿಳಿಯಿರಿ',
        'hero.title': 'ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ',
        'hero.subtitle': 'ಸರ್ಕಾರಿ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ನಿಮ್ಮ AI-ಚಾಲಿತ ಬಹುಭಾಷಾ ಸಹಾಯಕ.'
    },
    ml: {
        'nav.home': 'ഹോം',
        'nav.schemes': 'പദ്ധതികൾ',
        'nav.eligibility': 'യോഗ്യത',
        'nav.apply': 'അപേക്ഷിക്കുക',
        'nav.documents': 'രേഖകൾ',
        'nav.dashboard': 'ഡാഷ്ബോർഡ്',
        'nav.profile': 'എന്റെ പ്രൊഫൈൽ',
        'nav.chat': 'AI സഹായി',
        'nav.about': 'ഞങ്ങളെക്കുറിച്ച്',
        'nav.contact': 'ബന്ധപ്പെടുക',
        'nav.login': 'ലോഗിൻ',
        'nav.logout': 'ലോഗ്ഔട്ട്',
        'btn.getStarted': 'ആരംഭിക്കുക',
        'btn.learnMore': 'കൂടുതൽ അറിയുക',
        'hero.title': 'നിങ്ങളുടെ ഭാഷയിൽ സർക്കാർ പദ്ധതികൾ കണ്ടെത്തുക',
        'hero.subtitle': 'സർക്കാർ ക്ഷേമ പദ്ധതികൾ കണ്ടെത്താനും അപേക്ഷിക്കാനുമുള്ള നിങ്ങളുടെ AI പ്രവർത്തിത ബഹുഭാഷാ സഹായി.'
    }
};

// Utility Functions
function t(key) {
    return (translations[AppState.language] && translations[AppState.language][key]) || translations.en[key] || key;
}

function setLanguage(lang) {
    if (!LANGUAGE_MAP[lang]) {
        console.warn(`Unsupported language "${lang}", falling back to English`);
        lang = 'en';
    }
    AppState.language = lang;
    localStorage.setItem('language', lang);
    updateTranslations();
    document.dispatchEvent(new CustomEvent('languagechange', { detail: { language: lang } }));
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', AppState.theme);
    document.documentElement.classList.toggle('dark', AppState.theme === 'dark');
}

function updateTranslations() {
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        element.textContent = t(key);
    });
}

// ==================== */
// Centralized Speech Service
// Single source of truth for SpeechRecognition setup + error handling.
// Any file needing voice input should use SpeechService.createRecognition()
// instead of instantiating its own SpeechRecognition object.
// ==================== */
const SpeechService = {
    getLangCode(lang) {
        return LANGUAGE_MAP[lang || AppState.language] || 'en-US';
    },
    isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    },
    mediaRecorder: null,
    audioChunks: [],
    audioStream: null,
    async startRecording() {
        if (!this.isSupported()) {
            throw new Error('Audio recording is not supported in this browser.');
        }
        this.audioChunks = [];
        this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        let options = {};
        if (MediaRecorder.isTypeSupported('audio/webm')) {
            options.mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            options.mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
            options.mimeType = 'audio/ogg';
        } else if (MediaRecorder.isTypeSupported('audio/wav')) {
            options.mimeType = 'audio/wav';
        }

        this.mediaRecorder = new MediaRecorder(this.audioStream, options);
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        this.mediaRecorder.start(200);
    },
    stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder) {
                reject(new Error('No active recording session.'));
                return;
            }
            this.mediaRecorder.onstop = async () => {
                try {
                    const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
                    const audioBlob = new Blob(this.audioChunks, { type: mimeType });

                    if (this.audioStream) {
                        this.audioStream.getTracks().forEach(track => track.stop());
                        this.audioStream = null;
                    }
                    this.mediaRecorder = null;
                    this.audioChunks = [];
                    resolve(audioBlob);
                } catch (error) {
                    reject(error);
                }
            };
            this.mediaRecorder.stop();
        });
    },
    speak(text) {
        if (!('speechSynthesis' in window)) return false;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.getLangCode();
        speechSynthesis.speak(utterance);
        return true;
    }
};

// ==================== */
// Centralized voice navigation commands (multilingual)
// Each route maps to keyword arrays across all supported languages.
// ==================== */
const NAV_COMMANDS = [
    { route: '/', keywords: ['home', 'होम', 'முகப்பு', 'హోమ్', 'ಮುಖಪುಟ', 'ഹോം'] },
    { route: '/schemes/', keywords: ['scheme', 'योजना', 'திட்ட', 'పథక', 'ಯೋಜನೆ', 'പദ്ധതി'] },
    { route: '/eligibility/', keywords: ['eligibility', 'पात्रता', 'தகுதி', 'అర్హత', 'ಅರ್ಹತೆ', 'യോഗ്യത'] },
    { route: '/application/', keywords: ['apply', 'application', 'आवेदन', 'விண்ணப்ப', 'దరఖాస్తు', 'ಅರ್ಜಿ', 'അപേക്ഷ'] },
    { route: '/documents/', keywords: ['document', 'दस्तावेज', 'ஆவணங்கள்', 'పత్రాలు', 'ದಾಖಲೆ', 'രേഖ'] },
    { route: '/dashboard/', keywords: ['dashboard', 'डैशबोर्ड', 'டாஷ்போர்டு', 'డాష్‌బోర్డ్', 'ಡ್ಯಾಶ್\u200cಬೋರ್ഡ്', 'ഡാഷ്ബോർഡ്'] },
    { route: '/profile/', keywords: ['profile', 'प्रोफाइल', 'சுயவிவரம்', 'ప్రొఫైల్', 'ಪ್ರೊಫೈಲ್', 'പ്രൊഫൈൽ'] },
    { route: '/chat/', keywords: ['chat', 'assistant', 'सहायक', 'உதவியாளர்', 'సహాయకుడు', 'ಸಹಾಯಕ', 'സഹായി'] },
    { route: '/about/', keywords: ['about', 'हमारे बारे में', 'எங்களை', 'మా గురించి', 'ನಮ್ಮ గురించి', 'ഞങ്ങളെക്കുറിച്ച്'] },
    { route: '/contact/', keywords: ['contact', 'संपर्क', 'தொடர்பு', 'సంప్రదించండి', 'ಸಂಪರ್ಕ', 'ബന്ധപ്പെടുക'] },
    { route: '/login/', keywords: ['login', 'लॉगिन', 'உள்நுழை', 'లాగిన్', 'ಲಾಗಿನ್', 'ലോഗിൻ'] }
];

// Returns a matching route for a spoken command, or null if none match.
function matchVoiceCommand(transcript) {
    const command = transcript.toLowerCase();
    for (const entry of NAV_COMMANDS) {
        if (entry.keywords.some(keyword => command.includes(keyword.toLowerCase()))) {
            return entry.route;
        }
    }
    return null;
}

// API Service
const API = {
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        if (AppState.user?.token) {
            defaultOptions.headers.Authorization = `Bearer ${AppState.user.token}`;
        }
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (response.status === 401) {
                localStorage.removeItem('user');
                AppState.user = null;
                const protectedPaths = ['/dashboard/', '/profile/', '/application/', '/documents/', '/chat/', '/eligibility/'];
                const currentPath = window.location.pathname;
                const isProtected = protectedPaths.some(path => {
                    return currentPath === path || currentPath === path.replace(/\/$/, '') || currentPath === path + '/';
                });
                if (isProtected) {
                    window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
                    return;
                }
            }
            
            let data = {};
            const text = await response.text();
            if (text) {
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    data = { message: text };
                }
            }
            
            if (!response.ok) {
                throw new Error(data.message || 'Something went wrong');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    async get(url) {
        return this.request(url, { method: 'GET' });
    },
    
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async patch(url, data) {
        return this.request(url, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },
    
    // For file/FormData uploads — no JSON.stringify, no Content-Type override
    // (the browser sets the multipart boundary automatically).
    async postForm(url, formData) {
        const headers = {};
        if (AppState.user?.token) {
            headers.Authorization = `Bearer ${AppState.user.token}`;
        }
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData
            });
            
            if (response.status === 401) {
                localStorage.removeItem('user');
                AppState.user = null;
                const protectedPaths = ['/dashboard/', '/profile/', '/application/', '/documents/', '/chat/', '/eligibility/'];
                const currentPath = window.location.pathname;
                const isProtected = protectedPaths.some(path => {
                    return currentPath === path || currentPath === path.replace(/\/$/, '') || currentPath === path + '/';
                });
                if (isProtected) {
                    window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
                    return;
                }
            }
            
            let data = {};
            const text = await response.text();
            if (text) {
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    data = { message: text };
                }
            }
            
            if (!response.ok) {
                throw new Error(data.message || 'Something went wrong');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// Form Validation
const Validator = {
    required(value) {
        return value && value.trim().length > 0;
    },
    
    email(value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value);
    },
    
    minLength(value, min) {
        return value && value.length >= min;
    },
    
    maxLength(value, max) {
        return value && value.length <= max;
    },
    
    phone(value) {
        const phoneRegex = /^[6-9]\d{9}$/;
        return phoneRegex.test(value);
    },
    
    aadhaar(value) {
        const aadhaarRegex = /^\d{12}$/;
        return aadhaarRegex.test(value);
    },
    
    validate(form, rules) {
        const errors = {};
        let isValid = true;
        
        for (const field in rules) {
            // Supports both a live <form> element (form[field] is an input with .value)
            // and a plain data object (form[field] is already the value).
            const raw = form[field];
            const value = (raw && typeof raw === 'object' && 'value' in raw) ? raw.value : (raw ?? '');
            const fieldRules = rules[field];
            
            for (const rule of fieldRules) {
                if (rule.type === 'required' && !this.required(value)) {
                    errors[field] = rule.message || `${field} is required`;
                    isValid = false;
                    break;
                }
                
                if (rule.type === 'email' && !this.email(value)) {
                    errors[field] = rule.message || 'Invalid email address';
                    isValid = false;
                    break;
                }
                
                if (rule.type === 'minLength' && !this.minLength(value, rule.min)) {
                    errors[field] = rule.message || `Minimum ${rule.min} characters required`;
                    isValid = false;
                    break;
                }
                
                if (rule.type === 'phone' && !this.phone(value)) {
                    errors[field] = rule.message || 'Invalid phone number';
                    isValid = false;
                    break;
                }
                
                if (rule.type === 'aadhaar' && !this.aadhaar(value)) {
                    errors[field] = rule.message || 'Invalid Aadhaar number';
                    isValid = false;
                    break;
                }
            }
        }
        
        return { isValid, errors };
    }
};

// Toast Notifications
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.innerHTML = `
        <i class="fa-solid fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '10000';
    toast.style.minWidth = '300px';
    toast.style.animation = 'slideRight 0.3s ease-out';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Modal
function Modal(content, options = {}) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'card';
    modalContent.style.cssText = `
        max-width: ${options.maxWidth || '500px'};
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        animation: scaleIn 0.2s ease-out;
    `;
    
    modalContent.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            ${options.title ? `<h3>${options.title}</h3>` : ''}
            <button class="modal-close" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">&times;</button>
        </div>
        ${content}
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close handlers
    const close = () => {
        modal.style.animation = 'fadeOut 0.2s ease-out';
        setTimeout(() => modal.remove(), 200);
    };
    
    modal.querySelector('.modal-close').addEventListener('click', close);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) close();
    });
    
    if (options.onClose) {
        modal.addEventListener('close', options.onClose);
    }
    
    return { close };
}

// Shared debounce utility (was previously duplicated locally in schemes.js)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Load saved theme
    if (AppState.theme === 'dark') {
        document.documentElement.classList.add('dark');
    }
    
    // Load saved user
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        AppState.user = JSON.parse(savedUser);
        
        // Enforce boundary: Admins cannot access citizen/public pages, they are redirected to /admin-dashboard/
        if (AppState.user && AppState.user.role === 'admin') {
            const currentPath = window.location.pathname;
            const forbiddenForAdmins = ['/', '/schemes/', '/dashboard/', '/profile/', '/eligibility/', '/application/', '/documents/', '/chat/'];
            const isForbidden = forbiddenForAdmins.some(p => {
                if (p === '/') return currentPath === '/';
                return currentPath.startsWith(p) || currentPath === p;
            });
            if (isForbidden) {
                window.location.href = '/admin-dashboard/';
                return;
            }
        }
    }
    
    // Initialize language selector
    const languageSelect = document.getElementById('language');
    if (languageSelect) {
        languageSelect.value = AppState.language;
        languageSelect.addEventListener('change', (e) => {
            setLanguage(e.target.value);
        });
    }
    
    // Update translations
    updateTranslations();
    
    // Add smooth scroll behavior for anchor links only
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            // Only prevent default and smooth scroll if href is actually an anchor
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
});

// Export for use in other files
window.AppState = AppState;
window.LANGUAGE_MAP = LANGUAGE_MAP;
window.SpeechService = SpeechService;
window.NAV_COMMANDS = NAV_COMMANDS;
window.matchVoiceCommand = matchVoiceCommand;
window.API = API;
window.Validator = Validator;
window.showToast = showToast;
window.Modal = Modal;
window.setLanguage = setLanguage;
window.toggleTheme = toggleTheme;
window.debounce = debounce;
