import { useState } from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';
import './HeroSection.css';

function HeroSection({ onGenerate }) {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || isGenerating) return;

    setIsGenerating(true);
    await onGenerate(prompt);
    setIsGenerating(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e);
    }
  };

  const examplePrompts = [
    'Azure microservices architecture with Kubernetes',
    'AWS three-tier web application with high availability',
    'GCP data pipeline with BigQuery and Dataflow',
    'On-premises hybrid cloud with Azure connectivity'
  ];

  return (
    <div className="hero-section">
      <div className="hero-background-circle hero-circle-1"></div>
      <div className="hero-background-circle hero-circle-2"></div>
      
      <div className="hero-content">
        {/* Logo Icon */}
        <div className="hero-icon">
          <svg viewBox="0 0 100 100" className="hero-icon-svg">
            <rect x="10" y="10" width="30" height="30" fill="var(--color-primary)" opacity="0.9"/>
            <rect x="50" y="10" width="40" height="30" fill="var(--color-primary)" opacity="0.7"/>
            <rect x="10" y="50" width="40" height="40" fill="var(--color-primary)" opacity="0.8"/>
            <rect x="60" y="50" width="30" height="40" fill="var(--color-primary)" opacity="0.6"/>
          </svg>
        </div>

        {/* Main Heading */}
        <h1 className="hero-title">
          Architecture Diagram Generator
        </h1>
        
        <p className="hero-subtitle">
          Generate production-ready architecture diagrams from natural language using AI
        </p>

        {/* Input Card - NO GLASS EFFECT */}
        <form onSubmit={handleSubmit} className="hero-form">
          <div className="hero-input-card">
            <textarea
              className="hero-input"
              placeholder="Describe your architecture... e.g., 'Azure microservices with Kubernetes and Redis'"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isGenerating}
              rows={3}
            />
            
            <button
              type="submit"
              className="hero-button"
              disabled={!prompt.trim() || isGenerating}
            >
              <span className="hero-button-content">
                {isGenerating ? (
                  <>
                    <div className="spinner"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles size={20} />
                    Generate Architecture
                    <ArrowRight size={20} />
                  </>
                )}
              </span>
            </button>
          </div>
        </form>

        {/* Example Prompts */}
        <div className="hero-examples">
          <p className="hero-examples-label">Try these examples:</p>
          <div className="hero-examples-list">
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                className="hero-example-chip"
                onClick={() => setPrompt(example)}
                disabled={isGenerating}
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {/* Tip */}
        <div className="hero-tip">
          <span className="hero-tip-icon">💡</span>
          <span className="hero-tip-text">
            Press <kbd>Cmd/Ctrl + Enter</kbd> to generate
          </span>
        </div>
      </div>
    </div>
  );
}

export default HeroSection;
