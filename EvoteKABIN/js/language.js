// Language switching functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get language preference from localStorage or default to English
    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    
    // Initialize language on page load
    if (document.getElementById('english-content') && document.getElementById('nepali-content')) {
        switchLanguage(savedLang);
    }
    
    // Language toggle buttons
    const langEnBtn = document.getElementById('lang-en');
    const langNpBtn = document.getElementById('lang-np');
    
    if (langEnBtn) {
        langEnBtn.addEventListener('click', function() {
            switchLanguage('en');
            localStorage.setItem('selectedLanguage', 'en');
        });
    }
    
    if (langNpBtn) {
        langNpBtn.addEventListener('click', function() {
            switchLanguage('np');
            localStorage.setItem('selectedLanguage', 'np');
        });
    }
    
    // Language selection on language.html
    const languageOptions = document.querySelectorAll('.language-option');
    languageOptions.forEach(option => {
        option.addEventListener('click', function() {
            const selectedLang = this.getAttribute('data-lang');
            localStorage.setItem('selectedLanguage', selectedLang);
            
            // Remove previous selection
            languageOptions.forEach(opt => opt.classList.remove('selected'));
            // Add selection to clicked option
            this.classList.add('selected');
            
            // Redirect to registration page after a short delay
            setTimeout(() => {
                window.location.href = 'register.html';
            }, 300);
        });
    });
});

function switchLanguage(lang) {
    const englishContent = document.getElementById('english-content');
    const nepaliContent = document.getElementById('nepali-content');
    const englishForm = document.getElementById('english-form');
    const nepaliForm = document.getElementById('nepali-form');
    const langEnBtn = document.getElementById('lang-en');
    const langNpBtn = document.getElementById('lang-np');
    
    if (lang === 'np') {
        // Show Nepali content
        if (englishContent) englishContent.style.display = 'none';
        if (nepaliContent) nepaliContent.style.display = 'block';
        if (englishForm) englishForm.style.display = 'none';
        if (nepaliForm) nepaliForm.style.display = 'block';
        
        // Update button states
        if (langEnBtn) langEnBtn.classList.remove('active');
        if (langNpBtn) langNpBtn.classList.add('active');
    } else {
        // Show English content
        if (englishContent) englishContent.style.display = 'block';
        if (nepaliContent) nepaliContent.style.display = 'none';
        if (englishForm) englishForm.style.display = 'block';
        if (nepaliForm) nepaliForm.style.display = 'none';
        
        // Update button states
        if (langEnBtn) langEnBtn.classList.add('active');
        if (langNpBtn) langNpBtn.classList.remove('active');
    }
}
