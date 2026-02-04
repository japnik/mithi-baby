// Suno API Module
// Handles music and video generation using Suno V5 API

class SunoAPI {
    constructor(apiKey, baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    /**
     * Generate music with custom lyrics
     * @param {Object} params - Parameters for music generation
     * @param {string} params.lyrics - Lyrics text
     * @param {string} params.title - Song title
     * @param {string} params.language - Language for style
     * @returns {Promise<Object>} - Music data with taskId, audioUrl, etc.
     */
    async generateMusic({ lyrics, title, language, style }) {
        const finalStyle = style || `${language} lullaby, soft, gentle, soothing, female vocals, traditional, peaceful, calming, tender, baby song`;

        console.log('\n=== SUNO MUSIC GENERATION ===');
        console.log('Title:', title);
        console.log('Style:', finalStyle);
        console.log('Using custom lyrics from Gemini');

        const response = await fetch(`${this.baseUrl}/api/v1/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: lyrics,  // Custom lyrics from Gemini
                customMode: true,  // Use provided lyrics
                style: finalStyle,
                title: title,
                instrumental: false,
                model: 'V5',
                vocalGender: 'f',
                callBackUrl: 'https://example.com/callback'
            })
        });

        const result = await response.json();

        console.log('=== SUNO API INITIAL RESPONSE ===');
        console.log('Full response:', JSON.stringify(result, null, 2));

        // Log to backend
        if (window.Logger) {
            Logger.log('Suno API Initial Response', {
                code: result.code,
                taskId: result.data?.taskId,
                fullResponse: result
            });
        }

        if (result.code !== 200) {
            throw new Error(result.msg || 'Failed to generate music');
        }

        const taskId = result.data.taskId;
        console.log('✅ Music generation started. Task ID:', taskId);

        if (window.Logger) {
            Logger.log('Music generation started', { taskId: taskId });
        }

        // Poll for completion
        return await this.pollMusicGeneration(taskId, title, lyrics);
    }

    /**
     * Get aligned lyrics (timestamps) for a generated song
     * @param {string} taskId - Suno task ID from music generation
     * @param {string} audioId - Audio ID
     * @returns {Promise<Object>} - Timestamp data
     */
    async getAlignedLyrics(taskId, audioId) {
        console.log(`Getting aligned lyrics for Task: ${taskId}, Audio: ${audioId}...`);

        if (window.Logger) {
            Logger.log('Starting timestamp fetch', { taskId, audioId });
        }

        const maxAttempts = 12; // 12 * 5s = 60s max wait

        for (let i = 0; i < maxAttempts; i++) {
            try {
                // Poll every 5s
                if (i > 0) await this.sleep(5000);

                console.log(`[Timestamp Poll ${i + 1}/${maxAttempts}] Requesting data...`);

                const response = await fetch(`${this.baseUrl}/api/v1/generate/get-timestamped-lyrics`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        taskId: taskId,
                        audioId: audioId
                    })
                });

                const data = await response.json();

                // Log raw response for debugging
                console.log(`[Timestamp Poll ${i + 1}] Response:`, data);

                if (data.code === 200 && data.data && data.data.alignedWords && data.data.alignedWords.length > 0) {
                    console.log('✅ Aligned lyrics fetched successfully');

                    if (window.Logger) {
                        Logger.log('Timestamp fetch success', {
                            wordCount: data.data.alignedWords.length,
                            sample: data.data.alignedWords.slice(0, 3)
                        });
                    }

                    return data;
                } else {
                    console.warn(`[Timestamp Poll ${i + 1}] Not ready or invalid format`, data);
                    // Continue polling
                }
            } catch (error) {
                console.error(`[Timestamp Poll ${i + 1}] Error:`, error);
                if (window.Logger) {
                    Logger.error(`Timestamp fetch attempt ${i + 1} failed`, error);
                }
            }
        }

        console.error('❌ Timestamp fetch TIMEOUT');
        if (window.Logger) {
            Logger.error('Timestamp fetch timed out after all attempts');
        }
        return null;
    }

    /**
     * Poll for music generation completion
     * @param {string} taskId - Suno task ID
     * @param {string} title - Song title
     * @param {string} lyrics - Lyrics text
     * @param {number} maxAttempts - Maximum polling attempts
     * @returns {Promise<Object>} - Music data
     */
    async pollMusicGeneration(taskId, title, lyrics, maxAttempts = 120) {
        console.log(`⏳ Polling for task ${taskId} (max ${maxAttempts} attempts, ~${maxAttempts * 5 / 60} minutes)`);

        for (let i = 0; i < maxAttempts; i++) {
            await this.sleep(5000); // Wait 5 seconds

            const response = await fetch(
                `${this.baseUrl}/api/v1/generate/record-info?taskId=${taskId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`
                    }
                }
            );

            const result = await response.json();

            // Log every 10th attempt
            if (i % 10 === 0) {
                console.log(`Poll attempt ${i + 1}/${maxAttempts}: Status = ${result.data?.status || 'UNKNOWN'}`);
            }

            if (result.code === 200 && result.data?.status === 'SUCCESS') {
                const track = result.data.response.sunoData[0];

                console.log('\n=== MUSIC GENERATED ===');
                console.log('Audio URL:', track.audioUrl);
                console.log('Duration:', track.duration, 's');

                return {
                    taskId: taskId,
                    audioId: track.id,
                    audioUrl: track.audioUrl,
                    imageUrl: track.imageUrl,
                    duration: track.duration,
                    title: track.title || title,
                    lyrics: lyrics
                };
            }

            if (result.data?.status === 'FAILED') {
                console.error('❌ Music generation FAILED:', result);
                throw new Error('Music generation failed');
            }

            // Notify progress (for UI updates)
            if (window.updateProgress) {
                const progress = 20 + Math.min((i / maxAttempts) * 40, 40);
                window.updateProgress(progress, `Creating music... ${Math.round((i / maxAttempts) * 100)}%`);
            }
        }

        console.error(`❌ Music generation TIMEOUT after ${maxAttempts} attempts`);
        throw new Error('Music generation timeout');
    }

    /**
     * Generate video from audio
     * @param {Object} musicData - Music data from generateMusic
     * @returns {Promise<Object>} - Video data with videoUrl
     */
    async generateVideo(musicData) {
        console.log('\n=== VIDEO GENERATION ===');
        console.log('Audio ID:', musicData.audioId);

        const response = await fetch(`${this.baseUrl}/api/v1/mp4/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                taskId: musicData.taskId,
                audioId: musicData.audioId,
                domainName: 'mylori.app',
                callBackUrl: 'https://example.com/callback'
            })
        });

        const result = await response.json();

        if (result.code !== 200) {
            throw new Error(result.msg || 'Failed to generate video');
        }

        const taskId = result.data.taskId;
        console.log('Video generation started. Task ID:', taskId);

        // Poll for completion
        return await this.pollVideoGeneration(taskId);
    }

    /**
     * Poll for video generation completion
     * @param {string} taskId - Suno video task ID
     * @param {number} maxAttempts - Maximum polling attempts
     * @returns {Promise<Object>} - Video data
     */
    async pollVideoGeneration(taskId, maxAttempts = 60) {
        for (let i = 0; i < maxAttempts; i++) {
            await this.sleep(5000);

            const response = await fetch(
                `${this.baseUrl}/api/v1/mp4/record-info?taskId=${taskId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`
                    }
                }
            );

            const result = await response.json();

            if (result.code === 200 && result.data?.successFlag === 'SUCCESS') {
                console.log('\n=== VIDEO GENERATED ===');
                console.log('Video URL:', result.data.response.videoUrl);

                return {
                    videoUrl: result.data.response.videoUrl
                };
            }

            // Notify progress (for UI updates)
            if (window.updateProgress) {
                const progress = 65 + Math.min((i / maxAttempts) * 30, 30);
                window.updateProgress(progress, `Creating video... ${Math.round((i / maxAttempts) * 100)}%`);
            }
        }

        throw new Error('Video generation timeout');
    }

    /**
     * Helper function to sleep
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in other modules
window.SunoAPI = SunoAPI;
