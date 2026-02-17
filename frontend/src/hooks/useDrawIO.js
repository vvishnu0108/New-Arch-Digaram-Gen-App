import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook for Draw.IO iframe communication
 */
export function useDrawIO() {
    const iframeRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const pendingActionsRef = useRef([]);

    /**
     * Handle messages from Draw.IO iframe
     */
    const handleMessage = useCallback((event) => {
        // Only accept messages from draw.io
        if (!event.data || typeof event.data !== 'string') return;

        try {
            const message = JSON.parse(event.data);

            switch (message.event) {
                case 'init':
                    // Draw.IO is ready
                    setIsReady(true);
                    // Process any pending actions
                    pendingActionsRef.current.forEach(action => action());
                    pendingActionsRef.current = [];
                    break;

                case 'load':
                    // Diagram loaded
                    setIsEditing(false);
                    break;

                case 'save':
                    // User saved the diagram
                    if (message.xml) {
                        // You can add a callback here to handle saves
                    }
                    break;

                case 'export':
                    // Export completed
                    break;

                case 'exit':
                    // User closed the editor
                    setIsEditing(false);
                    break;

                default:
                    break;
            }
        } catch {
            // Not a JSON message, ignore
        }
    }, []);

    /**
     * Set up message listener
     */
    useEffect(() => {
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [handleMessage]);

    /**
     * Send a message to the Draw.IO iframe
     */
    const sendMessage = useCallback((message) => {
        if (iframeRef.current && iframeRef.current.contentWindow) {
            iframeRef.current.contentWindow.postMessage(
                JSON.stringify(message),
                '*'
            );
        }
    }, []);

    /**
     * Load diagram XML into Draw.IO
     */
    const loadDiagram = useCallback((xml) => {
        const action = () => {
            sendMessage({
                action: 'load',
                xml: xml,
                autosave: 1,
            });
        };

        if (isReady) {
            action();
        } else {
            pendingActionsRef.current.push(action);
        }
    }, [isReady, sendMessage]);

    /**
     * Export the current diagram
     */
    const exportDiagram = useCallback((format = 'xml') => {
        sendMessage({
            action: 'export',
            format: format,
        });
    }, [sendMessage]);

    /**
     * Get the current diagram XML
     */
    const getDiagramXml = useCallback(() => {
        return new Promise((resolve) => {
            const handler = (event) => {
                if (!event.data || typeof event.data !== 'string') return;
                try {
                    const message = JSON.parse(event.data);
                    if (message.event === 'export' && message.xml) {
                        window.removeEventListener('message', handler);
                        resolve(message.xml);
                    }
                } catch {
                    // Ignore
                }
            };

            window.addEventListener('message', handler);
            exportDiagram('xml');

            // Timeout after 5 seconds
            setTimeout(() => {
                window.removeEventListener('message', handler);
                resolve(null);
            }, 5000);
        });
    }, [exportDiagram]);

    /**
     * Clear the diagram
     */
    const clearDiagram = useCallback(() => {
        const emptyDiagram = `
      <mxfile>
        <diagram name="Page-1">
          <mxGraphModel>
            <root>
              <mxCell id="0"/>
              <mxCell id="1" parent="0"/>
            </root>
          </mxGraphModel>
        </diagram>
      </mxfile>
    `;
        loadDiagram(emptyDiagram);
    }, [loadDiagram]);

    return {
        iframeRef,
        isReady,
        isEditing,
        loadDiagram,
        exportDiagram,
        getDiagramXml,
        clearDiagram,
        sendMessage,
    };
}

export default useDrawIO;
