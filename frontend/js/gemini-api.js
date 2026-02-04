// Gemini API Module
// Handles lyrics generation using Gemini Flash Latest with structured JSON output

class GeminiAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.model = 'gemini-pro-latest'; // User requested "pro latest"
        this.baseUrl = 'https://generativelanguage.googleapis.com/v1beta/models';
    }

    /**
     * Generate song lyrics using Gemini AI
     * @param {Object} params - Parameters for lyrics generation
     * @param {string} params.babyName - Baby's name
     * @param {string} params.language - Language (Punjabi, Hindi, Hinglish)
     * @param {Array<string>} params.characters - People to mention (Papa, Mummy, etc.)
     * @param {string} params.occasion - Occasion (Lori, Birthday, etc.)
     * @returns {Promise<Object>} - { title, lyrics, prompt }
     */
    async generateLyrics({ babyName, language, characters, occasion }) {
        const charactersText = characters.join(', ');

        // Handle Random occasion
        if (occasion === 'Random') {
            const randomOccasions = ['Playtime', 'Good Morning', 'Sweet Dreams', 'Bath Time', 'Tummy Time', 'Happy Moments'];
            occasion = randomOccasions[Math.floor(Math.random() * randomOccasions.length)];
        }

        // 1. Determine Occasion Category
        // 1. Unified Mood & Visuals (Always Lullaby/Soothing)
        // User USP: "Lullaby Only" brand identity

        let moodRequirements = `
- Tone: Soothing, gentle, slow, and calm (Sleep inducing lullaby)
- Themes: Sleep, sweet dreams, moon, stars, protection, warmth
- Context: ${occasion} (Weave in ${occasion} themes like 'Birthday Cake' or 'Diwali Lights' but keep it a soft lullaby)
- Rhythm: Slow, rocking lullaby style, melodic`;

        let visualStyle = "Soft lighting, dreamy, night time, stars, peaceful, cozy, magical glow, aesthetics";

        const scriptNames = {
            'Punjabi': 'Gurmukhi (ਪੰਜਾਬੀ)',
            'Hindi': 'Devanagari (हिन्दी)',
            'Hinglish': 'Latin (English)'
        };

        const prompt = `Create a ${occasion} song in ${language} for baby ${babyName}.

The song should mention and celebrate these people as important in the baby's life: ${charactersText}.

CRITICAL LANGUAGE REQUIREMENTS:
- CRITICAL: SCRIPT must be ${scriptNames[language]}.
- IF PUNJABI: Use GURMUKHI script (e.g. ਸੋ ਜਾ). DO NOT use Roman (English) characters.
- DO NOT use English or romanized text (unless language is Hinglish)
- Use authentic ${language} vocabulary and grammar

Requirements:
${moodRequirements}
- Culturally appropriate for ${language} families
- 4-6 short verses (each verse 2-4 lines)
- Include baby's name "${babyName}" naturally in the lyrics
- Mention each of these people lovingly: ${charactersText}
- Use ${language} script throughout
- Make it warm, loving, and comforting
- Include a repeating chorus that's easy to remember

            Please provide:
1. A beautiful title for the song (MUST include "${babyName}" and "${occasion}")
2. The complete lyrics
3. A detailed prompt for generating a cover image for this song.
   - CRITICAL: The image prompt must describe a SCENE WITHOUT ANY HUMANS OR PEOPLE.
   - DO NOT include babies, parents, or any human figures.
   - Focus on the occasion, atmosphere, magical elements, toys, nature, or abstract representations of the mood.
   - Style: Digital Art, ${visualStyle}, Magical, Dreamy.
   - Elements: Include specific elements for ${occasion} if applicable.
4. A detailed music style description (tags) for the AI music generator.
   - CRITICAL: Always a LULLABY.
   - FOCUS: Traditional Instruments (Bansuri/Flute, Sitar, Santoor, Harmonium, Soft Tabla, Sarangi).
   - KEYWORDS: "lullaby, soft, gentle, soothing, female vocals, traditional, peaceful, calming, acoustic, slow tempo".
   - Match the cultural vibe of the language.

Format your response as JSON:
{
  "title": "Song Title",
  "lyrics": "Full lyrics here...",
  "image_prompt": "Image generation prompt here...",
  "musicStyle": "Music style tags here"
}`;

        console.log('Sending request to Gemini:', { babyName, occasion, language });

        const apiUrl = `${this.baseUrl}/${this.model}:generateContent?key=${this.apiKey}`;

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{
                        parts: [{ text: prompt }]
                    }],
                    generationConfig: {
                        temperature: 0.9,
                        topP: 0.95,
                        maxOutputTokens: 8192,
                        responseMimeType: "application/json",
                        responseSchema: {
                            type: "object",
                            properties: {
                                title: {
                                    type: "string",
                                    description: "Title of the song in the target language"
                                },
                                lyrics: {
                                    type: "string",
                                    description: "Complete lyrics with proper line breaks using \\n"
                                },
                                musicStyle: {
                                    type: "string",
                                    description: "Elaborate music style string."
                                },
                                imagePrompt: {
                                    type: "string",
                                    description: "Prompt for generating cover art"
                                }
                            },
                            required: ["title", "lyrics", "imagePrompt", "musicStyle"]
                        }
                    }
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Gemini API Error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();

            // Extract JSON from response
            const content = data.candidates[0].content.parts[0].text;
            const parsed = JSON.parse(content);

            return {
                title: parsed.title,
                text: parsed.lyrics,
                lyrics: parsed.lyrics,
                script: scriptNames[language],
                imagePrompt: parsed.imagePrompt,
                musicStyle: parsed.musicStyle,
                prompt: prompt
            };

        } catch (error) {
            console.error('Gemini Generation Failed:', error);
            throw error;
        }
    }
}

// Export for use in other modules
window.GeminiAPI = GeminiAPI;
