import React, { useState } from 'react';
import FindingCard from './FindingCard.jsx';

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };

const FILTER_OPTIONS = [
  { value: 'all',    label: 'All' },
  { value: 'high',   label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low',    label: 'Low' },
];

export default function FindingsList({ findings, selectedFinding, onSelect }) {
  const [filter, setFilter] = useState('all');

  if (findings.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">✓</div>
        <div className="empty-state__title">No findings detected</div>
        <div className="empty-state__body">
          The analysis did not identify any engineering issues in this repository.
          You can still describe a problem manually below.
        </div>
      </div>
    );
  }

  const visible = filter === 'all'
    ? [...findings].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
    : findings.filter((f) => f.severity === filter);

  return (
    <section className="findings-section">
      {/* Section header + filter */}
      <div className="findings-section__header">
        <h2 className="findings-section__title">
          Findings
          <span className="findings-section__count">{findings.length}</span>
        </h2>
        <div className="filter-tabs">
          {FILTER_OPTIONS.map(({ value, label }) => {
            const count = value === 'all'
              ? findings.length
              : findings.filter((f) => f.severity === value).length;
            return (
              <button
                key={value}
                className={`filter-tab${filter === value ? ' filter-tab--active' : ''}`}
                onClick={() => setFilter(value)}
              >
                {label}
                <span className="filter-tab__count">{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Cards */}
      <div className="findings-list">
        {visible.map((finding) => (
          <FindingCard
            key={finding.id}
            finding={finding}
            isSelected={selectedFinding?.id === finding.id}
            onSelect={onSelect}
          />
        ))}
        {visible.length === 0 && (
          <div className="findings-empty-filter">
            No {filter} severity findings.
          </div>
        )}
      </div>
    </section>
  );
}
