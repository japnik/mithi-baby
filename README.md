# MyLori - Setup Instructions

## Quick Start

### 🚀 Recommended Method (Auto-Fix)
The easiest way to run the server without Python errors is:

```bash
./run_server.sh
```
*(This automatically creates a safe environment and installs everything for you)*

### Manual Method

1. **Add your Gemini API Key**
   - Open `api/config.json`
   - Replace `YOUR_GEMINI_API_KEY_HERE` with your actual Gemini API key

2. **Run the application**
   ```bash
   ```bash
   # Run the application with backend (Required for video generation)
   python3 server.py
   ```

3. **Open in browser**
   - Navigate to `http://localhost:8000`

## Features

- **Multi-language Support**: Punjabi, Hindi, and Hinglish
- **Personalized Songs**: Custom lyrics with baby's name
- **Character Selection**: Papa, Mummy, Dadu, Dadi, Nanu, Nani, or custom
- **Multiple Occasions**: Bedtime, playtime, milestones, festivals, and more
- **AI-Generated**: Gemini AI for lyrics, Suno V5 for music
- **Video Generation**: Automatic music video creation
- **Song Library**: Save and replay all created songs

## API Keys Required

1. **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Suno API Key**: Already configured (KIE.ai)

## File Structure

```
mylori/
├── index.html          # Main HTML structure
├── css/
│   └── styles.css      # Premium styling
├── js/
│   └── app.js          # Application logic
├── assets/
│   └── logo.png        # App Logo
├── api/
│   └── config.json     # API configuration
└── README.md           # This file
```

## How It Works

1. User fills in baby's name, selects language, character, and occasion
2. Gemini AI generates culturally appropriate lyrics
3. Suno V5 API creates music with female vocals
4. Suno API generates a music video with visualizations
5. Song is saved to browser's LocalStorage
6. User can replay songs anytime from the library

## Deployment

### Option 1: Netlify
```bash
# Deploy to Netlify
cd mylori
netlify deploy --prod
```

### Option 2: GitHub Pages
1. Push to GitHub repository
2. Enable GitHub Pages in repository settings
3. Select main branch and /mylori folder

### Option 3: Any Static Host
Upload the `mylori` folder to any static hosting service (Vercel, Cloudflare Pages, etc.)

## Troubleshooting

**Issue**: Songs not generating
- Check that Gemini API key is correctly set in `api/config.json`
- Check browser console for errors
- Ensure internet connection is stable

**Issue**: Video not loading
- Videos are hosted on Suno's servers for 14 days
- Download videos if you want to keep them permanently

**Issue**: Songs not saving
- Check that browser allows LocalStorage
- Try a different browser if issues persist

## Future Enhancements

- [ ] Add database backend for persistent storage
- [ ] Implement user accounts
- [ ] Add sharing functionality
- [ ] Create playlists
- [ ] Add more languages
- [ ] Custom music styles
