import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Sparkles } from 'lucide-react';
import './ModernChatPanel.css';

function ModernChatPanel({ 
  messages = [], 
  onSendMessage, 
  isGenerating = false,
  sessionId 
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    onSendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="modern-chat-panel">
      {/* Header with session info */}
      <div className="chat-header">
        <div className="session-info">
          <div className="session-badge">
            <Sparkles size={14} />
            <span>Session: {sessionId?.slice(0, 8) || 'New'}</span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="empty-state-icon">
              <svg viewBox="0 0 100 100" width="80" height="80">
                <rect x="10" y="10" width="30" height="30" fill="var(--color-primary)" opacity="0.2"/>
                <rect x="50" y="10" width="40" height="30" fill="var(--color-primary)" opacity="0.3"/>
                <rect x="10" y="50" width="40" height="40" fill="var(--color-primary)" opacity="0.25"/>
                <rect x="60" y="50" width="30" height="40" fill="var(--color-primary)" opacity="0.2"/>
              </svg>
            </div>
            <h3>Start a Conversation</h3>
            <p>Describe the architecture you want to generate</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role === 'user' ? 'message-user' : 'message-assistant'}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? (
                  <User size={18} />
                ) : (
                  <Bot size={18} />
                )}
              </div>
              <div className="message-content">
                <div className="message-text">
                  {message.content}
                </div>
                {message.metadata && (
                  <div className="message-metadata">
                    {message.metadata.components && (
                      <div className="metadata-item">
                        <span className="metadata-icon">🔧</span>
                        <span className="metadata-label">Components:</span>
                        <span className="metadata-value">{message.metadata.components}</span>
                      </div>
                    )}
                    {message.metadata.quality_score && (
                      <div className="metadata-item">
                        <span className="metadata-icon">⭐</span>
                        <span className="metadata-label">Quality:</span>
                        <span className="metadata-value">{message.metadata.quality_score}/100</span>
                      </div>
                    )}
                    {message.metadata.clusters && (
                      <div className="metadata-item">
                        <span className="metadata-icon">📦</span>
                        <span className="metadata-label">Clusters:</span>
                        <span className="metadata-value">{message.metadata.clusters}</span>
                      </div>
                    )}
                  </div>
                )}
                {message.reasoning && (
                  <div className="message-reasoning">
                    <div className="reasoning-label">💡 Architectural Reasoning:</div>
                    <div className="reasoning-text">{message.reasoning}</div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Typing Indicator */}
        {isGenerating && (
          <div className="message message-assistant">
            <div className="message-avatar">
              <Bot size={18} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
              <div className="generating-text">Generating architecture...</div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Describe changes or ask questions..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
            rows={1}
          />
          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || isGenerating}
          >
            <Send size={20} />
          </button>
        </form>
        <div className="chat-input-hint">
          Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for new line
        </div>
      </div>
    </div>
  );
}

export default ModernChatPanel;
