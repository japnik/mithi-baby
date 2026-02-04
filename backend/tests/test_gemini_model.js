const fs = require('fs');

async function testGeminiPro() {
    try {
        // 1. Get API Key
        const config = JSON.parse(fs.readFileSync('api/config.json', 'utf8'));
        const apiKey = config.GEMINI_API_KEY || config.gemini_api_key;

        if (!apiKey) {
            console.error("No API Key found");
            return;
        }

        console.log(`Testing Model: gemini-pro-latest`);
        console.log(`Endpoint: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent`);

        // 2. Prepare Request (Same prompt structure as app)
        const prompt = `Create a Lori (Lullaby) song in Punjabi for baby Agam Singh.
Mention Papa and Mummy.
Use Gurmukhi script.
Return JSON with title, lyrics, musicStyle, imagePrompt.`;

        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key=${apiKey}`;

        // 3. Send Request
        console.log("Sending request...");
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{
                    parts: [{ text: prompt }]
                }],
                generationConfig: {
                    temperature: 0.9,
                    maxOutputTokens: 2048,
                    responseMimeType: "application/json"
                }
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        const content = data.candidates[0].content.parts[0].text;

        console.log("\n=== SUCCESS! Model Works ===");
        console.log("Response Preview:\n", content.substring(0, 500) + "...");

    } catch (e) {
        console.error("\n❌ TEST FAILED:", e.message);
    }
}

testGeminiPro();
