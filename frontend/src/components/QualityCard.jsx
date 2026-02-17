import { Star, Package, Layers, CheckCircle, AlertTriangle } from 'lucide-react';
import './QualityCard.css';

function QualityCard({ 
  qualityScore = 0, 
  components = 0, 
  clusters = 0,
  warnings = [],
  suggestions = []
}) {
  const getStarCount = (score) => {
    if (score >= 90) return 5;
    if (score >= 75) return 4;
    if (score >= 60) return 3;
    if (score >= 40) return 2;
    return 1;
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'score-excellent';
    if (score >= 75) return 'score-good';
    if (score >= 60) return 'score-fair';
    return 'score-poor';
  };

  const stars = getStarCount(qualityScore);

  if (qualityScore === 0) return null;

  return (
    <div className="quality-card">
      {/* Score Header */}
      <div className="quality-header">
        <div className="quality-label">Quality Score</div>
        <div className={`quality-score ${getScoreColor(qualityScore)}`}>
          {qualityScore}
          <span className="score-max">/100</span>
        </div>
      </div>

      {/* Star Rating */}
      <div className="quality-stars">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            size={16}
            fill={i < stars ? 'var(--color-primary)' : 'none'}
            stroke={i < stars ? 'var(--color-primary)' : 'var(--border-color)'}
          />
        ))}
      </div>

      {/* Metrics Grid */}
      <div className="quality-metrics">
        <div className="metric-item">
          <div className="metric-icon">
            <Package size={18} />
          </div>
          <div className="metric-info">
            <div className="metric-value">{components}</div>
            <div className="metric-label">Components</div>
          </div>
        </div>

        <div className="metric-item">
          <div className="metric-icon">
            <Layers size={18} />
          </div>
          <div className="metric-info">
            <div className="metric-value">{clusters}</div>
            <div className="metric-label">Clusters</div>
          </div>
        </div>
      </div>

      {/* Feedback */}
      {(warnings.length > 0 || suggestions.length > 0) && (
        <div className="quality-feedback">
          {warnings.length > 0 && (
            <div className="feedback-section feedback-warning">
              <div className="feedback-header">
                <AlertTriangle size={14} />
                <span>{warnings.length} Warning{warnings.length > 1 ? 's' : ''}</span>
              </div>
              <ul className="feedback-list">
                {warnings.slice(0, 2).map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {suggestions.length > 0 && (
            <div className="feedback-section feedback-suggestion">
              <div className="feedback-header">
                <CheckCircle size={14} />
                <span>{suggestions.length} Suggestion{suggestions.length > 1 ? 's' : ''}</span>
              </div>
              <ul className="feedback-list">
                {suggestions.slice(0, 2).map((suggestion, i) => (
                  <li key={i}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default QualityCard;
