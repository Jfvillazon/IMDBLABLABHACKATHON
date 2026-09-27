import React from 'react';

function healthClass(score) {
  if (score >= 70) return 'good';
  if (score >= 40) return 'medium';
  return 'poor';
}

function countBySeverity(findings, severity) {
  return findings.filter((f) => f.severity === severity).length;
}

export default function HealthOverview({ data }) {
  const cls    = healthClass(data.health_score);
  const high   = countBySeverity(data.findings, 'high');
  const medium = countBySeverity(data.findings, 'medium');
  const low    = countBySeverity(data.findings, 'low');

  return (
    <div className="overview-card">
      {/* Left — score */}
      <div className="overview-score">
        <div className={`health-score-number health-score-number--${cls}`}>
          {data.health_score}
        </div>
        <div className="health-score-label">Health Score</div>
        <div className="health-bar-track" style={{ marginTop: 8 }}>
          <div
            className={`health-bar-fill health-bar-fill--${cls}`}
            style={{ width: `${data.health_score}%` }}
          />
        </div>
      </div>

      {/* Centre — repo meta */}
      <div className="overview-meta">
        <div className="overview-repo">{data.repository}</div>
        <div className="overview-detail">
          <span className="overview-detail__item">
            <span className="overview-detail__label">Files</span>
            <strong>{data.files_analyzed}</strong>
          </span>
          <span className="overview-detail__item">
            <span className="overview-detail__label">Languages</span>
            <strong>{data.languages.length > 0 ? data.languages.join(', ') : '—'}</strong>
          </span>
          <span className="overview-detail__item">
            <span className="overview-detail__label">Findings</span>
            <strong>{data.findings.length}</strong>
          </span>
        </div>
      </div>

      {/* Right — severity breakdown */}
      <div className="overview-severity">
        {[
          { sev: 'high',   count: high,   label: 'High'   },
          { sev: 'medium', count: medium, label: 'Medium' },
          { sev: 'low',    count: low,    label: 'Low'    },
        ].map(({ sev, count, label }) => (
          <div className="sev-stat" key={sev}>
            <div className={`sev-stat__count sev-stat__count--${sev}`}>{count}</div>
            <div className="sev-stat__label">{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
