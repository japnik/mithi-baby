# 🍼 Mithi Baby - Application Architecture & Structure

Mithi Baby is a premium, AI-powered "Digital Nursery" that creates personalized lullabies and nursery rhymes for babies. It combines cutting-edge AI (Gemini, Suno) with a culturally rich, tactile UI.

---

## 🏗️ System Architecture

Mithi Baby follows a lightweight Python/JavaScript architecture with a focus on fast background processing and a premium frontend experience.

### 1. Frontend (Premium Digital Nursery)
- **Tech Stack**: Vanilla HTML5, CSS3 (Custom 3D Tactile Design), JavaScript (ES6+).
- **Core Files**:
  - `index.html`: Main landing page and library UI.
  - `css/styles.css`: Custom "Earth & Clay" design system, smooth animations, and tactile buttons.
  - `js/app.js`: State management, Stripe integration, and real-time status polling.

### 2. Backend (Orchestration Layer)
- **Tech Stack**: Python (HTTP Server), Supabase (DB & Storage), Stripe (Payments).
- **Core Files**:
  - `server.py`: Multi-threaded HTTP server handling API requests, Stripe webhooks, and process launching.
  - `process_song.py`: The "Brain". Orchestrates Gemini (lyrics), Suno (music/vocal), and local rendering.
  - `generate_video_task.py`: Specialized script for rendering high-quality karaoke videos with synced lyrics.

### 3. AI Integrations
- **Gemini AI**: Generates culturally sensitive, personalized lyrics in Punjabi, Hindi, and Hinglish.
- **Suno V5 (KIE.ai)**: Generates high-quality vocals and melodic music tracks.
- **DALL-E / Gemini Image**: Creates custom artwork for each song cover.

---

## 📂 Project Structure

```text
baby_songs/
├── mylori/
│   ├── frontend/        # Web UI and assets
│   │   ├── index.html   # Main UI
│   │   ├── css/         # Design system & styles
│   │   └── js/          # Frontend logic
│   ├── backend/         # Python services
│   │   ├── server.py    # Main API server
│   │   ├── process_song.py # Generation logic
│   │   ├── utils/       # Shared helpers (YouTube, Notifier)
│   │   ├── api_logs/    # JSON-based session logging
│   │   └── videos/      # Local processing & status files
│   └── README.md        # Technical setup guide
└── APP_STRUCTURE.md     # This architecture overview
```

---

## 🔄 Core Workflows

### 🎵 Song Generation Flow
1. **User Request**: User selects parameters (Baby Name, Language, Family Members, Occasion).
2. **Checkout**: Stripe handles the payment ($1.00 USD).
3. **Trigger**: Server launches `process_song.py` as a background task.
4. **AI Generation**:
   - `Gemini`: Writes personalized lyrics.
   - `Suno`: Generates music and gets aligned timestamps.
   - `Image Gen`: Creates a custom cover.
5. **Rendering**: `generate_video_task.py` crafts a karaoke video with synced lyrics.
6. **Cloud Sync**: Assets are uploaded to Supabase Storage; song metadata is saved to Supabase DB.
7. **Delivery**: User receives a "Ready" email, and the song appears in their Library.

### 📺 YouTube Integration
- Songs can be automatically published to the **Mithi Baby** YouTube channel with branded, unique titles:
  - Format: `[Name] — Personalized [Lang] [Occasion] ft. [Family] ([Month Year]) | Mithi Baby`

---

## 🗄️ External Services & APIs

| Service | Purpose |
| :--- | :--- |
| **Supabase** | Persistent Database & Asset Storage (Video/Audio/Lyrics) |
| **Stripe** | Secure payment processing |
| **Google Gemini** | LLM for lyrics and prompts |
| **Suno (KIE.ai)** | AI Music & Vocal generation |
| **Resend** | Transactional & Status emails |

---

## 🎨 Branding & Design
- **Theme**: "Earth & Clay" - A soothing palette of browns, clays, and creams.
- **Typography**: `Fredoka` for a playful yet premium nursery feel.
- **Interactions**: Tactile 3D buttons with bouncy transitions and subtle micro-animations.

---
*Created by Antigravity AI for MyLori | February 2026*
