import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Loader2, Copy, Check, Download } from 'lucide-react';
import './DocumentationPanel.css';

/**
 * Panel for displaying generated documentation in a Word document style
 */
function DocumentationPanel({
    documentation,
    sections = [],
    isLoading,
    onGenerate,
    hasSession
}) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        if (documentation) {
            await navigator.clipboard.writeText(documentation);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Download as HTML file styled like Word doc
    const handleDownload = () => {
        if (!fullDocument) return;

        const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Architecture Documentation</title>
    <style>
        body {
            font-family: 'Times New Roman', Georgia, serif;
            font-size: 12pt;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 40px;
            color: #000;
        }
        h1 { font-size: 24pt; border-bottom: 2px solid #E2231A; padding-bottom: 8pt; }
        h2 { font-size: 16pt; margin-top: 24pt; }
        h3 { font-size: 14pt; margin-top: 18pt; }
        p { text-align: justify; margin-bottom: 12pt; }
        ul, ol { padding-left: 24pt; margin-bottom: 12pt; }
        li { margin-bottom: 6pt; }
        hr { border: none; border-top: 1px solid #ccc; margin: 24pt 0; }
        code { font-family: Consolas, monospace; background: #f5f5f5; padding: 2px 6px; }
    </style>
</head>
<body>
${fullDocument.replace(/^## /gm, '<h2>').replace(/^### /gm, '<h3>').replace(/^# /gm, '<h1>')}
</body>
</html>`;

        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'architecture_documentation.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // Combine all sections into a single document
    const fullDocument = sections.length > 0
        ? sections.map(s => `## ${s.title}\n\n${s.content}`).join('\n\n---\n\n')
        : documentation;

    return (
        <div className="doc-panel panel">
            <div className="panel-header">
                <div className="panel-title">
                    <FileText size={18} />
                    <span>Documentation</span>
                </div>
                <div className="doc-actions">
                    {documentation && (
                        <>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={handleCopy}
                                title="Copy to clipboard"
                            >
                                {copied ? <Check size={14} /> : <Copy size={14} />}
                                {copied ? 'Copied!' : 'Copy'}
                            </button>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={handleDownload}
                                title="Download as document"
                            >
                                <Download size={14} />
                                Download
                            </button>
                        </>
                    )}
                    {hasSession && (
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={onGenerate}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={14} className="spinning" />
                                    Generating...
                                </>
                            ) : (
                                <>Generate</>
                            )}
                        </button>
                    )}
                </div>
            </div>

            <div className="panel-content">
                {isLoading ? (
                    <div className="doc-loading">
                        <Loader2 size={24} className="spinning" />
                        <p>Generating documentation...</p>
                    </div>
                ) : fullDocument ? (
                    <div className="doc-document">
                        <div className="doc-paper">
                            <ReactMarkdown
                                components={{
                                    h1: ({ children }) => <h1 className="doc-h1">{children}</h1>,
                                    h2: ({ children }) => <h2 className="doc-h2">{children}</h2>,
                                    h3: ({ children }) => <h3 className="doc-h3">{children}</h3>,
                                    p: ({ children }) => <p className="doc-p">{children}</p>,
                                    ul: ({ children }) => <ul className="doc-ul">{children}</ul>,
                                    ol: ({ children }) => <ol className="doc-ol">{children}</ol>,
                                    li: ({ children }) => <li className="doc-li">{children}</li>,
                                    strong: ({ children }) => <strong className="doc-strong">{children}</strong>,
                                    hr: () => <hr className="doc-hr" />,
                                    code: ({ children }) => <code className="doc-code">{children}</code>,
                                }}
                            >
                                {fullDocument}
                            </ReactMarkdown>
                        </div>
                    </div>
                ) : (
                    <div className="doc-empty">
                        <FileText size={32} className="doc-empty-icon" />
                        <p>No documentation generated yet.</p>
                        {hasSession && (
                            <p className="text-sm text-muted">
                                Click "Generate" to create documentation for your architecture.
                            </p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default DocumentationPanel;

