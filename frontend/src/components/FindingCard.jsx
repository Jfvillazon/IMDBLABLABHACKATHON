import React from 'react';

export default function FindingCard({ finding, isSelected, onSelect }) {
  const { id, severity, category, title, file, line, description, recommendation } = finding;

  return (
    <div
      className={`finding-card finding-card--${severity}${isSelected ? ' finding-card--selected' : ''}`}
    >
      {/* Card header row */}
      <div className="finding-card__header">
        <span className={`severity-badge severity-badge--${severity}`}>{severity}</span>
        <span className="finding-card__id">{id}</span>
        <span className="finding-card__category">{category}</span>
        <button
          className={`btn btn--investigate${isSelected ? ' btn--investigate-active' : ''}`}
          onClick={() => onSelect(finding)}
          title="Use this finding as the investigation prompt"
        >
          {isSelected ? '✓ Selected' : 'Investigate'}
        </button>
      </div>

      {/* Title */}
      <div className="finding-card__title">{title}</div>

      {/* File + line */}
      <div className="finding-card__location">
        <span className="finding-card__file">{file}</span>
        {line != null && (
          <span className="finding-card__line">line {line}</span>
        )}
      </div>

      {/* Description */}
      <div className="finding-card__description">{description}</div>

      {/* Recommendation */}
      <div className="finding-card__recommendation">
        <span className="finding-card__rec-label">Recommendation</span>
        {recommendation}
      </div>
    </div>
  );
}
