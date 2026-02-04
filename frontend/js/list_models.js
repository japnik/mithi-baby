const fs = require('fs');

async function listModels() {
    try {
        const config = JSON.parse(fs.readFileSync('api/config.json', 'utf8'));
        const apiKey = config.GEMINI_API_KEY || config.gemini_api_key;

        if (!apiKey) {
            console.error("No API Key found in api/config.json");
            return;
        }

        console.log("Using API Key: " + apiKey.substring(0, 10) + "...");
        const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            console.error("API Error:", data.error);
        } else if (data.models) {
            console.log("\n=== AVAILABLE MODELS ===");
            data.models.forEach(m => {
                if (m.name.includes('gemini')) {
                    console.log(`- ${m.name.replace('models/', '')} (${m.displayName})`);
                    console.log(`  Supported methods: ${m.supportedGenerationMethods.join(', ')}`);
                }
            });
        } else {
            console.log("No models found or unexpected response format.");
            console.log(JSON.stringify(data, null, 2));
        }

    } catch (e) {
        console.error("Error:", e);
    }
}

listModels();
