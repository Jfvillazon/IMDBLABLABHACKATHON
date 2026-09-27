import React from 'react';

/**
 * InvestigationResults — displays the full investigation output.
 *
 * Props:
 *   data                 — InvestigateResponse object from /api/investigate
 *   onRunValidation      — () => void — calls POST /api/validate
 *   isValidating         — boolean    — true while validation API call is in flight
 *   validationDone       — boolean    — true once validation completed successfully
 *   onInvestigateAnother — () => void — returns to issue-input without re-analyzing
 */
export default function InvestigationResults({ data, onRunValidation, isValidating, validationDone, onInvestigateAnother }) {
  const confidencePct = Math.round(data.confidence * 100);
  const confidenceClass =
    data.confidence >= 0.75
      ? 'confidence-bar__fill--high'
      : data.confidence >= 0.4
      ? 'confidence-bar__fill--medium'
      : 'confidence-bar__fill--low';

  return (
    <section className="investigation-results">

      {/* ── Section header ── */}
      <div className="investigation-results__header">
        <h2 className="investigation-results__title">Investigation Results</h2>
        <span className="investigation-results__issue-label">
          Issue: <em>{data.issue}</em>
        </span>
      </div>

      {/* ── Three answer cards ── */}
      <div className="inv-cards">

        {/* WHY */}
        <div className="inv-card inv-card--why">
          <div className="inv-card__eyebrow">Why is this happening?</div>
          <div className="inv-card__heading">Root Cause</div>
          <p className="inv-card__body">{data.root_cause}</p>
        </div>

        {/* WHAT */}
        <div className="inv-card inv-card--what">
          <div className="inv-card__eyebrow">What should be changed?</div>
          <div className="inv-card__heading">Suggested Fix</div>
          <p className="inv-card__body">{data.suggested_fix}</p>
        </div>

        {/* HOW */}
        <div className="inv-card inv-card--how">
          <div className="inv-card__eyebrow">How to regression-test the repair?</div>
          <div className="inv-card__heading">Regression-Test Recommendation</div>
          <pre className="inv-card__body inv-card__body--code">{data.test_generated}</pre>
        </div>

      </div>

      {/* ── Relevant files ── */}
      <div className="inv-files">
        <div className="inv-files__title">Relevant Files</div>
        {data.relevant_files && data.relevant_files.length > 0 ? (
          <ul className="inv-files__list">
            {data.relevant_files.map((f) => (
              <li key={f} className="inv-files__item">
                <span className="inv-files__icon">📄</span>
                <code className="inv-files__name">{f}</code>
              </li>
            ))}
          </ul>
        ) : (
          <div className="inv-files__empty">
            No specific files were identified for this issue.
          </div>
        )}
      </div>

      {/* ── Confidence ── */}
      <div className="inv-confidence">
        <div className="inv-confidence__header">
          <span className="inv-confidence__label">Confidence</span>
          <span className="inv-confidence__value">{confidencePct}%</span>
        </div>
        <div className="confidence-bar__track">
          <div
            className={`confidence-bar__fill ${confidenceClass}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
        <div className="inv-confidence__hint">
          {data.confidence >= 0.75
            ? 'High confidence — strong pattern match found.'
            : data.confidence >= 0.4
            ? 'Moderate confidence — partial match, review recommended.'
            : 'Low confidence — issue may be novel or ambiguous.'}
        </div>
      </div>

      {/* ── Validation CTA (hidden once validation is complete) ── */}
      {!validationDone && (
        <div className="inv-validate-cta">
          <div className="inv-validate-cta__description">
            Ready to verify the fix? Run the automated validation suite against the repository.
          </div>
          <div className="inv-validate-cta__buttons">
            <button
              className="btn btn--primary btn--validate"
              onClick={onRunValidation}
              disabled={isValidating}
            >
              {isValidating ? 'Running validation…' : 'Run Validation'}
            </button>
            <button
              className="btn btn--ghost"
              onClick={onInvestigateAnother}
              disabled={isValidating}
            >
              Investigate Another Issue
            </button>
          </div>
        </div>
      )}

      {/* ── After validation: offer re-investigation ── */}
      {validationDone && (
        <div className="inv-reinvestigate">
          <button className="btn btn--ghost" onClick={onInvestigateAnother}>
            Investigate Another Issue
          </button>
        </div>
      )}

    </section>
  );
}
