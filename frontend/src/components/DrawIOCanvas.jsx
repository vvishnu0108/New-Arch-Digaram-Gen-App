import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Maximize2, Minimize2, RefreshCw } from 'lucide-react';
import './DrawIOCanvas.css';

/**
 * Embedded Draw.IO canvas component
 */
const DrawIOCanvas = forwardRef(function DrawIOCanvas({
    diagramXml,
    onDiagramChange,
    onReady,
    iframeRef,
    isReady,
    isFullscreen,
    onToggleFullscreen
}, ref) {
    const containerRef = useRef(null);
    const exportResolveRef = useRef(null);

    // Draw.IO embed URL with configuration
    const drawioUrl = new URL('https://embed.diagrams.net/');
    drawioUrl.searchParams.set('embed', '1');
    drawioUrl.searchParams.set('spin', '1');
    drawioUrl.searchParams.set('proto', 'json');
    drawioUrl.searchParams.set('configure', '1');
    drawioUrl.searchParams.set('dark', '0'); // Light mode for Lenovo theme
    drawioUrl.searchParams.set('ui', 'kennedy'); // Modern UI
    drawioUrl.searchParams.set('noSaveBtn', '1');
    drawioUrl.searchParams.set('noExitBtn', '1');

    // Handle messages from Draw.IO
    useEffect(() => {
        const handleMessage = (event) => {
            if (!event.data || typeof event.data !== 'string') return;

            try {
                const message = JSON.parse(event.data);

                if (message.event === 'configure') {
                    // Send Lenovo-themed configuration
                    if (iframeRef.current && iframeRef.current.contentWindow) {
                        iframeRef.current.contentWindow.postMessage(JSON.stringify({
                            action: 'configure',
                            config: {
                                css: `
                  .geMenubar { background: #FFFFFF !important; border-bottom: 2px solid #E2231A !important; }
                  .geToolbar { background: #F7F7F7 !important; }
                  .geSidebarContainer { background: #FFFFFF !important; }
                  .geFormatContainer { background: #FFFFFF !important; }
                  .mxWindow { background: #FFFFFF !important; }
                `,
                                defaultFonts: ['Inter', 'Helvetica', 'Arial'],
                            }
                        }), '*');
                    }
                }

                if (message.event === 'init') {
                    // Draw.IO is ready, notify parent
                    if (onReady) {
                        onReady();
                    }
                    // Load the diagram if we have one
                    if (diagramXml && iframeRef.current && iframeRef.current.contentWindow) {
                        iframeRef.current.contentWindow.postMessage(JSON.stringify({
                            action: 'load',
                            xml: diagramXml,
                            autosave: 1,
                        }), '*');
                    }
                }

                if (message.event === 'autosave' && message.xml) {
                    // Diagram was edited, notify parent
                    if (onDiagramChange) {
                        onDiagramChange(message.xml);
                    }
                }

                if (message.event === 'save' && message.xml) {
                    // User explicitly saved
                    if (onDiagramChange) {
                        onDiagramChange(message.xml);
                    }
                }

                // Handle export response
                if (message.event === 'export' && message.data) {
                    if (exportResolveRef.current) {
                        exportResolveRef.current(message.data);
                        exportResolveRef.current = null;
                    }
                }

            } catch {
                // Not a JSON message, ignore
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [diagramXml, onDiagramChange, onReady, iframeRef]);

    // Load new diagram when diagramXml changes
    useEffect(() => {
        if (isReady && diagramXml && iframeRef.current && iframeRef.current.contentWindow) {
            iframeRef.current.contentWindow.postMessage(JSON.stringify({
                action: 'load',
                xml: diagramXml,
                autosave: 1,
            }), '*');
        }
    }, [diagramXml, isReady, iframeRef]);

    // Expose exportDiagram method to parent via ref
    useImperativeHandle(ref, () => ({
        exportDiagram: () => {
            return new Promise((resolve) => {
                if (iframeRef.current && iframeRef.current.contentWindow) {
                    exportResolveRef.current = resolve;
                    iframeRef.current.contentWindow.postMessage(JSON.stringify({
                        action: 'export',
                        format: 'xmlsvg'
                    }), '*');
                    // Timeout after 3 seconds
                    setTimeout(() => {
                        if (exportResolveRef.current) {
                            exportResolveRef.current(null);
                            exportResolveRef.current = null;
                        }
                    }, 3000);
                } else {
                    resolve(null);
                }
            });
        }
    }), [iframeRef]);

    const handleRefresh = () => {
        if (iframeRef.current) {
            iframeRef.current.src = iframeRef.current.src;
        }
    };

    return (
        <div
            ref={containerRef}
            className={`drawio-canvas ${isFullscreen ? 'fullscreen' : ''}`}
        >
            <div className="drawio-toolbar">
                <span className="drawio-title">
                    {isReady ? 'Draw.IO Editor' : 'Loading Editor...'}
                </span>
                <div className="drawio-actions">
                    <button
                        className="btn btn-ghost btn-icon"
                        onClick={handleRefresh}
                        title="Refresh Editor"
                    >
                        <RefreshCw size={18} />
                    </button>
                    <button
                        className="btn btn-ghost btn-icon"
                        onClick={onToggleFullscreen}
                        title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                    >
                        {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </button>
                </div>
            </div>

            <div className="drawio-frame-container">
                {!diagramXml && !isReady && (
                    <div className="drawio-placeholder">
                        <div className="drawio-placeholder-content">
                            <div className="drawio-placeholder-icon">📐</div>
                            <h3>No Diagram Yet</h3>
                            <p>Generate a diagram using the chat panel, then edit it here.</p>
                        </div>
                    </div>
                )}

                <iframe
                    ref={iframeRef}
                    className="drawio-frame"
                    src={drawioUrl.toString()}
                    title="Draw.IO Editor"
                    style={{ opacity: diagramXml || isReady ? 1 : 0 }}
                />
            </div>
        </div>
    );
});

export default DrawIOCanvas;
