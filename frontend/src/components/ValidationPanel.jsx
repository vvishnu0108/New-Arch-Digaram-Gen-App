import { useState } from 'react';
import {
    Shield,
    Loader2,
    CheckCircle,
    AlertTriangle,
    AlertCircle,
    Info,
    ThumbsUp,
    ThumbsDown,
    RotateCcw,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import './ValidationPanel.css';

/**
 * Panel for validation results and re-validation loop
 */
function ValidationPanel({
    validationResult,
    isLoading,
    onValidate,
    onFeedback,
    hasSession
}) {
    const [feedback, setFeedback] = useState('');
    const [acceptedSuggestions, setAcceptedSuggestions] = useState(new Set());
    const [expandedSuggestions, setExpandedSuggestions] = useState(new Set());
    const [showFeedbackForm, setShowFeedbackForm] = useState(false);

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'critical':
                return <AlertCircle size={16} className="severity-critical" />;
            case 'warning':
                return <AlertTriangle size={16} className="severity-warning" />;
            case 'info':
            default:
                return <Info size={16} className="severity-info" />;
        }
    };

    const getSeverityClass = (severity) => {
        switch (severity) {
            case 'critical':
                return 'badge-error';
            case 'warning':
                return 'badge-warning';
            case 'info':
            default:
                return 'badge-info';
        }
    };

    const getCategoryLabel = (category) => {
        const labels = {
            security: '🔒 Security',
            scalability: '📈 Scalability',
            cost: '💰 Cost',
            best_practice: '✨ Best Practice'
        };
        return labels[category] || category;
    };

    const toggleSuggestion = (id) => {
        setExpandedSuggestions(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const toggleAccept = (id) => {
        setAcceptedSuggestions(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const handleSubmitFeedback = () => {
        if (feedback.trim() || acceptedSuggestions.size > 0) {
            onFeedback(feedback, Array.from(acceptedSuggestions));
            setFeedback('');
            setShowFeedbackForm(false);
        }
    };

    const getScoreColor = (score) => {
        if (score >= 80) return 'var(--color-success)';
        if (score >= 60) return 'var(--color-warning)';
        return 'var(--color-error)';
    };

    return (
        <div className="validation-panel panel">
            <div className="panel-header">
                <div className="panel-title">
                    <Shield size={18} />
                    <span>Validation</span>
                </div>
                {hasSession && (
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={onValidate}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={14} className="spinning" />
                                Validating...
                            </>
                        ) : validationResult ? (
                            <>
                                <RotateCcw size={14} />
                                Re-validate
                            </>
                        ) : (
                            <>Validate</>
                        )}
                    </button>
                )}
            </div>

            <div className="panel-content">
                {isLoading ? (
                    <div className="validation-loading">
                        <Loader2 size={24} className="spinning" />
                        <p>Analyzing architecture...</p>
                    </div>
                ) : validationResult ? (
                    <div className="validation-results">
                        {/* Score */}
                        <div className="validation-score">
                            <div
                                className="score-circle"
                                style={{ '--score-color': getScoreColor(validationResult.overall_score) }}
                            >
                                <span className="score-value">{validationResult.overall_score}</span>
                                <span className="score-label">/ 100</span>
                            </div>
                            <div className="score-summary">
                                <h4>Architecture Score</h4>
                                <p>{validationResult.summary}</p>
                            </div>
                        </div>

                        {/* Explanation */}
                        {validationResult.explanation && (
                            <div className="validation-explanation">
                                <h5>Analysis</h5>
                                <p>{validationResult.explanation}</p>
                            </div>
                        )}

                        {/* Suggestions */}
                        {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                            <div className="validation-suggestions">
                                <h5>Suggestions ({validationResult.suggestions.length})</h5>
                                <div className="suggestions-list">
                                    {validationResult.suggestions.map((suggestion) => (
                                        <div
                                            key={suggestion.id}
                                            className={`suggestion-card ${acceptedSuggestions.has(suggestion.id) ? 'accepted' : ''}`}
                                        >
                                            <div
                                                className="suggestion-header"
                                                onClick={() => toggleSuggestion(suggestion.id)}
                                            >
                                                <div className="suggestion-title-row">
                                                    {getSeverityIcon(suggestion.severity)}
                                                    <span className="suggestion-title">{suggestion.title}</span>
                                                    <span className={`badge ${getSeverityClass(suggestion.severity)}`}>
                                                        {suggestion.severity}
                                                    </span>
                                                </div>
                                                <div className="suggestion-meta">
                                                    <span className="suggestion-category">
                                                        {getCategoryLabel(suggestion.category)}
                                                    </span>
                                                    {expandedSuggestions.has(suggestion.id) ? (
                                                        <ChevronUp size={14} />
                                                    ) : (
                                                        <ChevronDown size={14} />
                                                    )}
                                                </div>
                                            </div>

                                            {expandedSuggestions.has(suggestion.id) && (
                                                <div className="suggestion-details">
                                                    <div className="suggestion-description">
                                                        <strong>Issue:</strong> {suggestion.description}
                                                    </div>
                                                    <div className="suggestion-recommendation">
                                                        <strong>Recommendation:</strong> {suggestion.recommendation}
                                                    </div>
                                                    <div className="suggestion-actions">
                                                        <button
                                                            className={`btn btn-sm ${acceptedSuggestions.has(suggestion.id) ? 'btn-primary' : 'btn-ghost'}`}
                                                            onClick={() => toggleAccept(suggestion.id)}
                                                        >
                                                            <ThumbsUp size={14} />
                                                            {acceptedSuggestions.has(suggestion.id) ? 'Accepted' : 'Accept'}
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Feedback Form */}
                        <div className="validation-feedback">
                            {showFeedbackForm ? (
                                <div className="feedback-form">
                                    <textarea
                                        className="input textarea"
                                        value={feedback}
                                        onChange={(e) => setFeedback(e.target.value)}
                                        placeholder="Provide additional feedback or constraints..."
                                        rows={3}
                                    />
                                    <div className="feedback-actions">
                                        <button
                                            className="btn btn-ghost btn-sm"
                                            onClick={() => setShowFeedbackForm(false)}
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            className="btn btn-primary btn-sm"
                                            onClick={handleSubmitFeedback}
                                            disabled={!feedback.trim() && acceptedSuggestions.size === 0}
                                        >
                                            Re-validate with Feedback
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <button
                                    className="btn btn-secondary w-full"
                                    onClick={() => setShowFeedbackForm(true)}
                                >
                                    <ThumbsDown size={14} />
                                    Provide Feedback
                                </button>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="validation-empty">
                        <Shield size={32} className="validation-empty-icon" />
                        <p>No validation performed yet.</p>
                        {hasSession && (
                            <p className="text-sm text-muted">
                                Click "Validate" to analyze your architecture.
                            </p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default ValidationPanel;
