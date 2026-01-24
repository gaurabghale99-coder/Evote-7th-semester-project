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
    initializeDataStores();
    initializeWelcomePage();
    initializeRegistrationPage();
    initializeBallotPage();
    initializeSuccessPage();
    initializeLanguagePage();
    initializeAdminPanel();
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
        return JSON.parse(localStorage.getItem('votes') || '[]');
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

    // Ensure initial state
    if (faceStatus) faceStatus.style.display = 'none';
    if (faceCard) faceCard.style.display = 'block';
    if (proceedBtn) proceedBtn.disabled = true;

    // Face recognition button handler
    if (startFaceRecognitionBtn) {
        startFaceRecognitionBtn.addEventListener('click', function () {
            startFaceRecognition();
        });
    }

    // Proceed button handler
    if (proceedBtn) {
        proceedBtn.addEventListener('click', function () {
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
        faceRecognitionCard.innerHTML = `
            <div class="face-icon">📷</div>
            <h3>Processing Face Recognition... | अनुहार पहिचान प्रक्रिया...</h3>
            <p>Please look at the camera | कृपया क्यामेरामा हेर्नुहोस्</p>
        `;
    }

    if (faceStatus) faceStatus.style.display = 'none';
    if (proceedBtn) proceedBtn.disabled = true;

    // Replace YOUR_BACKEND_IP with your backend laptop IP
    fetch("http://localhost:8000/face_login")
        .then(response => response.json())
        .then(data => {
            if (data.status === "allowed") {
                if (faceRecognitionCard) faceRecognitionCard.style.display = 'none';
                if (faceStatus) {
                    faceStatus.textContent = `Welcome ${data.name}! You can vote now. | स्वागत ${data.name}! अब तपाईं मतदान गर्न सक्नुहुन्छ।`;
                    faceStatus.style.display = 'block';

                    // Store voter data for later use in voting
                    const currentVoter = JSON.parse(localStorage.getItem('voterData') || '{}');
                    currentVoter.voterId = data.voter_id; // Store ID from backend
                    currentVoter.fullName = data.name;
                    localStorage.setItem('voterData', JSON.stringify(currentVoter));
                }
                if (proceedBtn) proceedBtn.disabled = false;
            } else if (data.status === "already_voted") {
                if (faceStatus) {
                    faceStatus.textContent = `${data.name} has already voted! | ${data.name} ले पहिले नै मतदान गरिसके।`;
                    faceStatus.style.display = 'block';
                }
            } else {
                if (faceStatus) {
                    faceStatus.textContent = `Face not recognized. Please try again. | अनुहार चिनिन सकेन। कृपया फेरि प्रयास गर्नुहोस्।`;
                    faceStatus.style.display = 'block';
                }
            }
        })
        .catch(err => {
            console.error("Error connecting to backend:", err);
            if (faceStatus) {
                faceStatus.textContent = "Cannot connect to backend. Please check the network. | ब्याकएन्डसँग जडान हुन सकेन। नेटवर्क जाँच गर्नुहोस्।";
                faceStatus.style.display = 'block';
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

    const formData = new FormData(form);
    const voterData = {
        voterId: formData.get('voterId'),
        fullName: formData.get('fullName'),
        dateOfBirth: formData.get('dateOfBirth')
    };

    // Validate data
    if (!voterData.voterId || !voterData.fullName || !voterData.dateOfBirth) {
        alert(lang === 'np'
            ? 'कृपया सबै फिल्डहरू भर्नुहोस्'
            : 'Please fill in all fields');
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

    // Persist voter list for admin view
    addVoter(voterData);

    // Save voter data to localStorage
    localStorage.setItem('voterData', JSON.stringify(voterData));

    // Redirect to ballot page
    window.location.href = 'ballot.html';
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
                const value = btn.getAttribute('data-constituency');
                selectedConstituencyInput.value = value;
                ballotConstNumber.textContent = value;

                // Visual selection
                constituencyButtons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');

                // Show ballot paper section
                ballotPaperSection.style.display = 'block';

                // Scroll into view for better UX
                ballotPaperSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    const palette = ['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ef4444', '#14b8a6', '#f97316', '#eab308', '#a855f7', '#f43f5e'];
    return palette[idx % palette.length];
}

function renderResultsSummary() {
    const container = document.getElementById('results-summary');
    if (!container) return;
    const summary = buildConstituencySummary();
    container.innerHTML = '';

    Object.keys(summary).forEach(key => {
        const data = summary[key];
        const card = document.createElement('div');
        card.className = 'result-card';

        const partiesSorted = Object.entries(data.parties || {}).sort((a, b) => b[1] - a[1]);
        const topLine = partiesSorted.length
            ? `${partiesSorted[0][0]} (${partiesSorted[0][1]} votes)`
            : 'No votes yet';

        card.innerHTML = `
            <h5>Constituency ${key}</h5>
            <div class="result-row"><span>Total votes</span><strong>${data.total}</strong></div>
            <div class="result-row"><span>Leading</span><strong>${topLine}</strong></div>
        `;

        if (partiesSorted.length > 1) {
            const rest = partiesSorted.slice(1, 3).map(([name, count]) => `<div class="result-row"><span>${name}</span><span>${count}</span></div>`).join('');
            card.innerHTML += rest;
        }

        container.appendChild(card);
    });
}

function renderResultsChart() {
    const chartContainer = document.getElementById('results-chart');
    if (!chartContainer) return;

    // Get Data
    const votes = getVotes();
    const voters = getVoterList();
    const totalVoters = voters.length || 0; // Avoid 0 division issues visually
    const totalVotesCast = votes.length;

    // Group by constituency
    const constituencyCounts = {};
    votes.forEach(vote => {
        const c = vote.constituency || 'Unknown';
        constituencyCounts[c] = (constituencyCounts[c] || 0) + 1;
    });

    // Clear Container
    chartContainer.innerHTML = '';
    // reset basic style to allow new flex layout
    chartContainer.className = 'storage-chart-3d';

    // 1. Header Section
    const headerHtml = `
        <div class="chart-3d-header">
            <h3>Total Votes</h3>
            <p>${totalVotesCast} votes / ${totalVoters} total voters | ${Math.max(0, totalVoters - totalVotesCast)} non voters</p>
        </div>
    `;

    // 2. Cylinder Construction
    // Sort constituencies to stack them consistently (e.g. 1 to 10)
    // We reverse so Const 1 is at top or bottom? Ideally bottom up.
    // CSS Stack: flex-direction: column-reverse puts first element at bottom.

    let segmentsHtml = '';
    const sortedKeys = Object.keys(constituencyCounts).sort((a, b) => Number(a) - Number(b));

    // Determine scale: proportional to totalVoters (capacity)
    // Avoid calculating percentages based on pure 0 voters if app is fresh
    const capacity = Math.max(totalVoters, 1);

    sortedKeys.forEach((key, idx) => {
        const count = constituencyCounts[key];
        const percentage = (count / capacity) * 100;
        const color = getColorForIndex(Number(key) - 1); // Use key 1-based index for color consistency

        segmentsHtml += `
            <div class="cylinder-segment" style="height: ${percentage}%; --seg-color: ${color};" title="Const ${key}: ${count} votes"></div>
        `;
    });

    // Non-voters filler
    // This fills the remaining space automatically if we use flex/height correctly, 
    // OR we can explicitly add a transparent segment.
    // Let's use a "filler" segment for non-voters at the top.
    const nonVoterCount = Math.max(0, totalVoters - totalVotesCast);
    const nonVoterPercentage = (nonVoterCount / capacity) * 100;

    // We put non-voter segment at the TOP (end of list if column-reverse)
    const nonVoterSegment = `<div class="cylinder-segment segment-empty" style="height: ${nonVoterPercentage}%;"></div>`;


    // 3. Legend Construction
    let legendItemsHtml = '';
    for (let i = 1; i <= 10; i++) {
        const key = String(i);
        const count = constituencyCounts[key] || 0;
        const color = getColorForIndex(Number(key) - 1);
        legendItemsHtml += `
            <div class="legend-item">
                <span class="legend-dot" style="background-color: ${color}"></span>
                <div class="legend-info">
                    <span class="legend-label">Parliamentary constituency ${key}</span>
                    <span class="legend-value">${count} votes</span>
                </div>
            </div>
       `;
    }

    // Assemble Full HTML
    chartContainer.innerHTML = `
        ${headerHtml}
        <div class="cylinder-chart-body">
            <div class="cylinder-wrapper">
                <div class="cylinder-container">
                    <div class="cylinder-top-cap"></div>
                    <div class="cylinder-segments-stack">
                         ${nonVoterSegment} 
                         ${segmentsHtml} 
                         <!-- Note: flex-direction column means top element is top. 
                              So Non-voter should be first in DOM for "top", or last if column-reverse.
                              We will use standard Flex Column, so Non-Voter First = Top.
                          -->
                    </div>
                    <div class="cylinder-bottom-cap"></div>
                    <!-- Overlay glass effect -->
                    <div class="cylinder-glass"></div>
                </div>
            </div>
            <div class="chart-legend">
                ${legendItemsHtml}
            </div>
        </div>
    `;
}

function renderVoterTable() {
    const tableBody = document.querySelector('#voter-table tbody');
    const summaryBox = document.getElementById('voter-summary');
    if (!tableBody || !summaryBox) return;

    const voters = getVoterList();
    tableBody.innerHTML = '';

    voters.forEach((voter, idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${idx + 1}</td>
            <td>${voter.voterId || '-'}</td>
            <td>${voter.fullName || '-'}</td>
            <td>${voter.dateOfBirth || '-'}</td>
        `;
        tableBody.appendChild(row);
    });

    summaryBox.textContent = `Total registered voters: ${voters.length}`;
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
    }
    if (targetId === 'admin-voters') {
        renderVoterTable();
    }
}

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
        if (!modal || !dashboard) {
            console.error('Modal or dashboard not found');
            return;
        }
        // Show the modal
        modal.style.display = 'flex';
        // Prevent background scrolling
        document.body.style.overflow = 'hidden';

        // Show authentication card logic:
        if (authCard) {
            authCard.style.display = 'block';
            if (passwordInput) passwordInput.value = '';
        }

        // Hide dashboard initially
        dashboard.style.display = 'none';

        // Hide error text
        if (errorText) {
            errorText.style.display = 'none';
        }
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
        console.log('Admin button clicked');
        openModal();
        return false;
    });
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

    const refreshResults = document.getElementById('admin-refresh-results');
    if (refreshResults) {
        refreshResults.addEventListener('click', () => {
            renderResultsSummary();
            renderResultsChart();
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
