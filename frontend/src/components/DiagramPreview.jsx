import { useState } from 'react';
import { Maximize2, ExternalLink, X, Download } from 'lucide-react';
import ModernTabs from './ModernTabs';
import QualityCard from './QualityCard';
import DrawIOCanvas from './DrawIOCanvas';
import DocumentationPanel from './DocumentationPanel';
import ValidationPanel from './ValidationPanel';
import './DiagramPreview.css';

function DiagramPreview({
  diagramXml,
  onDiagramChange,
  documentation,
  validationResult,
  pythonCode,
  qualityData,
  onDownload,
  onClose
}) {
  const [activeTab, setActiveTab] = useState('diagram');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    // TODO: Implement fullscreen logic
  };

  const handleOpenNewTab = () => {
    // TODO: Open diagram in new tab
    window.open('/diagram-viewer', '_blank');
  };

  return (
    <div className={`diagram-preview ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Header - NO LOGO */}
      <div className="preview-header">
        <div className="preview-actions">
          <button className="action-button" onClick={onDownload} title="Download">
            <Download size={18} />
          </button>
          <button className="action-button" onClick={handleFullscreen} title="Fullscreen">
            <Maximize2 size={18} />
          </button>
          <button className="action-button" onClick={handleOpenNewTab} title="Open in new tab">
            <ExternalLink size={18} />
          </button>
          <button className="action-button action-close" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <ModernTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Content */}
      <div className="preview-content">
        {activeTab === 'diagram' && (
          <div className="preview-diagram-container">
            {diagramXml ? (
              <DrawIOCanvas 
                xml={diagramXml}
                onXmlChange={onDiagramChange}
              />
            ) : (
              <div className="preview-empty">
                <div className="empty-icon">📊</div>
                <h3>No Diagram Yet</h3>
                <p>Generate an architecture to see the diagram here</p>
              </div>
            )}

            {/* Floating Quality Card */}
            {qualityData && qualityData.score > 0 && (
              <div className="floating-quality-card">
                <QualityCard
                  qualityScore={qualityData.score}
                  components={qualityData.components}
                  clusters={qualityData.clusters}
                  warnings={qualityData.warnings}
                  suggestions={qualityData.suggestions}
                />
              </div>
            )}
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="preview-panel-content">
            {documentation ? (
              <DocumentationPanel documentation={documentation} />
            ) : (
              <div className="preview-empty">
                <div className="empty-icon">📄</div>
                <h3>No Documentation</h3>
                <p>Documentation will appear here after generation</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'code' && (
          <div className="preview-panel-content">
            {pythonCode ? (
              <div className="code-container">
                <div className="code-header">
                  <span className="code-label">Python Code</span>
                  <button 
                    className="copy-button"
                    onClick={() => navigator.clipboard.writeText(pythonCode)}
                  >
                    Copy
                  </button>
                </div>
                <pre className="code-block">
                  <code>{pythonCode}</code>
                </pre>
              </div>
            ) : (
              <div className="preview-empty">
                <div className="empty-icon">💻</div>
                <h3>No Code</h3>
                <p>Python code will appear here after generation</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'validation' && (
          <div className="preview-panel-content">
            {validationResult ? (
              <ValidationPanel validationResult={validationResult} />
            ) : (
              <div className="preview-empty">
                <div className="empty-icon">✓</div>
                <h3>No Validation Results</h3>
                <p>Validation results will appear here</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DiagramPreview;
