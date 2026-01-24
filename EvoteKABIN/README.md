# E-Vote: Intelligent Online Voting System - Frontend

## Project Overview
This is the frontend part of the E-Vote system, an intelligent online voting platform with bilingual support (English and Nepali).

## File Structure

```
E-Vote/
├── index.html          # Welcome page with face recognition option
├── language.html       # Language selection page
├── register.html       # Voter registration page
├── ballot.html         # Ballot paper with party selection
├── success.html        # Vote success confirmation page
├── css/
│   └── style.css       # Main stylesheet
├── js/
│   ├── main.js         # Main JavaScript functionality
│   └── language.js     # Language switching logic
└── README.md           # This file
```

## Features

### 1. Welcome Page (`index.html`)
- Bilingual welcome message (English/Nepali)
- Face recognition option
- Language toggle
- Proceed to voting button (enabled after face recognition)

### 2. Language Selection (`language.html`)
- Choose between English and Nepali
- Redirects to registration page

### 3. Voter Registration (`register.html`)
- Voter ID input
- Full Name input
- Date of Birth input
- Form validation
- Bilingual form support

### 4. Ballot Paper (`ballot.html`)
- Nepal-style ballot paper format
- Multiple candidates/parties with emoji symbols
- Radio button selection (one vote only)
- Instructions in both languages
- Confirmation alert before submission

### 5. Success Page (`success.html`)
- Vote confirmation
- Display vote details
- Security note
- Return to home option

## Usage

1. Open `index.html` in a web browser
2. Complete face recognition (simulated)
3. Select language preference
4. Register with Voter ID, Name, and Date of Birth
5. Select candidate/party on ballot paper
6. Confirm and submit vote
7. View success confirmation

## Technologies Used

- HTML5
- CSS3 (with modern styling and animations)
- Vanilla JavaScript (ES6+)
- LocalStorage for data persistence
- Responsive design

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Notes

- Face recognition is currently simulated (2.5 second delay)
- Data is stored in browser localStorage
- Form validation is implemented
- All pages are responsive and mobile-friendly

## Future Enhancements

- Integration with actual CNN face recognition API
- Backend API integration
- Database connectivity
- Real-time vote counting
- Admin dashboard
- Observer view
