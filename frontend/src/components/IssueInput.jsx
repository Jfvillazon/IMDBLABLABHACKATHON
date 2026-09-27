import React from 'react';

/**
 * IssueInput — investigation preparation panel.
 *
 * Props:
 *   selectedFinding  — the currently selected FindingCard object (or null)
 *   issueText        — controlled textarea value
 *   onIssueChange    — (newText: string) => void
 *   onClearFinding   — () => void  — deselects the finding without clearing text
 *   onInvestigate    — () => void  — triggers the investigation API call
 *   isInvestigating  — boolean     — true while API request is in flight
 */
export default function IssueInput({
  selectedFinding,
  issueText,
  onIssueChange,
  onClearFinding,
  onInvestigate,
  isInvestigating,
}) {
  const canSubmit = issueText.trim().length > 0 && !isInvestigating;

  return (
    <section className="issue-section">
      <h2 className="issue-section__title">Investigate a Problem</h2>
      <p className="issue-section__subtitle">
        Select a finding above to pre-fill, or describe any issue manually.
      </p>

      {/* Source badge — shows which finding is pre-filling the textarea */}
      {selectedFinding && (
        <div className="issue-source-badge">
          <span className={`severity-badge severity-badge--${selectedFinding.severity}`}>
            {selectedFinding.severity}
          </span>
          <span className="issue-source-badge__text">
            {selectedFinding.id} · {selectedFinding.title}
          </span>
          <button
            className="issue-source-badge__clear"
            onClick={onClearFinding}
            title="Deselect finding"
            disabled={isInvestigating}
          >
            ✕
          </button>
        </div>
      )}

      <textarea
        className="issue-textarea"
        value={issueText}
        onChange={(e) => onIssueChange(e.target.value)}
        placeholder="Describe the bug or issue you want to investigate…"
        rows={5}
        disabled={isInvestigating}
      />

      <div className="issue-actions">
        <button
          className="btn btn--primary"
          disabled={!canSubmit}
          onClick={onInvestigate}
        >
          {isInvestigating ? 'Investigating…' : 'Investigate Problem'}
        </button>
        {issueText.trim() && !isInvestigating && (
          <span className="issue-actions__hint">Ready to investigate</span>
        )}
        {isInvestigating && (
          <span className="issue-actions__hint issue-actions__hint--working">
            Investigating problem…
          </span>
        )}
      </div>
    </section>
  );
}
