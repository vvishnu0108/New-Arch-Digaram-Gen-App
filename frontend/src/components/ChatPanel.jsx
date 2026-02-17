import { useState } from 'react';
import { Send, Loader2, Sparkles, MessageSquare, Bot, User } from 'lucide-react';
import './ChatPanel.css';

/**
 * Chat panel for submitting prompts and viewing conversation history
 */
function ChatPanel({
    onSubmit,
    isLoading,
    conversationHistory = [],
    hasActiveSession
}) {
    const [prompt, setPrompt] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (prompt.trim() && !isLoading) {
            onSubmit(prompt.trim());
            setPrompt('');
        }
    };

    const examplePrompts = [
        '3-tier web application on AWS with load balancing',
        'Azure microservices architecture with Kubernetes',
        'GCP data pipeline with BigQuery and Dataflow',
        'Serverless architecture on AWS with Lambda and API Gateway',
    ];

    return (
        <div className="chat-panel">
            {/* Header */}
            <div className="chat-header">
                <div className="chat-header-title">
                    <MessageSquare size={20} />
                    <span>Architecture Chat</span>
                </div>
                {hasActiveSession && (
                    <span className="badge badge-success">Session Active</span>
                )}
            </div>

            {/* Conversation History */}
            <div className="chat-messages">
                {conversationHistory.length === 0 ? (
                    <div className="chat-empty">
                        <div className="chat-empty-icon">
                            <Sparkles size={48} />
                        </div>
                        <h3>Create Your Architecture</h3>
                        <p>Describe the architecture you want to create, and I'll generate a professional diagram for you.</p>

                        <div className="chat-examples">
                            <span className="chat-examples-label">Try an example:</span>
                            {examplePrompts.map((example, index) => (
                                <button
                                    key={index}
                                    className="chat-example-btn"
                                    onClick={() => setPrompt(example)}
                                    disabled={isLoading}
                                >
                                    {example}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="chat-history">
                        {conversationHistory.map((msg, index) => (
                            <div key={index} className={`chat-message chat-message-${msg.role}`}>
                                <div className="chat-message-avatar">
                                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>
                                <div className="chat-message-content">
                                    <span className="chat-message-role">
                                        {msg.role === 'user' ? 'You' : 'Assistant'}
                                    </span>
                                    <p>{msg.content}</p>
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="chat-message chat-message-assistant">
                                <div className="chat-message-avatar">
                                    <Bot size={16} />
                                </div>
                                <div className="chat-message-content">
                                    <span className="chat-message-role">Assistant</span>
                                    <div className="chat-typing">
                                        <Loader2 size={16} className="spinning" />
                                        <span>Generating diagram...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Input Form */}
            <form className="chat-input-form" onSubmit={handleSubmit}>
                <div className="chat-input-wrapper">
                    <textarea
                        className="chat-input"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder={hasActiveSession
                            ? "Describe changes to the diagram..."
                            : "Describe your architecture..."
                        }
                        rows={3}
                        disabled={isLoading}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                    />
                    <button
                        type="submit"
                        className="chat-submit-btn btn btn-primary"
                        disabled={!prompt.trim() || isLoading}
                    >
                        {isLoading ? (
                            <Loader2 size={20} className="spinning" />
                        ) : (
                            <Send size={20} />
                        )}
                    </button>
                </div>
                <div className="chat-input-hint">
                    Press Enter to send, Shift+Enter for new line
                </div>
            </form>
        </div>
    );
}

export default ChatPanel;
