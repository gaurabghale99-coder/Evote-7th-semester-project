// Main JavaScript for E-Vote System

const ADMIN_PASSWORD = 'admin123';

const DEFAULT_PARTIES = [
    { id: 'party1', name: 'Nepal Communist Party (Unified Marxist-Leninist)', candidate: 'Ram Bahadur Shrestha', emoji: '☀️' },
    { id: 'party2', name: 'Nepali Congress', candidate: 'Sita Devi Yadav', emoji: '🌳' },
    { id: 'party3', name: 'Rastriya Prajatantra Party', candidate: 'Hari Prasad Koirala', emoji: '🔔' },
    { id: 'party4', name: 'Janata Samajwadi Party', candidate: 'Gita Kumari Thapa', emoji: '📣' },
    { id: 'party5', name: 'Loktantrik Samajwadi Party', candidate: 'Krishna Bahadur Mahara', emoji: '🪘' },
    { id: 'party6', name: 'Independent Candidate', candidate: 'Shyam Kumar Basnet', emoji: '🐓' },
    { id: 'party7', name: 'Rastriya Swatantra Party', candidate: 'Anil Prakash', emoji: '🐝' },
    { id: 'party8', name: 'Bibeksheel Sajha', candidate: 'Rina Gautam', emoji: '✡️' },
    { id: 'party9', name: 'Maoist Centre', candidate: 'Kul Prasad Bhattarai', emoji: '🧺' },
    { id: 'party10', name: 'Janamat Party', candidate: 'Manoj Yadav', emoji: '🎯' },
    { id: 'party11', name: 'Rastriya Prajatantra Party', candidate: 'Shankar Prasad', emoji: '⚙️' },
    { id: 'party12', name: 'Independent Candidate', candidate: 'Lila Karki', emoji: '🐟' }
];

document.addEventListener('DOMContentLoaded', function () {
    // 1. Force Redirect to Home on Refresh
    // If we are NOT on index.html (or root), and the page was reloaded, go to index.html
    const isIndex = window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/');

    // Check for reload navigation
    const entries = performance.getEntriesByType("navigation");
    const isReload = entries.length > 0 && entries[0].type === "reload";

    if (!isIndex && isReload) {
        window.location.href = 'index.html';
        return; // Stop further initialization
    }

    try { initializeDataStores(); } catch (e) { console.error('DataStore Init Failed', e); }
    try { initializeAdminPanel(); } catch (e) { console.error('Admin Panel Init Failed', e); }
    try { initializeWelcomePage(); } catch (e) { console.error('Welcome Page Init Failed', e); }
    try { initializeRegistrationPage(); } catch (e) { console.error('Registration Page Init Failed', e); }
    try { initializeBallotPage(); } catch (e) { console.error('Ballot Page Init Failed', e); }
    try { initializeSuccessPage(); } catch (e) { console.error('Success Page Init Failed', e); }
    try { initializeLanguagePage(); } catch (e) { console.error('Language Page Init Failed', e); }

    // Cleanup camera if the user navigates away or closes the tab
    window.addEventListener('pagehide', function () {
        fetch("http://localhost:8000/stop_camera").catch(() => { });
    });
});

// ============================================
// Data helpers
// ============================================

function initializeDataStores() {
    const storedParties = getParties();
    if (!storedParties.length) {
        localStorage.setItem('parties', JSON.stringify(DEFAULT_PARTIES));
    }
    if (!localStorage.getItem('votes')) {
        localStorage.setItem('votes', '[]');
    }
    if (!localStorage.getItem('voterList')) {
        localStorage.setItem('voterList', '[]');
    }
}

function getParties() {
    try {
        return JSON.parse(localStorage.getItem('parties') || '[]');
    } catch (e) {
        return [];
    }
}

function saveParties(parties) {
    localStorage.setItem('parties', JSON.stringify(parties));
}

function addParty(party) {
    const parties = getParties();
    parties.push(party);
    saveParties(parties);
}

function deletePartyById(id) {
    const parties = getParties().filter(p => p.id !== id);
    saveParties(parties);
}

function getVotes() {
    try {
        const rawVotes = JSON.parse(localStorage.getItem('votes') || '[]');
        const activeParties = getParties();

        const validVotes = rawVotes.filter(vote => {
            const pStr = vote.selectedParty;
            if (!pStr) return false;

            const parts = pStr.split(' | ');
            const pName = parts[0];

            return activeParties.some(p => p.name === pName && (!parts[1] || p.candidate === parts[1]));
        });

        // Retroactively remove them from database if we filtered anything out
        if (validVotes.length !== rawVotes.length) {
            localStorage.setItem('votes', JSON.stringify(validVotes));
        }

        return validVotes;
    } catch (e) {
        return [];
    }
}

function addVote(vote) {
    const votes = getVotes();
    votes.push(vote);
    localStorage.setItem('votes', JSON.stringify(votes));
    // Keep last vote for existing flows
    localStorage.setItem('voteData', JSON.stringify(vote));
}

function getVoterList() {
    try {
        return JSON.parse(localStorage.getItem('voterList') || '[]');
    } catch (e) {
        return [];
    }
}

function addVoter(voter) {
    const voters = getVoterList();
    voters.push(voter);
    localStorage.setItem('voterList', JSON.stringify(voters));
}

// ============================================
// Welcome Page Functionality
// ============================================

// ============================================
// Welcome Page Functionality
// ============================================

function initializeWelcomePage() {
    const startFaceRecognitionBtn = document.getElementById('start-face-recognition');
    const proceedBtn = document.getElementById('proceed-btn');
    const faceStatus = document.getElementById('face-status');
    const faceCard = document.getElementById('face-recognition-card');

    // Always reset face recognition state on page load
    localStorage.removeItem('faceRecognitionDone');

    // Reset face recognition card to initial state (stops any lingering camera stream)
    // Reset face recognition card to initial state
    if (faceCard) {
        faceCard.innerHTML = `
            <div class="face-icon">👤</div>
            <h3>Face Recognition | अनुहार पहिचान</h3>
            <p>Complete your face recognition to proceed with voting<br>मतदान अगाडि बढ्नको लागि आफ्नो अनुहार पहिचान पूरा गर्नुहोस्</p>
            <button class="btn btn-primary" id="start-face-recognition">
                Start Face Recognition | अनुहार पहिचान सुरु गर्नुहोस्
            </button>
        `;
        faceCard.style.display = 'block';

        // Re-binding event listener
        const newStartBtn = document.getElementById('start-face-recognition');
        if (newStartBtn) {
            newStartBtn.addEventListener('click', function () {
                startFaceRecognition();
            });
        }
    }

    // Explicitly ensure camera is off when returning to welcome page
    fetch("http://localhost:8000/stop_camera").catch(() => { });

    // Check for persistent block
    const blockUntil = localStorage.getItem('voterBlockUntil');
    const now = Date.now();

    if (blockUntil && now < parseInt(blockUntil)) {
        // Still blocked!
        if (faceCard) {
            faceCard.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            faceCard.innerHTML = `
                <div class="face-icon">🚫</div>
                <h3 style="color: white;">Access Blocked | पहुँच रोकियो</h3>
            `;
        }
        if (proceedBtn) {
            proceedBtn.disabled = false;
            proceedBtn.setAttribute('data-blocked', 'true');
            proceedBtn.setAttribute('data-message', localStorage.getItem('voterBlockMessage') || 'You are blocked for 1 minute.');
        }
        if (faceStatus) faceStatus.style.display = 'none';
    } else {
        // Not blocked or block expired
        localStorage.removeItem('voterBlockUntil');
        localStorage.removeItem('voterBlockMessage');

        if (faceStatus) faceStatus.style.display = 'none';
        if (proceedBtn) {
            proceedBtn.disabled = true;
            proceedBtn.removeAttribute('data-blocked');
        }
    }

    // Proceed button handler
    if (proceedBtn) {
        proceedBtn.addEventListener('click', function () {
            const isBlocked = proceedBtn.getAttribute('data-blocked') === 'true';
            if (isBlocked) {
                const msg = proceedBtn.getAttribute('data-message') || 'You have been blocked for 1 minute.';
                alert(msg);
                return;
            }
            if (!proceedBtn.disabled) {
                window.location.href = 'language.html';
            }
        });
    }
}

function startFaceRecognition() {
    const faceRecognitionCard = document.getElementById('face-recognition-card');
    const faceStatus = document.getElementById('face-status');
    const proceedBtn = document.getElementById('proceed-btn');

    if (faceRecognitionCard) {
        // Cache busting for the camera stream
        const timestamp = new Date().getTime();
        faceRecognitionCard.innerHTML = `
            <div class="camera-stream-container">
                <div class="camera-placeholder">
                    <div class="spinner"></div>
                    <p>Initializing camera...</p>
                </div>
                <img src="" 
                     data-src="http://localhost:8000/video_feed?t=${timestamp}" 
                     alt="Live Camera Feed" 
                     class="camera-stream" 
                     style="display: none;"
                     onload="this.style.display='block'; if(this.previousElementSibling) this.previousElementSibling.style.display='none'">
                <div class="scanning-bar"></div>
            </div>
            <h3>Scanning Face... | अनुहार स्क्यान गर्दै...</h3>
            <p>Please keep your face steady.<br>कृपया आफ्नो अनुहार स्थिर राख्नुहोस्।</p>
        `;

        // Small delay to allow backend to warm up BEFORE setting the img src
        setTimeout(() => {
            const img = faceRecognitionCard.querySelector('.camera-stream');
            if (img && img.hasAttribute('data-src')) {
                img.src = img.getAttribute('data-src');
            }
        }, 1000); // 1 second warm-up
    }

    if (faceStatus) {
        faceStatus.style.display = 'none';
        faceStatus.classList.remove('error');
    }
    if (proceedBtn) proceedBtn.disabled = true;

    // Start both the backend request and a 4s timer
    const scanDuration = 4000; // 4 seconds

    const faceLoginPromise = fetch("http://localhost:8000/face_login").then(res => res.json());

    const minDelayPromise = new Promise(resolve => {
        setTimeout(() => {
            resolve();
        }, scanDuration);
    });

    Promise.all([faceLoginPromise, minDelayPromise])
        .then(([data]) => {
            // Function to clear camera stream and signal backend
            const stopCameraStream = () => {
                const streamImg = document.querySelector('.camera-stream');
                if (streamImg) {
                    streamImg.src = '';
                    streamImg.remove();
                }
                // Explicitly tell backend to stop camera
                fetch("http://localhost:8000/stop_camera").catch(() => { });
            };

            if (data.status === "allowed") {
                stopCameraStream(); // Clear camera immediately
                if (faceRecognitionCard) {
                    faceRecognitionCard.style.display = 'none';
                }

                if (faceStatus) {
                    faceStatus.innerHTML = `
                        <div class="status-icon">✅</div>
                        <p>Face recognized: <strong>${data.name}</strong><br>You can vote now. | अब तपाईं मतदान गर्न सक्नुहुन्छ।</p>
                    `;
                    faceStatus.style.display = 'block';
                    faceStatus.className = 'face-recognition-status success';

                    const currentVoter = JSON.parse(localStorage.getItem('voterData') || '{}');
                    currentVoter.voterId = data.voter_id;
                    currentVoter.voterCode = data.voter_code;
                    currentVoter.fullName = data.name;
                    localStorage.setItem('voterData', JSON.stringify(currentVoter));
                }
                if (proceedBtn) {
                    proceedBtn.disabled = false;
                    proceedBtn.removeAttribute('data-blocked');
                }
            } else if (data.status === "blocked") {
                stopCameraStream();
                if (faceRecognitionCard) {
                    faceRecognitionCard.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                    faceRecognitionCard.innerHTML = `
                        <div class="face-icon">🚫</div>
                        <h3 style="color: white;">Access Blocked | पहुँच रोकियो</h3>
                    `;
                }
                // Hide redundant status box
                if (faceStatus) {
                    faceStatus.style.display = 'none';
                }

                // Persist the block for 1 minute in case of refresh
                localStorage.setItem('voterBlockUntil', Date.now() + 60000);
                localStorage.setItem('voterBlockMessage', data.message);

                // Enable proceed button but with a block flag so click shows the alert as requested
                if (proceedBtn) {
                    proceedBtn.disabled = false;
                    proceedBtn.setAttribute('data-blocked', 'true');
                    proceedBtn.setAttribute('data-message', data.message);
                }
            } else if (data.status === "already_voted") {
                stopCameraStream(); // Clear camera
                if (faceRecognitionCard) {
                    faceRecognitionCard.innerHTML = `
                        <div class="status-icon">⚠️</div>
                        <p>${data.name} has already voted! | ${data.name} ले पहिले नै मतदान गरिसके।</p>
                        <button class="btn btn-secondary" onclick="window.location.reload()">Back | फिर्ता</button>
                    `;
                }
                if (faceStatus) {
                    faceStatus.innerHTML = `
                        <div class="status-icon">⚠️</div>
                        <p>${data.name} has already voted! | ${data.name} ले पहिले नै मतदान गरिसके।</p>
                    `;
                    faceStatus.style.display = 'block';
                    faceStatus.className = 'face-recognition-status warning';
                }
            } else if (data.status === "multiple_faces") {
                stopCameraStream(); // Clear camera

                // Hide the red status box
                if (faceStatus) {
                    faceStatus.style.display = 'none';
                }

                if (faceRecognitionCard) {
                    // Change card background to red
                    faceRecognitionCard.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                    faceRecognitionCard.innerHTML = `
                        <div class="face-icon">👥</div>
                        <h3 style="color: white;">Multiple Faces Detected | धेरै अनुहार फेला परे</h3>
                        <p style="color: white;">Only one person is allowed at a time. | एक पटकमा एक जना मात्र अनुमति छ।</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            Retry | फेरि प्रयास गर्नुहोस्
                        </button>
                    `;
                }
            } else {
                stopCameraStream(); // Clear camera

                // Hide the red status box
                if (faceStatus) {
                    faceStatus.style.display = 'none';
                }

                if (faceRecognitionCard) {
                    // Change card background to red and add inline styling
                    faceRecognitionCard.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                    faceRecognitionCard.innerHTML = `
                        <div class="face-icon">👤</div>
                        <h3>Recognition Failed | पहिचान विफल</h3>
                        <p>We couldn't recognize your face. | हामीले तपाईंको अनुहार चिन्न सकेनौं।</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            Retry | फेरि प्रयास गर्नुहोस्
                        </button>
                    `;
                }
            }
        })
        .catch(err => {
            console.error("Error connecting to backend:", err);
            const streamImg = document.querySelector('.camera-stream');
            if (streamImg) streamImg.remove();

            if (faceStatus) {
                faceStatus.innerHTML = `
                    <div class="status-icon">🚫</div>
                    <p>Cannot connect to backend. | ब्याकएन्डसँग जडान हुन सकेन।</p>
                `;
                faceStatus.style.display = 'block';
                faceStatus.className = 'face-recognition-status error';
            }
        });
}

// ============================================
// Registration Page Functionality
// ============================================

// Auto-format date input (YYYY/MM/DD)
function clampNumber(value, min, max) {
    if (Number.isNaN(value)) return null;
    return Math.min(max, Math.max(min, value));
}

// Validate BS date string (YYYY/MM/DD) with basic bounds:
// - month: 1-12
// - day: 1-32 (BS months can vary; keep a safe upper bound)
function validateBsDateString(value) {
    const match = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec((value || '').trim());
    if (!match) {
        return { valid: false, message: 'Date must be in YYYY/MM/DD format (e.g., 2080/01/15)' };
    }

    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);

    if (Number.isNaN(year) || year < 1) {
        return { valid: false, message: 'Year must be a valid number' };
    }
    if (Number.isNaN(month) || month < 1 || month > 12) {
        return { valid: false, message: 'Month must be between 1 and 12' };
    }
    if (Number.isNaN(day) || day < 1 || day > 32) {
        return { valid: false, message: 'Day must be between 1 and 32' };
    }

    return { valid: true, message: '' };
}

function formatDateInput(input) {
    input.addEventListener('input', function (e) {
        let value = e.target.value;

        // Remove all characters except numbers and forward slashes
        value = value.replace(/[^\d/]/g, '');

        // Remove extra slashes
        value = value.replace(/\/+/g, '/');

        // Split by slash to get parts
        const parts = value.split('/');
        let formatted = '';

        // Format year (first 4 digits)
        if (parts[0]) {
            formatted = parts[0].substring(0, 4);

            // Add slash after year if 4 digits entered
            if (parts[0].length >= 4 && parts.length === 1) {
                formatted += '/';
            } else if (parts.length > 1) {
                formatted += '/';

                // Format month (next 2 digits)
                if (parts[1]) {
                    let rawMonth = parts[1].substring(0, 2);
                    // Clamp month once user has typed 2 digits or they typed an explicit slash after month
                    if (rawMonth.length === 2 || parts.length > 2) {
                        const m = clampNumber(Number(rawMonth), 1, 12);
                        rawMonth = m === null ? rawMonth : String(m).padStart(2, '0');
                    }
                    formatted += rawMonth;

                    // Add slash after month if 2 digits entered
                    if (parts[1].length >= 2 && parts.length === 2) {
                        formatted += '/';
                    } else if (parts.length > 2) {
                        formatted += '/';

                        // Format day (last 2 digits)
                        if (parts[2]) {
                            let rawDay = parts[2].substring(0, 2);
                            // Clamp day once user has typed 2 digits
                            if (rawDay.length === 2) {
                                const d = clampNumber(Number(rawDay), 1, 32);
                                rawDay = d === null ? rawDay : String(d).padStart(2, '0');
                            }
                            formatted += rawDay;
                        }
                    }
                }
            }
        }

        e.target.value = formatted;
        // Clear custom validity while typing; we'll enforce on blur/submit
        if (e.target.validity && e.target.validity.customError) {
            e.target.setCustomValidity('');
        }
    });

    // Handle backspace to remove slashes properly
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace') {
            const cursorPos = e.target.selectionStart;
            const value = e.target.value;

            // If backspacing on a slash, remove the slash and previous character
            if (cursorPos > 0 && value[cursorPos - 1] === '/') {
                e.preventDefault();
                const newValue = value.substring(0, cursorPos - 2) + value.substring(cursorPos);
                e.target.value = newValue;
                e.target.setSelectionRange(cursorPos - 2, cursorPos - 2);
            }
        }
    });

    // Validate when leaving the field
    input.addEventListener('blur', function (e) {
        const result = validateBsDateString(e.target.value);
        e.target.setCustomValidity(result.valid ? '' : result.message);
        if (!result.valid) e.target.reportValidity();
    });
}

// Render ballot parties dynamically from storage
function renderBallotParties() {
    const grid = document.querySelector('.icon-ballot-grid');
    if (!grid) return;

    const parties = getParties();
    grid.innerHTML = '';

    parties.forEach((party, index) => {
        const inputId = `party-${party.id}-${index}`;
        const cell = document.createElement('div');
        cell.className = 'icon-ballot-cell';
        cell.innerHTML = `
            <input type="radio" name="vote" id="${inputId}" value="${party.id}" required>
            <label for="${inputId}" class="icon-card">
                <span class="icon-emoji">${party.emoji || '🗳️'}</span>
                <div class="icon-text">
                    <div class="icon-title">${party.name}</div>
                    <div class="icon-sub">Candidate: ${party.candidate || 'N/A'}</div>
                </div>
                <div class="icon-checkbox"></div>
            </label>
        `;
        grid.appendChild(cell);
    });
}



// Custom Error Modal
function showCustomError(message) {
    const modal = document.getElementById('custom-error-modal');
    const msgElement = document.getElementById('custom-error-message');
    const titleElement = document.getElementById('custom-error-title');
    const closeBtn = document.getElementById('custom-error-close');

    const lang = localStorage.getItem('selectedLanguage') || 'en';

    if (modal && msgElement) {
        msgElement.textContent = message;

        // Localize Modal UI
        if (titleElement) {
            titleElement.textContent = lang === 'np' ? 'त्रुटि' : 'Error';
        }
        if (closeBtn) {
            closeBtn.textContent = lang === 'np' ? 'बन्द गर्नुहोस्' : 'Close';
        }

        modal.style.display = 'flex';

        if (closeBtn) {
            closeBtn.onclick = function () {
                modal.style.display = 'none';
            };
        }

        // Close on outside click
        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    } else {
        alert(message); // Fallback
    }
}

// Check if voter is under 18 based on BS date
function isUnder18BS(dobString) {
    if (!dobString) return true; // Default to blocked if empty

    const cleanDob = dobString.trim().replace(/[-.]/g, '/');
    const parts = cleanDob.split('/');
    if (parts.length !== 3) return true;

    const birthYear = parseInt(parts[0], 10);
    const birthMonth = parseInt(parts[1], 10);
    const birthDay = parseInt(parts[2], 10);

    if (isNaN(birthYear) || isNaN(birthMonth) || isNaN(birthDay)) return true;

    // Current BS date: Magh 14, 2082 (corresponds to Jan 28, 2026 AD)
    const currentBsYear = 2082;
    const currentBsMonth = 10;
    const currentBsDay = 14;

    let age = currentBsYear - birthYear;

    // Precise age calculation
    if (currentBsMonth < birthMonth || (currentBsMonth === birthMonth && currentBsDay < birthDay)) {
        age--;
    }

    console.log(`Checking age: Born ${birthYear}/${birthMonth}/${birthDay}, Current ${currentBsYear}/${currentBsMonth}/${currentBsDay} -> Age: ${age}`);
    return age < 18;
}

function initializeRegistrationPage() {
    const registrationFormEn = document.getElementById('registration-form-en');
    const registrationFormNp = document.getElementById('registration-form-np');

    // Load saved language preference
    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    if (window.switchLanguage) {
        switchLanguage(savedLang);
    }

    // Add auto-formatting to date inputs (BS format: YYYY/MM/DD)
    const dobEn = document.getElementById('dob-en');
    const dobNp = document.getElementById('dob-np');
    if (dobEn) formatDateInput(dobEn);
    if (dobNp) formatDateInput(dobNp);

    if (registrationFormEn) {
        registrationFormEn.addEventListener('submit', function (e) {
            e.preventDefault();
            handleRegistration('en');
        });
    }

    if (registrationFormNp) {
        registrationFormNp.addEventListener('submit', function (e) {
            e.preventDefault();
            handleRegistration('np');
        });
    }
}

function handleRegistration(lang) {
    const form = lang === 'np'
        ? document.getElementById('registration-form-np')
        : document.getElementById('registration-form-en');

    if (!form) return;

    // Helper to Title Case names (e.g., "gaurab ghale" -> "Gaurab Ghale")
    const toTitleCase = (str) => {
        return str.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    };

    const formData = new FormData(form);
    const voterData = {
        voterId: formData.get('voterId').toString().trim().toUpperCase(), // Force Uppercase ID
        fullName: toTitleCase(formData.get('fullName').toString().trim()), // Force Title Case Name
        dateOfBirth: formData.get('dateOfBirth')
    };

    // Validate data
    if (!voterData.voterId || !voterData.fullName || !voterData.dateOfBirth) {
        alert(lang === 'np'
            ? 'कृपया सबै फिल्डहरू भर्नुहोस्'
            : 'Please fill in all fields');
        return;
    }

    // 2. Validate Age (Under 18)
    if (isUnder18BS(String(voterData.dateOfBirth))) {
        showCustomError(lang === 'np'
            ? 'तपाईं मतदान गर्न सक्नुहुन्न'
            : 'You cannot Vote');
        return;
    }

    // Validate DOB bounds (month/day range)
    const dobInput = lang === 'np' ? document.getElementById('dob-np') : document.getElementById('dob-en');
    if (dobInput) {
        const result = validateBsDateString(String(voterData.dateOfBirth || ''));
        dobInput.setCustomValidity(result.valid ? '' : result.message);
        if (!result.valid) {
            dobInput.reportValidity();
            return;
        }
    }

    // Start of Security Check
    // Get the data from face recognition
    const knownVoterData = JSON.parse(localStorage.getItem('voterData') || '{}');

    // Check if we have recognized data to compare against
    if (knownVoterData.voterId && knownVoterData.fullName) {
        // Normalize for comparison (lowercase, trimmed)
        const inputId = voterData.voterId.trim().toUpperCase();
        const knownCode = (knownVoterData.voterCode || knownVoterData.voterId).toString().trim().toUpperCase();

        const inputName = voterData.fullName.trim().toLowerCase();
        const knownName = knownVoterData.fullName.trim().toLowerCase();

        // 1. Validate Voter ID Match with Face Recognition result
        if (inputId !== knownCode) {
            showCustomError(lang === 'np'
                ? `तपाईंको मतदाता परिचयपत्र नम्बर मेल खाएन`
                : `Your voter id does not match`);
            return;
        }

        // 2. Validate Name Match with Face Recognition result
        if (!inputName.includes(knownName)) {
            showCustomError(lang === 'np'
                ? `तपाईंको मतदाता नाम मेल खाएन`
                : `Your voter name does not match`);
            return;
        }
    }

    // 3. BACKEND VERIFICATION (Verify DOB and ID against Database)
    // Show a loading state or disable button? Let's just do the fetch.
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = lang === 'np' ? 'प्रमाणित गर्दै...' : 'Verifying...';

    fetch("http://localhost:8000/verify_voter_details", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            voter_id: voterData.voterId,
            full_name: voterData.fullName,
            dob: voterData.dateOfBirth
        }),
    })
        .then(res => res.json())
        .then(data => {
            if (data.verified) {
                // Persist voter list for admin view
                addVoter(voterData);

                // Save voter data to localStorage
                localStorage.setItem('voterData', JSON.stringify(voterData));

                // Redirect to ballot page
                window.location.href = 'ballot.html';
            } else {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;

                // Show error from backend
                const errorMsg = data.message || (lang === 'np' ? 'प्रमाणीकरण विफल भयो।' : 'Verification Failed.');
                showCustomError(errorMsg);
            }
        })
        .catch(err => {
            console.error("Verification error:", err);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            showCustomError(lang === 'np'
                ? 'सर्भरसँग जडान गर्न सकिएन'
                : 'Could not connect to verification server');
        });
}

// ============================================
// Ballot Page Functionality
// ============================================

function initializeBallotPage() {
    renderBallotParties();
    const ballotForm = document.getElementById('ballot-form');
    const constituencyButtons = document.querySelectorAll('.constituency-btn');
    const ballotPaperSection = document.getElementById('ballot-paper-section');
    const selectedConstituencyInput = document.getElementById('selected-constituency');
    const ballotConstNumber = document.getElementById('ballot-constituency-number');

    if (ballotForm) {
        ballotForm.addEventListener('submit', function (e) {
            e.preventDefault();
            handleVoteSubmission();
        });
    }

    // Handle constituency selection
    if (constituencyButtons && selectedConstituencyInput && ballotPaperSection && ballotConstNumber) {
        constituencyButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const selectedValue = btn.getAttribute('data-constituency');

                // Get voter data from storage to get voterId
                const voterData = JSON.parse(localStorage.getItem('voterData') || '{}');
                const voterId = voterData.voterId;

                if (!voterId) {
                    showCustomError('Voter information not found. Please register again.');
                    return;
                }

                // Show loading state on the button
                const originalText = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = 'Verifying...';

                // Fetch correct constituency from backend
                fetch(`http://localhost:8000/get_constituency?voter_id=${voterId}`)
                    .then(res => res.json())
                    .then(data => {
                        btn.disabled = false;
                        btn.innerHTML = originalText;

                        const dbConstituency = String(data.constituency);

                        if (dbConstituency !== selectedValue) {
                            // INCORRECT SELECTION
                            const currentLang = localStorage.getItem('selectedLanguage') || 'en';
                            const errorMsg = currentLang === 'np'
                                ? `प्रमाणीकरण विफल: गलत प्रतिनिधि सभा निर्वाचन क्षेत्र। तपाईको निर्वाचन क्षेत्र ${dbConstituency} हो।`
                                : `Verification Failed: Incorrect Parliamentary Constituency. Yours is ${dbConstituency}.`;

                            showCustomError(errorMsg);

                            // Visual feedback
                            btn.classList.add('error');
                            setTimeout(() => btn.classList.remove('error'), 2000);

                            // Hide ballot paper if it was somehow shown
                            ballotPaperSection.style.display = 'none';
                        } else {
                            // CORRECT SELECTION
                            selectedConstituencyInput.value = selectedValue;
                            ballotConstNumber.textContent = selectedValue;

                            // Visual selection
                            constituencyButtons.forEach(b => b.classList.remove('selected'));
                            btn.classList.add('selected');

                            // Reset party selection
                            const partyRadios = document.querySelectorAll('input[name="vote"]');
                            partyRadios.forEach(radio => radio.checked = false);

                            // Show ballot paper section
                            ballotPaperSection.style.display = 'block';

                            // Scroll into view for better UX
                            ballotPaperSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    })
                    .catch(err => {
                        console.error("Constituency verification error:", err);
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                        showCustomError('Could not verify constituency. Please check your connection.');
                    });
            });
        });
    }

    // Load voter data and display if needed
    const voterData = JSON.parse(localStorage.getItem('voterData') || '{}');
    if (voterData.voterId) {
        console.log('Voter registered:', voterData.fullName);
    }
}

function handleVoteSubmission() {
    const ballotForm = document.getElementById('ballot-form');
    const selectedVote = ballotForm.querySelector('input[name="vote"]:checked');
    const selectedConstituencyInput = document.getElementById('selected-constituency');
    const selectedConstituency = selectedConstituencyInput ? selectedConstituencyInput.value : '';

    if (!selectedConstituency) {
        alert('Please select your parliamentary constituency before submitting.\n\nकृपया मत पेश गर्नु अघि आफ्नो प्रतिनिधि सभा निर्वाचन क्षेत्र छान्नुहोस्।');
        return;
    }

    if (!selectedVote) {
        alert('Please select a candidate/party before submitting');
        return;
    }

    // Get voter data
    const voterData = JSON.parse(localStorage.getItem('voterData') || '{}');

    const parties = getParties();
    const selectedPartyObj = parties.find(p => p.id === selectedVote.value);
    const selectedParty = selectedPartyObj
        ? `${selectedPartyObj.name}${selectedPartyObj.candidate ? ' | ' + selectedPartyObj.candidate : ''}`
        : selectedVote.value;

    // Show confirmation alert
    const confirmMessage = `Do you want to finish and submit your vote?\n\nConstituency: ${selectedConstituency}\nSelected: ${selectedParty}\n\nकृपया आफ्नो मत पेश गर्न चाहनुहुन्छ?\n\nनिर्वाचन क्षेत्र: ${selectedConstituency}\nछानिएको: ${selectedParty}`;

    if (confirm(confirmMessage)) {
        // Save vote data
        const voteData = {
            voterId: voterData.voterId,
            voterName: voterData.fullName,
            selectedParty: selectedParty,
            constituency: selectedConstituency,
            voteTime: new Date().toLocaleString(),
            timestamp: new Date().toISOString()
        };

        addVote(voteData);

        // Notify Backend to mark user as voted
        fetch("http://localhost:8000/record_vote", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ voter_id: voterData.voterId })
        })
            .then(response => response.json())
            .then(res => {
                console.log("Vote recorded in backend:", res);
                // Redirect to success page regardless of backend result (UI priority)
                window.location.href = 'success.html';
            })
            .catch(err => {
                console.error("Failed to record vote in backend:", err);
                // Still redirect to success page so user feels it worked? 
                // Or show error? For now, proceed.
                window.location.href = 'success.html';
            });
    }
}

// ============================================
// Success Page Functionality
// ============================================

function initializeSuccessPage() {
    const voteData = JSON.parse(localStorage.getItem('voteData') || '{}');
    const savedLang = localStorage.getItem('selectedLanguage') || 'en';

    // Display vote details
    if (voteData.voterId) {
        document.getElementById('display-voter-id').textContent = voteData.voterId;
        document.getElementById('display-voter-name').textContent = voteData.voterName;
        document.getElementById('display-party').textContent = voteData.selectedParty;
        document.getElementById('display-time').textContent = voteData.voteTime;
    }

    // Switch language based on preference
    if (savedLang === 'np') {
        const englishElements = ['success-title', 'success-message', 'security-note'];
        const nepaliElements = ['success-title-np', 'success-message-np', 'security-note-np'];

        englishElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        nepaliElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'block';
        });
    }
}

// ============================================
// Admin Panel
// ============================================

function buildConstituencySummary() {
    const votes = getVotes();
    const summary = {};
    for (let i = 1; i <= 10; i++) {
        summary[i] = { total: 0, parties: {} };
    }

    votes.forEach(vote => {
        const key = vote.constituency || 'Unknown';
        if (!summary[key]) summary[key] = { total: 0, parties: {} };
        const partyName = vote.selectedParty || 'Unknown';
        summary[key].total += 1;
        summary[key].parties[partyName] = (summary[key].parties[partyName] || 0) + 1;
    });

    return summary;
}

function getColorForIndex(idx) {
    const palette = ['#f39c12', '#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#078e73ff', '#e67e22', '#f0d153ff', '#d19be7ff', '#34495e'];
    return palette[idx % palette.length];
}

function renderResultsSummary() {
    const container = document.getElementById('results-summary');
    if (!container) return;
    const summary = buildConstituencySummary();
    container.innerHTML = '';

    const allParties = getParties();

    Object.keys(summary).forEach(key => {
        const data = summary[key];
        const card = document.createElement('div');
        card.className = 'result-card';

        const partiesSorted = Object.entries(data.parties || {}).sort((a, b) => b[1] - a[1]);

        let html = `
            <h5>Constituency ${key}</h5>
            <div class="result-row"><span>Total votes</span><strong>${data.total}</strong></div>
            <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.1);" />
        `;

        if (partiesSorted.length === 0) {
            html += `<div class="result-row" style="justify-content: center;"><span>No votes yet</span></div>`;
        } else {
            let visibleHtml = '';
            let hiddenHtml = '';

            partiesSorted.forEach(([name, count], index) => {
                const parts = name.split(' | ');
                const pName = parts[0];
                const cName = parts[1] || pName;

                const partyObj = allParties.find(p => p.name === pName && (!parts[1] || p.candidate === parts[1]));
                const emojiChar = (partyObj && partyObj.emoji) ? partyObj.emoji : '🗳️';

                const percentage = data.total > 0 ? ((count / data.total) * 100).toFixed(2) : '0.00';

                const rowHtml = `
                    <div class="result-row" style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 12px; width: 75%;">
                            <div style="background: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.2); font-size: 1.5em; color: black; line-height: 1;">
                                ${emojiChar}
                            </div>
                            <div style="display: flex; flex-direction: column; overflow: hidden; text-align: left;">
                                <span style="font-weight: bold; font-size: 1.05em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #f8fafc;">${cName}</span>
                                <span style="font-size: 0.85em; opacity: 0.7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #94a3b8;">${pName}</span>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; width: 25%;">
                            <span style="font-weight: bold; font-size: 1.2em; color: #4ade80;">${count}</span>
                            <span style="font-size: 0.85em; opacity: 0.7; color: #94a3b8;">${percentage}%</span>
                        </div>
                    </div>
                `;

                if (index < 3) {
                    visibleHtml += rowHtml;
                } else {
                    hiddenHtml += rowHtml;
                }
            });

            html += visibleHtml;

            if (hiddenHtml !== '') {
                const hiddenContainerId = `hidden-parties-constituency-${key}`;
                html += `
                    <div id="${hiddenContainerId}" style="display: none;">
                        ${hiddenHtml}
                    </div>
                    <div class="result-row" style="justify-content: center; margin-top: 12px;">
                        <span style="color: #60a5fa; cursor: pointer; text-decoration: underline; font-size: 0.9em;" 
                              onclick="
                                  const el = document.getElementById('${hiddenContainerId}');
                                  if (el.style.display === 'none') {
                                      el.style.display = 'block';
                                      this.innerText = 'See less';
                                  } else {
                                      el.style.display = 'none';
                                      this.innerText = 'See more';
                                  }
                              ">See more</span>
                    </div>
                `;
            }
        }

        card.innerHTML = html;
        container.appendChild(card);
    });
}

function renderResultsChart() {
    const chartContainer = document.getElementById('results-chart');
    if (!chartContainer) return;

    // Fetch live voter list from backend to ensure accurate count
    fetch("http://localhost:8000/all_voters")
        .then(res => res.json())
        .then(voters => {
            const votes = getVotes();
            const allParties = getParties();
            
            const totalVoters = voters.length || 0;
            const totalVotesCast = votes.length;
            const nonVoters = Math.max(0, totalVoters - totalVotesCast);

            // Group by party
            const partyCounts = {};

            votes.forEach(vote => {
                const parts = vote.selectedParty.split(' | ');
                const pName = parts[0];
                partyCounts[pName] = (partyCounts[pName] || 0) + 1;
            });

            // The rest of the rendering logic remains the same but inside the .then block
            renderChartWithData(chartContainer, votes, allParties, totalVoters, totalVotesCast, nonVoters, partyCounts);
        })
        .catch(err => {
            console.error("Failed to fetch live voters for chart:", err);
            // Fallback or error message
            chartContainer.innerHTML = '<p class="admin-error">Failed to load live voter data.</p>';
        });
}

function renderChartWithData(chartContainer, votes, allParties, totalVoters, totalVotesCast, nonVoters, partyCounts) {
    chartContainer.innerHTML = '';
    chartContainer.className = 'pie-chart-container';
    chartContainer.style.position = 'relative';
    chartContainer.style.display = 'flex';
    chartContainer.style.justifyContent = 'center';
    chartContainer.style.alignItems = 'center';
    chartContainer.style.padding = '20px 0';
    chartContainer.style.minHeight = '350px';

    if (totalVotesCast === 0) {
        const emptyHeaderHtml = `
            <div style="width: 100%; text-align: left; margin-bottom: 25px;">
                <h3 style="margin: 0 0 8px 0; font-size: 1.4em; color: #f8fafc;">Total Votes</h3>
                <p style="margin: 0; color: #94a3b8; font-size: 0.95em;">
                    ${totalVoters} total voters | ${nonVoters} non voters | ${totalVotesCast} votes
                </p>
            </div>
        `;
        chartContainer.innerHTML = `
            <div style="width: 100%; display: flex; flex-direction: column; align-items: center; position: relative;">
                ${emptyHeaderHtml}
                <div style="width: 250px; height: 125px; background: #1e293b; border-radius: 150px 150px 0 0; margin-top: 20px; border: 1px solid rgba(255,255,255,0.05);"></div>
                <p style="color: #94a3b8; padding: 20px; font-weight: 500;">No votes casted yet.</p>
            </div>
        `;
        return;
    }

    const sortedParties = Object.keys(partyCounts).sort((a, b) => partyCounts[b] - partyCounts[a]);

    let svg = `<svg viewBox="-1 -1 2 2" style="transform: rotate(-90deg); width: 280px; height: 280px; display: block; overflow: visible; filter: drop-shadow(0 10px 15px rgba(0,0,0,0.3));">`;
    let cumulativePercent = 0;

    function getCoordinatesForPercent(percent) {
        const x = Math.cos(2 * Math.PI * percent);
        const y = Math.sin(2 * Math.PI * percent);
        return [x, y];
    }

    let legendHtml = '<div style="margin-top: 25px; display: flex; flex-direction: column; gap: 10px; width: 100%; max-width: 320px;">';

    sortedParties.forEach((pName, idx) => {
        const count = partyCounts[pName];
        const percent = count / totalVotesCast;
        const color = getColorForIndex(idx);
        const percentStr = (percent * 100).toFixed(2) + '%';

        const displayPName = pName.replace(' (Unified Marxist-Leninist)', '').replace('(Unified Marxist-Leninist)', '').trim();

        const tooltipText = `${displayPName}|${color}|${displayPName}: ${percentStr}`;

        if (percent === 1) {
            svg += `<circle r="1" cx="0" cy="0" fill="${color}" class="pie-slice" data-tooltip="${tooltipText}" cursor="pointer" />`;
        } else {
            const [startX, startY] = getCoordinatesForPercent(cumulativePercent);
            cumulativePercent += percent;
            const [endX, endY] = getCoordinatesForPercent(cumulativePercent);
            const largeArcFlag = percent > 0.5 ? 1 : 0;
            const pathData = [
                `M ${startX} ${startY}`,
                `A 1 1 0 ${largeArcFlag} 1 ${endX} ${endY}`,
                `L 0 0`
            ].join(' ');

            svg += `<path d="${pathData}" fill="${color}" class="pie-slice" data-tooltip="${tooltipText}" stroke="#0f172a" stroke-width="0.015" cursor="pointer" style="transition: opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1" />`;
        }

        legendHtml += `
            <div style="display: flex; align-items: center; gap: 10px; font-size: 0.95em;">
                <span style="width: 14px; height: 14px; background: ${color}; border-radius: 3px; display: inline-block;"></span>
                <span style="color: #f8fafc; font-weight: 500;">${displayPName}</span>
                <strong style="color: #94a3b8; margin-left: auto;">${percentStr}</strong>
            </div>
        `;
    });

    svg += `</svg>`;
    legendHtml += '</div>';

    const tooltipHtml = `
        <div id="pie-tooltip" style="position: absolute; display: none; background: #1e293b; color: white; padding: 14px; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); pointer-events: none; z-index: 1000; min-width: 220px; border: 1px solid rgba(255,255,255,0.1);">
            <div id="pie-tt-title" style="font-weight: bold; font-size: 1.05em; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px;"></div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span id="pie-tt-color" style="width: 14px; height: 14px; border-radius: 2px; display: inline-block;"></span>
                <span id="pie-tt-desc" style="font-size: 0.95em; color: #cbd5e1;"></span>
            </div>
        </div>
    `;

    const headerHtml = `
        <div style="width: 100%; text-align: left; margin-bottom: 25px;">
            <h3 style="margin: 0 0 8px 0; font-size: 1.4em; color: #f8fafc;">Total Votes</h3>
            <p style="margin: 0; color: #94a3b8; font-size: 0.95em;">
                ${totalVoters} total voters | ${nonVoters} non voters | ${totalVotesCast} votes
            </p>
        </div>
    `;

    chartContainer.innerHTML = `
        <div style="width: 100%; display: flex; flex-direction: column; align-items: center; position: relative;">
            ${headerHtml}
            ${svg}
            ${tooltipHtml}
            ${legendHtml}
        </div>
    `;

    const slices = chartContainer.querySelectorAll('.pie-slice');
    const tooltip = chartContainer.querySelector('#pie-tooltip');
    const ttTitle = chartContainer.querySelector('#pie-tt-title');
    const ttColor = chartContainer.querySelector('#pie-tt-color');
    const ttDesc = chartContainer.querySelector('#pie-tt-desc');

    const trackMouse = (e) => {
        if (!tooltip) return;
        const rect = chartContainer.getBoundingClientRect();
        // Keep tooltip within bounds somewhat
        let x = e.clientX - rect.left + 15;
        let y = e.clientY - rect.top + 15;
        tooltip.style.left = x + 'px';
        tooltip.style.top = y + 'px';
    };

    slices.forEach(slice => {
        slice.addEventListener('mouseover', (e) => {
            const data = slice.getAttribute('data-tooltip').split('|');
            ttTitle.innerText = data[0];
            ttColor.style.background = data[1];
            ttDesc.innerText = data[2];
            tooltip.style.display = 'block';
            trackMouse(e);
        });
        slice.addEventListener('mousemove', trackMouse);
        slice.addEventListener('mouseout', () => {
            tooltip.style.display = 'none';
        });
    });
}

function renderAgeGroupTable() {
    const container = document.getElementById('age-group-summary-container');
    if (!container) return;

    fetch("http://localhost:8000/age_group_summary")
        .then(res => res.json())
        .then(data => {
            const order = ["18-25", "26-35", "36-45", "46-60", "60 above"];

            let tableHtml = `
                <table class="voter-table age-summary-table">
                    <thead>
                        <tr>
                            <th>Age Group</th>
                            <th>No of Voter</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            order.forEach(group => {
                tableHtml += `
                    <tr>
                        <td>${group}</td>
                        <td>${data[group] || 0}</td>
                    </tr>
                `;
            });

            tableHtml += `
                    </tbody>
                </table>
            `;

            container.innerHTML = tableHtml;
        })
        .catch(err => {
            console.error("Failed to fetch age group summary:", err);
            container.innerHTML = "<p class='admin-error'>Failed to load age summary</p>";
        });
}




function renderVoterTable() {
    const tableBody = document.querySelector('#voter-table tbody');
    const summaryBox = document.getElementById('voter-summary');
    if (!tableBody || !summaryBox) return;

    fetch("http://localhost:8000/all_voters")
        .then(res => res.json())
        .then(voters => {
            tableBody.innerHTML = '';
            voters.forEach((voter, idx) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${voter.voter_id || '-'}</td>
                    <td>${voter.full_name || '-'}</td>
                    <td>${voter.date_of_birth || '-'}</td>
                    <td>${voter.parliamentary_constituency || '-'}</td>
                `;
                tableBody.appendChild(row);
            });
            summaryBox.textContent = `Total registered voters: ${voters.length}`;
        })
        .catch(err => {
            console.error("Failed to fetch voters:", err);
            // Fallback to local storage if needed, or show error
            summaryBox.textContent = "Error loading voter list";
        });
}



function populateDeleteSelect() {
    const select = document.getElementById('admin-delete-select');
    if (!select) return;
    const parties = getParties();
    select.innerHTML = '';
    parties.forEach(party => {
        const opt = document.createElement('option');
        opt.value = party.id;
        opt.textContent = `${party.name} (${party.candidate || 'N/A'})`;
        select.appendChild(opt);
    });
}

function setActiveAdminTab(targetId) {
    const tabs = document.querySelectorAll('.admin-tab');
    const sections = document.querySelectorAll('.admin-section');
    tabs.forEach(tab => {
        const isActive = tab.dataset.target === targetId;
        tab.classList.toggle('active', isActive);
    });
    sections.forEach(section => {
        section.style.display = section.id === targetId ? 'flex' : 'none';
    });

    if (targetId === 'admin-results') {
        renderResultsSummary();
        renderResultsChart();
        renderAgeGroupTable();
    }
    if (targetId === 'admin-voters') {
        renderVoterTable();
    }
}

// Make Admin Modal globally accessible for inline onclick fallback
window.openAdminModal = function () {
    const modal = document.getElementById('admin-modal');
    const authCard = document.getElementById('admin-auth');
    const dashboard = document.getElementById('admin-dashboard');

    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        if (authCard) authCard.style.display = 'block';
        if (dashboard) dashboard.style.display = 'none';
        console.log('Admin Modal Opened via Global Function');
    } else {
        console.error('Admin modal not found');
    }
};

function initializeAdminPanel() {
    const adminBtn = document.getElementById('admin-button');
    const modal = document.getElementById('admin-modal');
    const closeBtn = document.getElementById('admin-close');

    const authCard = document.getElementById('admin-auth');
    const dashboard = document.getElementById('admin-dashboard');
    const passwordInput = document.getElementById('admin-password');
    const errorText = document.getElementById('admin-auth-error');
    const authSubmit = document.getElementById('admin-auth-submit');

    if (!adminBtn || !modal || !dashboard) {
        console.error('Admin panel elements not found:', { adminBtn, modal, dashboard });
        return;
    }

    const openModal = () => {
        window.openAdminModal();
        // Also clear password field if possible, handled in global or here
        if (passwordInput) passwordInput.value = '';
        if (errorText) errorText.style.display = 'none';
    };

    const closeModal = () => {
        modal.style.display = 'none';
        // Restore background scrolling
        document.body.style.overflow = '';
    };
    window.closeAdminModal = closeModal;

    adminBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Admin button detected click (listener)');
        openModal();
    });
    // ... rest of the function remains similar or we can rely on existing
    // We need to keep the event listeners for authSubmit etc.

    closeBtn && closeBtn.addEventListener('click', closeModal);

    authSubmit && authSubmit.addEventListener('click', () => {
        const pwd = (passwordInput.value || '').trim();
        if (pwd === ADMIN_PASSWORD) {
            authCard.style.display = 'none';
            dashboard.style.display = 'flex';
            errorText.style.display = 'none';
            populateDeleteSelect();
            setActiveAdminTab('admin-update');
        } else {
            errorText.style.display = 'block';
        }
    });

    passwordInput && passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            authSubmit.click();
        }
    });

    const tabs = document.querySelectorAll('.admin-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => setActiveAdminTab(tab.dataset.target));
    });

    const addForm = document.getElementById('admin-add-party-form');
    if (addForm) {
        addForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('party-name').value.trim();
            const candidate = document.getElementById('party-candidate').value.trim();
            const emoji = document.getElementById('party-symbol').value.trim() || '🗳️';
            if (!name || !candidate) return;
            const party = {
                id: `party-${Date.now()}`,
                name,
                candidate,
                emoji
            };
            addParty(party);
            populateDeleteSelect();
            addForm.reset();
            alert('Party added.');
        });
    }

    const deleteBtn = document.getElementById('admin-delete-button');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const select = document.getElementById('admin-delete-select');
            if (!select || !select.value) return;
            const confirmed = confirm('Delete selected party from ballot?');
            if (confirmed) {
                deletePartyById(select.value);
                populateDeleteSelect();
                alert('Party deleted.');
            }
        });
    }

    const resetVotesBtn = document.getElementById('admin-reset-votes-button');
    if (resetVotesBtn) {
        resetVotesBtn.addEventListener('click', () => {
            const confirmed = confirm('Warning: This action will delete all currently casted votes and reset the voting process to the beginning. Proceed?');
            if (confirmed) {
                // Wipe local storage votes array natively
                localStorage.removeItem('votes');

                // Fetch backend to reset DB voter status flags
                fetch('http://localhost:8000/reset_all_votes')
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert('Success! All casted votes have been cleared. You are now ready to re-vote from the start.');
                            const refreshBtn = document.getElementById('admin-refresh-results');
                            if (refreshBtn) refreshBtn.click();
                        } else {
                            alert('Local votes wiped, but the backend returned an error.');
                        }
                    })
                    .catch(err => {
                        console.error('Reset backend connection error:', err);
                        alert('Local votes wiped natively. Ensure the backend handles the wipe.');
                    });
            }
        });
    }

    const refreshResults = document.getElementById('admin-refresh-results');
    if (refreshResults) {
        refreshResults.addEventListener('click', () => {
            renderResultsSummary();
            renderResultsChart();
            renderAgeGroupTable();
        });
    }

    const refreshVoters = document.getElementById('admin-refresh-voters');
    if (refreshVoters) {
        refreshVoters.addEventListener('click', () => {
            renderVoterTable();
        });
    }
}

// ============================================
// Language Page Functionality
// ============================================

function initializeLanguagePage() {
    // Language selection is handled in language.js
    // This function can be used for additional initialization if needed
}
