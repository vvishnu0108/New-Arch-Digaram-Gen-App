/**
 * API client for backend communication
 */

const API_BASE_URL = '/api';

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
}

/**
 * Diagram API endpoints
 */
export const diagramsApi = {
    /**
     * Generate a new diagram from a prompt
     */
    generate: async (prompt, sessionId = null) => {
        return apiRequest('/diagrams/generate', {
            method: 'POST',
            body: JSON.stringify({
                prompt,
                session_id: sessionId,
            }),
        });
    },

    /**
     * Generate a new diagram with streaming status updates
     * @param {string} prompt - The diagram description
     * @param {string|null} sessionId - Optional session ID
     * @param {function} onStatus - Callback for status updates (message, step, attempt)
     * @returns {Promise} - Resolves with the final diagram result
     */
    generateStream: (prompt, sessionId = null, onStatus) => {
        return new Promise((resolve, reject) => {
            // Create a temporary form to send POST data with EventSource
            // Using fetch with streaming instead
            const controller = new AbortController();

            fetch(`${API_BASE_URL}/diagrams/generate/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, session_id: sessionId }),
                signal: controller.signal
            })
                .then(response => {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';

                    function processChunk() {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                return;
                            }

                            buffer += decoder.decode(value, { stream: true });

                            // Parse SSE events from buffer
                            const lines = buffer.split('\n');
                            buffer = lines.pop() || ''; // Keep incomplete line in buffer

                            let currentEvent = '';
                            let currentData = '';

                            for (const line of lines) {
                                if (line.startsWith('event: ')) {
                                    currentEvent = line.slice(7);
                                } else if (line.startsWith('data: ')) {
                                    currentData = line.slice(6);
                                } else if (line === '' && currentEvent && currentData) {
                                    // End of event
                                    try {
                                        const data = JSON.parse(currentData);

                                        if (currentEvent === 'status' && onStatus) {
                                            onStatus(data.message, data.step, data.attempt);
                                        } else if (currentEvent === 'complete') {
                                            resolve(data);
                                            return;
                                        }
                                    } catch (e) {
                                        console.error('Failed to parse SSE data:', e);
                                    }
                                    currentEvent = '';
                                    currentData = '';
                                }
                            }

                            processChunk();
                        }).catch(reject);
                    }

                    processChunk();
                })
                .catch(reject);
        });
    },


    /**
     * Update an existing diagram with a follow-up prompt
     */
    update: async (sessionId, prompt, currentDiagramXml = null) => {
        return apiRequest('/diagrams/update', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                prompt,
                current_diagram_xml: currentDiagramXml,
            }),
        });
    },

    /**
     * Import diagram XML from Draw.IO edits
     */
    import: async (sessionId, diagramXml) => {
        return apiRequest('/diagrams/import', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                diagram_xml: diagramXml,
            }),
        });
    },

    /**
     * Get session information
     */
    getSession: async (sessionId) => {
        return apiRequest(`/diagrams/${sessionId}`);
    },

    /**
     * Get file download URL
     */
    getFileUrl: (filename) => {
        return `${API_BASE_URL}/diagrams/files/${filename}`;
    },
};

/**
 * Documentation API endpoints
 */
export const docsApi = {
    /**
     * Generate documentation for a diagram
     */
    generate: async (sessionId) => {
        return apiRequest('/docs/generate', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
            }),
        });
    },

    /**
     * Get documentation for a session
     */
    get: async (sessionId) => {
        return apiRequest(`/docs/${sessionId}`);
    },
};

/**
 * Validation API endpoints
 */
export const validationApi = {
    /**
     * Validate a diagram
     */
    validate: async (sessionId) => {
        return apiRequest('/validate', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
            }),
        });
    },

    /**
     * Submit validation feedback for re-validation
     */
    feedback: async (sessionId, feedback, acceptedSuggestions = []) => {
        return apiRequest('/validate/feedback', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                feedback,
                accepted_suggestions: acceptedSuggestions,
            }),
        });
    },
};

export default {
    diagrams: diagramsApi,
    docs: docsApi,
    validation: validationApi,
};
