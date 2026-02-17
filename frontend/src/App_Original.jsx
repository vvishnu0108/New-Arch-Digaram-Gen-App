import { useState, useRef, useCallback } from 'react';
import {
    Layers,
    FileText,
    Shield,
    PanelLeftClose,
    PanelLeft,
    RefreshCw
} from 'lucide-react';

import ChatPanel from './components/ChatPanel';
import DrawIOCanvas from './components/DrawIOCanvas';
import DocumentationPanel from './components/DocumentationPanel';
import ValidationPanel from './components/ValidationPanel';
import DownloadControls from './components/DownloadControls';

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
        setConversationHistory,
    } = useSession();

    // UI State
    const [activePanel, setActivePanel] = useState('docs'); // 'docs' or 'validation'
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Loading states
    const [isGenerating, setIsGenerating] = useState(false);
    const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);
    const [isValidating, setIsValidating] = useState(false);

    // Data
    const [documentation, setDocumentation] = useState(null);
    const [docSections, setDocSections] = useState([]);
    const [validationResult, setValidationResult] = useState(null);

    // Draw.IO iframe ref
    const iframeRef = useRef(null);
    const drawioCanvasRef = useRef(null);
    const [drawioReady, setDrawioReady] = useState(false);

    /**
     * Handle prompt submission (new or update)
     */
    const handlePromptSubmit = useCallback(async (prompt) => {
        setIsGenerating(true);

        // Add user message to UI immediately
        addMessage('user', prompt);

        try {
            let response;

            if (sessionId) {
                // Export current diagram state from Draw.IO before updating
                let currentXml = currentDiagramXml;
                if (drawioReady && drawioCanvasRef.current) {
                    try {
                        const exportedXml = await drawioCanvasRef.current.exportDiagram();
                        if (exportedXml) {
                            currentXml = exportedXml;
                            updateDiagramXml(exportedXml); // Also update local state
                        }
                    } catch (err) {
                        console.warn('Failed to export diagram from Draw.IO:', err);
                    }
                }
                // Update existing diagram with latest canvas state
                response = await diagramsApi.update(sessionId, prompt, currentXml);
            } else {
                // Generate new diagram
                response = await diagramsApi.generate(prompt);
            }

            if (response.success) {
                updateFromResponse(response);
                addMessage('assistant', response.message || 'Diagram generated successfully');

                // Clear previous validation and docs when diagram changes
                setValidationResult(null);
                setDocumentation(null);
                setDocSections([]);
            } else {
                addMessage('assistant', `Error: ${response.message}`);
            }
        } catch (error) {
            addMessage('assistant', `Error: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    }, [sessionId, currentDiagramXml, drawioReady, addMessage, updateFromResponse, updateDiagramXml]);

    /**
     * Handle diagram changes from Draw.IO
     */
    const handleDiagramChange = useCallback((xml) => {
        updateDiagramXml(xml);
    }, [updateDiagramXml]);

    /**
     * Generate documentation
     */
    const handleGenerateDocs = useCallback(async () => {
        if (!sessionId) return;

        setIsGeneratingDocs(true);
        try {
            const response = await docsApi.generate(sessionId);
            if (response.success) {
                setDocumentation(response.documentation);
                setDocSections(response.sections || []);
            }
        } catch (error) {
            console.error('Failed to generate docs:', error);
        } finally {
            setIsGeneratingDocs(false);
        }
    }, [sessionId]);

    /**
     * Validate diagram
     */
    const handleValidate = useCallback(async () => {
        if (!sessionId) return;

        setIsValidating(true);
        try {
            const response = await validationApi.validate(sessionId);
            if (response.success) {
                setValidationResult(response);
            }
        } catch (error) {
            console.error('Failed to validate:', error);
        } finally {
            setIsValidating(false);
        }
    }, [sessionId]);

    /**
     * Handle validation feedback for re-validation
     */
    const handleValidationFeedback = useCallback(async (feedback, acceptedSuggestions) => {
        if (!sessionId) return;

        setIsValidating(true);
        try {
            const response = await validationApi.feedback(sessionId, feedback, acceptedSuggestions);
            if (response.success) {
                setValidationResult(response);
            }
        } catch (error) {
            console.error('Failed to re-validate:', error);
        } finally {
            setIsValidating(false);
        }
    }, [sessionId]);

    /**
     * Start a new session
     */
    const handleNewSession = useCallback(() => {
        clearSession();
        setDocumentation(null);
        setDocSections([]);
        setValidationResult(null);
        setConversationHistory([]);
    }, [clearSession, setConversationHistory]);

    return (
        <div className="app">
            {/* Header */}
            <header className="app-header">
                <div className="header-left">
                    <button
                        className="btn btn-ghost btn-icon"
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        title={sidebarCollapsed ? 'Show Chat' : 'Hide Chat'}
                    >
                        {sidebarCollapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
                    </button>
                    <div className="app-logo">
                        <Layers size={24} className="logo-icon" />
                        <h1>AI Architecture Diagram Generator</h1>
                    </div>
                </div>

                <div className="header-center">
                    {sessionId && (
                        <div className="session-info">
                            <span className="session-label">Session:</span>
                            <code className="session-id">{sessionId}</code>
                        </div>
                    )}
                </div>

                <div className="header-right">
                    {files.length > 0 && (
                        <DownloadControls files={files} />
                    )}
                    <button
                        className="btn btn-secondary"
                        onClick={handleNewSession}
                        title="Start New Session"
                    >
                        <RefreshCw size={16} />
                        New
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="app-main">
                {/* Left Sidebar - Chat */}
                <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
                    <ChatPanel
                        onSubmit={handlePromptSubmit}
                        isLoading={isGenerating}
                        conversationHistory={conversationHistory}
                        hasActiveSession={!!sessionId}
                    />
                </aside>

                {/* Center - Draw.IO Canvas */}
                <section className="canvas-area">
                    <DrawIOCanvas
                        ref={drawioCanvasRef}
                        diagramXml={currentDiagramXml}
                        onDiagramChange={handleDiagramChange}
                        onReady={() => setDrawioReady(true)}
                        iframeRef={iframeRef}
                        isReady={drawioReady}
                        isFullscreen={isFullscreen}
                        onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                    />
                </section>

                {/* Right Panel - Docs & Validation */}
                <aside className={`right-panel ${rightPanelCollapsed ? 'collapsed' : ''}`}>
                    {/* Panel Tabs */}
                    <div className="panel-tabs">
                        <button
                            className={`panel-tab ${activePanel === 'docs' ? 'active' : ''}`}
                            onClick={() => setActivePanel('docs')}
                        >
                            <FileText size={16} />
                            Docs
                        </button>
                        <button
                            className={`panel-tab ${activePanel === 'validation' ? 'active' : ''}`}
                            onClick={() => setActivePanel('validation')}
                        >
                            <Shield size={16} />
                            Validate
                        </button>
                    </div>

                    {/* Panel Content */}
                    <div className="panel-content-area">
                        {activePanel === 'docs' ? (
                            <DocumentationPanel
                                documentation={documentation}
                                sections={docSections}
                                isLoading={isGeneratingDocs}
                                onGenerate={handleGenerateDocs}
                                hasSession={!!sessionId}
                            />
                        ) : (
                            <ValidationPanel
                                validationResult={validationResult}
                                isLoading={isValidating}
                                onValidate={handleValidate}
                                onFeedback={handleValidationFeedback}
                                hasSession={!!sessionId}
                            />
                        )}
                    </div>
                </aside>
            </main>
        </div>
    );
}

export default App;
