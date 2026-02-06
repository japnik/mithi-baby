// Mithi.baby - Application Logic

// Configuration
const CONFIG = {
    GEMINI_API_KEY: '',
    SUNO_API_KEY: '',
    SUNO_BASE_URL: '',
    SUPABASE_URL: '', // Loaded from config.json
    SUPABASE_KEY: '', // Loaded from config.json
    STRIPE_PUBLIC_KEY: '',
    ENABLE_PAYMENTS: true // Default true
};

// API Instances
let supabaseClient = null;
let stripe = null;

// State Management
const state = {
    language: 'Punjabi',
    babyName: '',
    characters: ['Papa', 'Mummy'],
    occasion: 'Lori', // Default since UI removed it
    user: null,
    songs: []
};

// DOM Elements
const elements = {
    loginBtn: document.getElementById('loginBtn'),
    userProfile: document.getElementById('userProfile'),
    userEmail: document.getElementById('userEmail'),
    logoutBtn: document.getElementById('logoutBtn'),

    languageBtns: document.querySelectorAll('[data-language]'),
    babyNameInput: document.getElementById('babyName'),
    characterBtns: document.querySelectorAll('[data-character]'),
    selectAllCharacters: document.getElementById('selectAllCharacters'),
    createSongBtn: document.getElementById('createSongBtn'),
    autoYoutube: document.getElementById('autoYoutube'),

    // Loading/Progress
    loadingContainer: document.getElementById('loadingContainer'),
    loadingText: document.getElementById('loadingText'),
    progressBar: document.getElementById('progressBar'),
    progressPercentage: document.getElementById('progressPercentage'),

    // Library
    libraryEmpty: document.getElementById('libraryEmpty'),
    songList: document.getElementById('songList'),

    // Modals
    playerModal: document.getElementById('playerModal'),
    closeModal: document.getElementById('closeModal'),
    videoPlayer: document.getElementById('videoPlayer'),
    playerTitle: document.getElementById('playerTitle'),
    playerMeta: document.getElementById('playerMeta'),
    downloadBtn: document.getElementById('downloadBtn'),

    detailsModal: document.getElementById('detailsModal'),
    closeDetailsModal: document.getElementById('closeDetailsModal'),
    detailsContent: document.getElementById('detailsContent'),

    // Auth Modal
    authModal: document.getElementById('authModal'),
    closeAuthModal: document.getElementById('closeAuthModal'),
    modalLoginBtn: document.getElementById('modalLoginBtn'),

    // Payment Modal
    paymentModal: document.getElementById('paymentModal'),
    closePaymentModal: document.getElementById('closePaymentModal'),
    confirmPaymentBtn: document.getElementById('confirmPaymentBtn'),

    // Success Modal
    successModal: document.getElementById('successModal'),
    closeSuccessModal: document.getElementById('closeSuccessModal'),
    successCloseBtn: document.getElementById('successCloseBtn'),

    // Promo Code
    promoCodeInput: document.getElementById('promoCodeInput'),
    applyPromoBtn: document.getElementById('applyPromoBtn'),
    promoStatus: document.getElementById('promoStatus')
};

// --- Helpers ---
function saveFormState(intent = null) {
    const data = {
        babyName: state.babyName,
        language: state.language,
        characters: state.characters,
        occasion: state.occasion,
        autoYoutube: elements.autoYoutube ? elements.autoYoutube.checked : true,
        intent: intent // e.g., 'showPayment'
    };
    localStorage.setItem('mithi_baby_form_state', JSON.stringify(data));
}

function checkAndTriggerIntent() {
    if (!state.user) return;

    const saved = localStorage.getItem('mithi_baby_form_state');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            if (data.intent === 'showPayment' && elements.paymentModal) {
                elements.paymentModal.classList.remove('hidden');
                // Clear intent so it doesn't pop up again on refresh
                data.intent = null;
                localStorage.setItem('mithi_baby_form_state', JSON.stringify(data));
            }
        } catch (e) { console.error('Intent check error:', e); }
    }
}

function loadFormState() {
    const saved = localStorage.getItem('mithi_baby_form_state');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            state.babyName = data.babyName || '';
            state.language = data.language || 'Punjabi';
            state.characters = data.characters || [];
            state.occasion = data.occasion || 'Lori';

            // Migration: If the stored occasion is "Special Song", migrate it to "Lori"
            if (state.occasion === 'Special Song') {
                state.occasion = 'Lori';
                saveFormState();
            }

            // Update UI
            if (elements.babyNameInput) elements.babyNameInput.value = state.babyName;

            elements.languageBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.language === state.language);
            });

            // Sync UI for ALL buttons based on state
            elements.characterBtns.forEach(btn => {
                const char = btn.dataset.character;
                const isSelected = state.characters.includes(char);
                btn.classList.toggle('selected', isSelected);
            });
        } catch (e) {
            console.error('Failed to load form state:', e);
        }
    }
}

function resetForm() {
    state.babyName = '';
    if (elements.babyNameInput) elements.babyNameInput.value = '';
    state.characters = ['Papa', 'Mummy'];
    elements.characterBtns.forEach(btn => {
        const isDefault = state.characters.includes(btn.dataset.character);
        btn.classList.toggle('selected', isDefault);
    });

    // Clear Promo Code
    if (elements.promoCodeInput) elements.promoCodeInput.value = '';
    if (elements.promoStatus) {
        elements.promoStatus.textContent = '';
        elements.promoStatus.style.display = 'none';
    }
}

// --- Authentication ---

async function signInWithGoogle() {
    if (!supabaseClient) return alert("Supabase not initialized");
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin, // Redirect back to this page
            queryParams: {
                prompt: 'select_account',
                access_type: 'offline'
            }
        }
    });
    if (error) alert(error.message);
}

async function signOut() {
    if (!supabaseClient) return;
    const { error } = await supabaseClient.auth.signOut();
    if (error) alert(error.message);
    else {
        state.user = null;
        updateAuthUI();
        window.location.reload();
    }
}

function updateAuthUI() {
    if (state.user) {
        if (elements.loginBtn) elements.loginBtn.classList.add('hidden');
        if (elements.userProfile) elements.userProfile.classList.remove('hidden');
        if (elements.userEmail) {
            elements.userEmail.textContent = state.user.email;
            // Set initial
            const initial = state.user.email.charAt(0).toUpperCase();
            const initialEl = document.getElementById('userInitial');
            if (initialEl) initialEl.textContent = initial;
        }
    } else {
        if (elements.loginBtn) elements.loginBtn.classList.remove('hidden');
        if (elements.userProfile) elements.userProfile.classList.add('hidden');
        if (elements.userEmail) elements.userEmail.textContent = '';
    }
}


// --- Event Listeners ---

function setupEventListeners() {
    // Auth
    if (elements.loginBtn) elements.loginBtn.addEventListener('click', signInWithGoogle);
    if (elements.logoutBtn) elements.logoutBtn.addEventListener('click', signOut);

    // Language
    elements.languageBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.languageBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.language = btn.dataset.language;

            // Temporary bounce effect
            btn.classList.add('bounce-ball');
            setTimeout(() => btn.classList.remove('bounce-ball'), 600);
        });
    });

    // Baby Name
    elements.babyNameInput.addEventListener('input', (e) => {
        state.babyName = e.target.value;
    });

    // Characters
    elements.characterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('selected');
            const char = btn.dataset.character;

            if (btn.classList.contains('selected')) {
                if (!state.characters.includes(char)) state.characters.push(char);
                // Bounce effect on selection
                btn.classList.add('bounce-ball');
                setTimeout(() => btn.classList.remove('bounce-ball'), 600);
            } else {
                state.characters = state.characters.filter(c => c !== char);
            }
            saveFormState();
        });
    });

    // Select All
    elements.selectAllCharacters.addEventListener('click', () => {
        const allSelected = state.characters.length === elements.characterBtns.length;
        if (allSelected) {
            state.characters = [];
            elements.characterBtns.forEach(btn => {
                btn.classList.remove('selected');
            });
            elements.selectAllCharacters.textContent = 'Select All';
        } else {
            state.characters = [];
            elements.characterBtns.forEach(btn => {
                btn.classList.add('selected');
                state.characters.push(btn.dataset.character);
            });
            elements.selectAllCharacters.textContent = 'Deselect All';
        }
    });

    // Create Song (Payment Flow)
    elements.createSongBtn.addEventListener('click', handlePayAndCreateSong);

    // Modals
    elements.closeModal.addEventListener('click', closePlayerModal);
    elements.playerModal.addEventListener('click', (e) => {
        if (e.target === elements.playerModal) closePlayerModal();
    });

    if (elements.closeDetailsModal) {
        elements.closeDetailsModal.addEventListener('click', () => elements.detailsModal.classList.add('hidden'));
        elements.detailsModal.addEventListener('click', (e) => {
            if (e.target === elements.detailsModal) elements.detailsModal.classList.add('hidden');
        });
    }

    // Auth Modal Links
    if (elements.modalLoginBtn) {
        elements.modalLoginBtn.addEventListener('click', () => {
            saveFormState();
            signInWithGoogle();
        });
    }
    if (elements.closeAuthModal) {
        elements.closeAuthModal.addEventListener('click', () => elements.authModal.classList.add('hidden'));
        elements.authModal.addEventListener('click', (e) => {
            if (e.target === elements.authModal) elements.authModal.classList.add('hidden');
        });
    }

    // Payment Modal
    if (elements.applyPromoBtn) {
        elements.applyPromoBtn.addEventListener('click', () => {
            const code = elements.promoCodeInput.value.trim();
            if (!code) return;

            // Disable immediately to prevent double-clicks
            elements.applyPromoBtn.disabled = true;

            // Improved feedback
            elements.promoStatus.style.display = 'block';
            elements.promoStatus.textContent = "✨ Validating heirloom token...";
            elements.promoStatus.style.color = "var(--primary)";

            // Subtle delay for "premium" feel
            setTimeout(() => {
                if (elements.confirmPaymentBtn) {
                    elements.confirmPaymentBtn.click();
                }
                // Re-enable in case it fails or modal stays open
                setTimeout(() => {
                    if (elements.applyPromoBtn) elements.applyPromoBtn.disabled = false;
                }, 2000);
            }, 800);
        });
    }

    if (elements.confirmPaymentBtn) {
        elements.confirmPaymentBtn.addEventListener('click', () => {
            // Don't close immediately! Wait for result.
            // elements.paymentModal.classList.add('hidden'); 
            createCheckoutSession();
        });
    }
    if (elements.closePaymentModal) {
        elements.closePaymentModal.addEventListener('click', () => elements.paymentModal.classList.add('hidden'));
    }

    // Success Modal Closing Logic
    const closeSuccess = () => {
        if (elements.successModal) elements.successModal.classList.add('hidden');
        resetForm();
    };
    if (elements.closeSuccessModal) elements.closeSuccessModal.addEventListener('click', closeSuccess);
    if (elements.successCloseBtn) elements.successCloseBtn.addEventListener('click', closeSuccess);
    if (elements.successModal) {
        elements.successModal.addEventListener('click', (e) => {
            if (e.target === elements.successModal) closeSuccess();
        });
    }
} // <--- Correctly close setupEventListeners

// --- Payment & Creation Flow ---

async function handlePayAndCreateSong() {
    // 1. Validate Inputs
    if (!state.babyName.trim()) {
        alert('Please enter your baby\'s name');
        elements.babyNameInput.focus();
        return;
    }
    if (state.characters.length === 0) {
        state.characters = ['Papa', 'Mummy'];
    }

    // 2. Check Auth
    if (!state.user) {
        saveFormState('showPayment');
        if (elements.authModal) {
            elements.authModal.classList.remove('hidden');
        } else {
            signInWithGoogle(); // Fallback
        }
        return;
    }

    // 3. Show Payment Commitment Modal Instead of checking out immediately
    if (CONFIG.ENABLE_PAYMENTS) {
        if (elements.paymentModal) {
            elements.paymentModal.classList.remove('hidden');
        } else {
            createCheckoutSession(); // Fallback
        }
    } else {
        // Bypass Payment Modal if disabled
        createCheckoutSession();
    }
}

async function createCheckoutSession() {
    // 4. Initiate Checkout
    const btn = elements.createSongBtn;

    // Guard Clause: Prevent double-submission
    if (btn.disabled) return;

    const ogText = btn.textContent;
    btn.textContent = 'Preparing Payment...';
    btn.disabled = true;

    try {
        const payload = {
            babyName: state.babyName,
            language: state.language,
            characters: state.characters,
            occasion: state.occasion,
            email: state.user.email,
            user_id: state.user.id,
            autoYoutube: elements.autoYoutube ? elements.autoYoutube.checked : true,
            promoCode: elements.promoCodeInput ? elements.promoCodeInput.value.trim() : ""
        };

        const response = await fetch('/api/create_checkout_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to create payment session');

        const data = await response.json();

        if (data.status === 'payment_skipped') {
            // Free song! 🪄
            if (elements.paymentModal) elements.paymentModal.classList.add('hidden');
            if (elements.successModal) elements.successModal.classList.remove('hidden');
            pollPendingSong(data.song_id);

            // Reset button
            btn.textContent = ogText;
            btn.disabled = false;
            return;
        }

        // Handle Invalid Promo Code (User stays on modal)
        if (data.status === 'invalid_promo') {
            if (elements.promoStatus) {
                elements.promoStatus.style.display = 'block';
                elements.promoStatus.textContent = "❌ Invalid Code. Try again or pay $1.00";
                elements.promoStatus.style.color = "red";
            }
            // Reset buttons to allow retry
            btn.textContent = ogText;
            btn.disabled = false;
            // The apply button has a timeout re-enable, but we can ensure it here if desired
            return;
        }

        if (data.id) {
            stripe.redirectToCheckout({ sessionId: data.id });
        } else {
            alert(data.error || 'Failed to create checkout session');
        }
    } catch (error) {
        console.error('Payment Error:', error);
        alert('Payment failed: ' + error.message);
        btn.textContent = ogText;
        btn.disabled = false;
    }
}


// --- Library & Utils ---

async function loadSongsFromStorage() {
    try {
        let songs = [];

        // 1. Try Supabase Direct (Leverages RLS + Auth Session)
        if (supabaseClient && state.user) {
            console.log("Fetching songs from Supabase for user:", state.user.id);
            const { data, error } = await supabaseClient
                .from('songs')
                .select('*')
                .eq('user_id', state.user.id) // Filter by logged-in user
                .order('started_at', { ascending: false })
                .order('created_at', { ascending: false }); // Fallback sorting

            if (!error && data) {
                songs = data;
                console.log(`Found ${songs.length} songs in Supabase.`);
            } else if (error) {
                console.warn("Supabase Fetch Error:", error);
            }
        }

        // 2. Fallback/Merge with Backend API (legacy/global)
        if (songs.length === 0 && state.user) {
            console.log("Falling back to Backend API...");
            const response = await fetch(`/api/songs?user_id=${state.user.id}`);
            if (response.ok) {
                const data = await response.json();
                if (data.songs) songs = data.songs;
            }
        }

        if (songs) {
            state.songs = songs.map(s => ({
                id: s.song_id || s.id,
                title: s.title,
                babyName: s.babyName || s.baby_name,
                occasion: s.occasion,
                language: s.language,
                characters: s.characters,
                lyrics: s.lyrics,
                videoUrl: s.video_url,
                coverImageUrl: s.cover_image_url || s.image_url,
                audioUrl: s.audio_url,
                youtubeUrl: s.youtube_url,
                createdAt: s.date || s.created_at,
                createdAt: s.date || s.created_at,
                source: "cloud"
            })).filter(s => {
                // Filter out bad data ("null" titles) UNLESS it is processing
                // If processing, title might be null, so we keep it and handle display in UI
                if (s.title === "null" || !s.title) {
                    // Only keep if explicitly processing/pending
                    // But if it's completed and null, it's junk.
                    // Actually, let's just sanitize the title in display.
                    return true;
                }
                return true;
            });
            updateLibraryDisplay();
        }
    } catch (e) {
        console.error("Load songs error:", e);
    }
}

function updateLibraryDisplay() {
    if (!elements.libraryEmpty || !elements.songList) return;

    if (state.songs.length === 0) {
        elements.libraryEmpty.classList.remove('hidden');
        elements.songList.innerHTML = '';
        return;
    }
    elements.libraryEmpty.classList.add('hidden');
    elements.songList.innerHTML = state.songs.map(song => `
        <div class="song-card" onclick="playSongById('${song.id}')">
            <img src="${song.coverImageUrl || 'assets/logo.png'}" alt="${song.title || 'Generating...'}" class="song-thumbnail">
            <div class="song-info">
                <h3 class="song-title">${(!song.title || song.title === 'null') ? '✨ Creating Song...' : song.title}</h3>
                <div class="song-tags">
                    <span class="song-tag">${song.language}</span>
                </div>
            </div>
            <div class="song-actions">
                <button class="song-play-btn" onclick="event.stopPropagation(); playSongById('${song.id}')">▶</button>
                ${song.youtubeUrl
            ? `<button class="song-yt-btn" onclick="event.stopPropagation(); window.open('${song.youtubeUrl}', '_blank')" title="Watch on YouTube">
                <svg viewBox="0 0 68 48" width="48" height="34">
                    <path class="yt-icon-bg" d="M66.52,7.74c-0.78-2.93-2.49-5.41-5.42-6.19C55.79,.13,34,0,34,0S12.21,.13,6.9,1.55 C3.97,2.33,2.27,4.81,1.48,7.74C0.06,13.05,0,24,0,24s0.06,10.95,1.48,16.26c0.78,2.93,2.49,5.41,5.42,6.19 C12.21,47.87,34,48,34,48s21.79-0.13,27.1-1.55c2.93-0.78,4.64-3.26,5.42-6.19C67.94,34.95,68,24,68,24S67.94,13.05,66.52,7.74z" fill="#FF0000"></path>
                    <path d="M 45,24 27,14 27,34" fill="#FFFFFF"></path>
                </svg>
               </button>`
            : ''}
            </div>
        </div>
    `).join('');
}


function playSongById(songId) {
    const song = state.songs.find(s => s.id === songId);
    if (song) playSong(song);
}

function playSong(song) {
    elements.playerTitle.textContent = song.title;
    elements.playerMeta.textContent = `${song.babyName} • ${song.language} `;
    elements.videoPlayer.src = song.videoUrl;
    elements.videoPlayer.poster = song.coverImageUrl;
    elements.downloadBtn.onclick = () => downloadVideo(song.videoUrl, song.title);
    elements.playerModal.classList.remove('hidden');
}

function closePlayerModal() {
    elements.playerModal.classList.add('hidden');
    elements.videoPlayer.pause();
    elements.videoPlayer.src = '';
}

function showSongDetails(songId) {
    const song = state.songs.find(s => s.id === songId);
    if (!song) return;
    const detailsContent = document.getElementById('detailsContent');
    detailsContent.innerHTML = `
        <h2 style="margin-bottom: 1.5rem; color: var(--primary);">${song.title}</h2>
            <div style="background: #FFF5F7; padding: 1.5rem; border-radius: 12px; border: 1px solid #FFE8F0;">
                <p style="font-size: 1.1rem; line-height: 1.8; color: var(--text-dark); white-space: pre-line;">${song.lyrics || 'No lyrics available'}</p>
            </div>
    `;
    elements.detailsModal.classList.remove('hidden');
}

function downloadVideo(url, title) {
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.mp4`;
    a.click();
}





// --- Initialization ---

async function loadConfig() {
    try {
        const response = await fetch('api/config.json');
        const config = await response.json();

        CONFIG.GEMINI_API_KEY = config.GEMINI_API_KEY; // Likely used by backend now, frontend might not need?
        CONFIG.SUPABASE_URL = config.SUPABASE_URL;
        CONFIG.SUPABASE_KEY = config.SUPABASE_KEY;
        CONFIG.STRIPE_PUBLIC_KEY = config.STRIPE_PUBLIC_KEY; // NEW
        CONFIG.ENABLE_PAYMENTS = config.ENABLE_PAYMENTS;

        if (CONFIG.SUPABASE_URL && CONFIG.SUPABASE_KEY && window.supabase) {
            supabaseClient = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_KEY);

            // Check session
            const { data } = await supabaseClient.auth.getSession();
            if (data.session) {
                state.user = data.session.user;
                updateAuthUI();
                loadSongsFromStorage();
                checkAndTriggerIntent(); // Initial check
            }

            // Auth listener
            supabaseClient.auth.onAuthStateChange((event, session) => {
                state.user = session ? session.user : null;
                updateAuthUI();
                if (session) {
                    loadSongsFromStorage();
                    checkAndTriggerIntent(); // Event-based check
                } else {
                    state.songs = []; // Clear songs on logout
                }
                updateLibraryDisplay();
            });
        }

        if (config.STRIPE_PUBLIC_KEY) {
            stripe = Stripe(config.STRIPE_PUBLIC_KEY);
        }

    } catch (error) {
        console.error('Error loading config:', error);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // Check for success params (Redirect from Stripe)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('session_id')) {
        history.replaceState(null, '', window.location.pathname); // Clear URL
        localStorage.removeItem('mithi_baby_form_state'); // Clear stored form

        // Show Success Modal
        if (elements.successModal) {
            elements.successModal.classList.remove('hidden');
        }

        // Trigger generation by calling backend to "verify_and_generate" using session_id
        try {
            const sessionId = urlParams.get('session_id');
            fetch(`/ api / payment_success ? session_id = ${sessionId} `)
                .then(r => r.json())
                .then(d => {
                    if (d.status === 'started') {
                        // Start polling in background
                        pollPendingSong(d.song_id);
                    }
                });
        } catch (e) { console.error(e); }
    }

    await loadConfig();
    loadFormState(); // Restore state from storage
    setupEventListeners();
});

// Simple Polling (Concise)
async function pollPendingSong(songId) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/ task_status / ${songId} `);
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'completed') {
                    clearInterval(interval);
                    loadSongsFromStorage(); // Refresh list
                    elements.loadingContainer.classList.add('hidden');
                    elements.createSongBtn.classList.remove('hidden');
                    alert("Song Ready!");
                }
            }
        } catch (e) { }
    }, 5000);
}

// Global expose
window.playSongById = playSongById;
window.showSongDetails = showSongDetails;

