// Kie Image API Module
// Handles image generation using Kie AI / Z-Image Model

class KieImageAPI {
    constructor(apiKey, baseUrl = 'https://api.kie.ai') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    /**
     * Generate image using z-image model
     * @param {Object} params - Parameters for image generation
     * @param {string} params.prompt - Text description
     * @param {string} params.aspectRatio - '1:1', '16:9', etc.
     * @param {string} [params.callBackUrl] - Optional callback
     * @returns {Promise<Object>} - Result containing imageUrls
     */
    async generateImage({ prompt, aspectRatio = '1:1', callBackUrl = null }) {
        console.log('\n=== KIE IMAGE GENERATION ===');
        console.log('Model: z-image');
        console.log('Prompt:', prompt);

        const response = await fetch(`${this.baseUrl}/api/v1/jobs/createTask`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'z-image',
                input: {
                    prompt: prompt,
                    aspect_ratio: aspectRatio
                },
                callBackUrl: callBackUrl
            })
        });

        const result = await response.json();

        if (result.code !== 200) {
            throw new Error(result.msg || 'Failed to create image task');
        }

        const taskId = result.data.taskId;
        console.log('Image task started. ID:', taskId);

        return await this.pollTask(taskId);
    }

    /**
     * Poll for task completion
     * @param {string} taskId 
     * @param {number} maxAttempts 
     * @returns {Promise<Object>}
     */
    async pollTask(taskId, maxAttempts = 60) {
        for (let i = 0; i < maxAttempts; i++) {
            await this.sleep(2000); // 2 seconds delay

            const response = await fetch(
                `${this.baseUrl}/api/v1/jobs/recordInfo?taskId=${taskId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`
                    }
                }
            );

            const result = await response.json();

            if (result.code === 200) {
                const state = result.data.state;  // 'waiting', 'success', 'fail'

                if (state === 'success') {
                    // resultJson is a string, needs parsing
                    const resultData = JSON.parse(result.data.resultJson);
                    console.log('=== IMAGE GENERATION SUCCESS ===');
                    console.log('Results:', resultData.resultUrls);

                    return {
                        taskId: taskId,
                        imageUrls: resultData.resultUrls
                    };
                }

                if (state === 'fail') {
                    throw new Error(`Task failed: ${result.data.failMsg || 'Unknown error'}`);
                }

                // Still waiting
                if (window.logToUI) window.logToUI(`Polling... ${state}`);
            }
        }

        throw new Error('Image generation timeout');
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export
window.KieImageAPI = KieImageAPI;
