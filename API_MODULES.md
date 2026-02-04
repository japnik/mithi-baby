# MyLori API Modules

## Overview
The application uses modularized API integrations for better code organization and maintainability.

## Files

### `js/gemini-api.js`
Handles lyrics generation using Google's Gemini Flash Latest model.

**Class:** `GeminiAPI`

**Methods:**
- `generateLyrics({ babyName, language, characters, occasion })` - Generates song lyrics with structured JSON output

**Features:**
- Uses `gemini-flash-latest` model (always latest version)
- Structured JSON output with schema validation
- Language-specific script requirements (Gurmukhi, Devanagari, Latin)
- Culturally appropriate lyrics generation

### `js/suno-api.js`
Handles music and video generation using Suno V5 API.

**Class:** `SunoAPI`

**Methods:**
- `generateMusic({ lyrics, title, language })` - Creates music with custom lyrics
- `generateVideo(musicData)` - Generates video from audio
- `pollMusicGeneration(taskId, title, lyrics)` - Polls for music completion
- `pollVideoGeneration(taskId)` - Polls for video completion

**Features:**
- Custom mode with Gemini-generated lyrics
- Automatic polling with progress updates
- Female vocals, traditional lullaby style

## Usage Example

```javascript
// Initialize APIs
const gemini = new GeminiAPI(CONFIG.GEMINI_API_KEY);
const suno = new SunoAPI(CONFIG.SUNO_API_KEY, CONFIG.SUNO_BASE_URL);

// Generate lyrics
const lyrics = await gemini.generateLyrics({
    babyName: 'Liv Kaur',
    language: 'Punjabi',
    characters: ['Papa', 'Mummy', 'Dadu'],
    occasion: 'Lori (Lullaby)'
});

// Generate music
const musicData = await suno.generateMusic({
    lyrics: lyrics.text,
    title: lyrics.title,
    language: 'Punjabi'
});

// Generate video
const videoData = await suno.generateVideo(musicData);
```

## Integration

Both modules are loaded before `app.js` in `index.html`:
```html
<script src="js/gemini-api.js"></script>
<script src="js/suno-api.js"></script>
<script src="js/app.js"></script>
```
