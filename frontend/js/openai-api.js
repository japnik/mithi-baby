// OpenAI API Module
// Handles lyrics generation using OpenAI (GPT-4o) with structured JSON output

class OpenAIAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.model = 'gpt-4o'; // Using the latest capable model
        this.baseUrl = 'https://api.openai.com/v1/chat/completions';
    }

    /**
     * Generate song lyrics using OpenAI
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

        const systemPrompt = `You are a professional songwriter and poet specializing in culturally authentic lullabies for Indian families.
Your goal is to create beautiful, soothing, and high-quality lyrics.`;

        const userPrompt = `Create a ${occasion} song in ${language} for baby ${babyName}.

The song should mention and celebrate these people as important in the baby's life: ${charactersText}.

CRITICAL LANGUAGE REQUIREMENTS:
- CRITICAL: SCRIPT must be ${scriptNames[language]}.
- IF PUNJABI: Use GURMUKHI script (e.g. ਸੋ ਜਾ). DO NOT use Roman (English) characters.
- DO NOT use English or romanized text (unless language is Hinglish)
- Use authentic ${language} vocabulary and grammar. Avoid repetitive or simple connections. Write deep, meaningful, and poetic lyrics.

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

Response Format: JSON`;

        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: this.model,
                messages: [
                    { role: "system", content: systemPrompt },
                    { role: "user", content: userPrompt }
                ],
                temperature: 0.9,
                response_format: { type: "json_object" }
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        const content = data.choices[0].message.content;

        // Parse the JSON content
        const result = JSON.parse(content);

        console.log('=== OPENAI GENERATED LYRICS & PROMPT ===');
        console.log('Title:', result.title);
        console.log('Image Prompt:', result.image_prompt);

        return {
            title: result.title,
            text: result.lyrics,
            script: result.language_script || scriptNames[language], // Fallback if not provided
            imagePrompt: result.image_prompt,
            musicStyle: result.music_style,
            prompt: userPrompt
        };
    }
}

// Export for use in other modules
window.OpenAIAPI = OpenAIAPI;
