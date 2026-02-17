import { useState, useCallback } from 'react';

/**
 * Custom hook for session management
 */
export function useSession() {
    const [sessionId, setSessionId] = useState(null);
    const [conversationHistory, setConversationHistory] = useState([]);
    const [currentDiagramXml, setCurrentDiagramXml] = useState(null);
    const [files, setFiles] = useState([]);

    /**
     * Update session from API response
     */
    const updateFromResponse = useCallback((response) => {
        if (response.session_id) {
            setSessionId(response.session_id);
        }
        if (response.diagram_xml) {
            setCurrentDiagramXml(response.diagram_xml);
        }
        if (response.files) {
            setFiles(response.files);
        }
    }, []);

    /**
     * Add a message to conversation history
     */
    const addMessage = useCallback((role, content) => {
        const message = {
            role,
            content,
            timestamp: new Date().toISOString(),
        };
        setConversationHistory(prev => [...prev, message]);
        return message;
    }, []);

    /**
     * Clear the current session
     */
    const clearSession = useCallback(() => {
        setSessionId(null);
        setConversationHistory([]);
        setCurrentDiagramXml(null);
        setFiles([]);
    }, []);

    /**
     * Update diagram XML (from Draw.IO edits)
     */
    const updateDiagramXml = useCallback((xml) => {
        setCurrentDiagramXml(xml);
    }, []);

    return {
        sessionId,
        conversationHistory,
        currentDiagramXml,
        files,
        updateFromResponse,
        addMessage,
        clearSession,
        updateDiagramXml,
        setConversationHistory,
    };
}

export default useSession;
