import { useState, useRef, useCallback, useEffect } from 'react';
import HeroSection from './components/HeroSection';
import ModernChatPanel from './components/ModernChatPanel';
import DiagramPreview from './components/DiagramPreview';
import { diagramsApi, docsApi, validationApi } from './services/api';
import useSession from './hooks/useSession';
import './App.css';

function App() {
    // Session management
    const {
        sessionId,
        conversationHistory,
        currentDiagramXml,
        files,
        updateFromResponse,
        addMessage,
        clearSession,
        updateDiagramXml,
    } = useSession();

    // View state: 'home' or 'chat'
    const [currentView, setCurrentView] = useState('home');

    // Loading states
    const [isGenerating, setIsGenerating] = useState(false);

    // Data
    const [documentation, setDocumentation] = useState(null);
    const [validationResult, setValidationResult] = useState(null);
    const [pythonCode, setPythonCode] = useState(null);
    const [qualityData, setQualityData] = useState(null);

    // Draw.IO ref
    const drawioCanvasRef = useRef(null);
    const [drawioReady, setDrawioReady] = useState(false);

    /**
     * Handle diagram generation from hero page
     */
    const handleGenerate = useCallback(async (prompt) => {
        if (!prompt.trim()) return;

        setIsGenerating(true);
        setCurrentView('chat'); // Switch to chat view

        // Add user message
        addMessage('user', prompt);

        try {
            const response = await diagramsApi.generate(prompt);

            if (response.success) {
                updateFromResponse(response);
                
                // Add assistant message with metadata
                const assistantMessage = {
                    role: 'assistant',
                    content: response.message || 'Architecture diagram generated successfully!',
                    metadata: {
                        components: extractComponentCount(response.python_code),
                        quality_score: response.quality_score || 0,
                        clusters: extractClusterCount(response.python_code)
                    },
                    reasoning: response.architectural_reasoning || null
                };
                addMessage('assistant', assistantMessage.content, assistantMessage.metadata, assistantMessage.reasoning);

                // Store additional data
                setPythonCode(response.python_code);
                setQualityData({
                    score: response.quality_score || 0,
                    components: extractComponentCount(response.python_code),
                    clusters: extractClusterCount(response.python_code),
                    warnings: response.quality_feedback?.warnings || [],
                    suggestions: response.quality_feedback?.suggestions || []
                });
            } else {
                addMessage('assistant', `Error: ${response.message || 'Failed to generate diagram'}`);
            }
        } catch (error) {
            console.error('Generation error:', error);
            addMessage('assistant', `Error: ${error.message || 'Something went wrong'}`);
        } finally {
            setIsGenerating(false);
        }
    }, [addMessage, updateFromResponse]);

    /**
     * Handle updates from chat
     */
    const handleChatMessage = useCallback(async (prompt) => {
        setIsGenerating(true);
        addMessage('user', prompt);

        try {
            // Export current diagram state if available
            let currentXml = currentDiagramXml;
            if (drawioReady && drawioCanvasRef.current) {
                try {
                    const exportedXml = await drawioCanvasRef.current.exportDiagram();
                    if (exportedXml) {
                        currentXml = exportedXml;
                        updateDiagramXml(exportedXml);
                    }
                } catch (err) {
                    console.warn('Failed to export diagram:', err);
                }
            }

            const response = await diagramsApi.update(sessionId, prompt, currentXml);

            if (response.success) {
                updateFromResponse(response);
                
                const assistantMessage = {
                    role: 'assistant',
                    content: response.message || 'Diagram updated successfully!',
                    metadata: {
                        components: extractComponentCount(response.python_code),
                        quality_score: response.quality_score || 0,
                        clusters: extractClusterCount(response.python_code)
                    },
                    reasoning: response.architectural_reasoning || null
                };
                addMessage('assistant', assistantMessage.content, assistantMessage.metadata, assistantMessage.reasoning);

                // Update data
                setPythonCode(response.python_code);
                setQualityData({
                    score: response.quality_score || 0,
                    components: extractComponentCount(response.python_code),
                    clusters: extractClusterCount(response.python_code),
                    warnings: response.quality_feedback?.warnings || [],
                    suggestions: response.quality_feedback?.suggestions || []
                });

                // Clear docs and validation when diagram changes
                setDocumentation(null);
                setValidationResult(null);
            } else {
                addMessage('assistant', `Error: ${response.message}`);
            }
        } catch (error) {
            console.error('Update error:', error);
            addMessage('assistant', `Error: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    }, [sessionId, currentDiagramXml, drawioReady, addMessage, updateFromResponse, updateDiagramXml]);

    /**
     * Handle diagram XML changes from Draw.IO editor
     */
    const handleDiagramChange = useCallback((newXml) => {
        updateDiagramXml(newXml);
    }, [updateDiagramXml]);

    /**
     * Handle download
     */
    const handleDownload = useCallback(() => {
        if (files && files.length > 0) {
            files.forEach(file => {
                const link = document.createElement('a');
                link.href = file.url;
                link.download = file.filename;
                link.click();
            });
        }
    }, [files]);

    /**
     * Handle close/reset
     */
    const handleClose = useCallback(() => {
        if (window.confirm('Close current session and start over?')) {
            clearSession();
            setCurrentView('home');
            setDocumentation(null);
            setValidationResult(null);
            setPythonCode(null);
            setQualityData(null);
        }
    }, [clearSession]);

    /**
     * Generate documentation
     */
    const handleGenerateDocs = useCallback(async () => {
        if (!sessionId) return;

        try {
            const response = await docsApi.generate(sessionId);
            if (response.success) {
                setDocumentation(response);
            }
        } catch (error) {
            console.error('Documentation generation error:', error);
        }
    }, [sessionId]);

    /**
     * Run validation
     */
    const handleValidate = useCallback(async () => {
        if (!sessionId) return;

        try {
            const response = await validationApi.validate(sessionId);
            if (response.success) {
                setValidationResult(response);
            }
        } catch (error) {
            console.error('Validation error:', error);
        }
    }, [sessionId]);

    // Auto-generate docs when diagram is created
    useEffect(() => {
        if (sessionId && currentDiagramXml && !documentation) {
            handleGenerateDocs();
        }
    }, [sessionId, currentDiagramXml, documentation, handleGenerateDocs]);

    // Format messages for ModernChatPanel
    const formattedMessages = conversationHistory.map(msg => ({
        role: msg.role,
        content: msg.content,
        metadata: msg.metadata,
        reasoning: msg.reasoning
    }));

    return (
        <div className="app-container">
            {currentView === 'home' ? (
                /* Home View - Hero Section */
                <HeroSection onGenerate={handleGenerate} />
            ) : (
                /* Chat View - Split Screen */
                <div className="chat-view">
                    <div className="chat-layout">
                        {/* Left Panel - Chat (40%) */}
                        <div className="chat-panel-container">
                            <ModernChatPanel
                                messages={formattedMessages}
                                onSendMessage={handleChatMessage}
                                isGenerating={isGenerating}
                                sessionId={sessionId}
                            />
                        </div>

                        {/* Right Panel - Diagram Preview (60%) */}
                        <div className="diagram-panel-container">
                            <DiagramPreview
                                diagramXml={currentDiagramXml}
                                onDiagramChange={handleDiagramChange}
                                documentation={documentation}
                                validationResult={validationResult}
                                pythonCode={pythonCode}
                                qualityData={qualityData}
                                onDownload={handleDownload}
                                onClose={handleClose}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper functions
function extractComponentCount(code) {
    if (!code) return 0;
    const matches = code.match(/=\s*\w+\(["\']/) || [];
    return matches.length;
}

function extractClusterCount(code) {
    if (!code) return 0;
    const matches = code.match(/with\s+Cluster\(/g) || [];
    return matches.length;
}

export default App;
