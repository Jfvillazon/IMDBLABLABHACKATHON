import React from 'react';

/**
 * ValidationResults — displays the output of POST /api/validate.
 *
 * Props:
 *   data    — ValidateResponse: { tests_run, passed, failed, status }
 *   onRetry — () => void — called when the user clicks "Run Validation Again"
 */
export default function ValidationResults({ data, onRetry }) {
  const { tests_run, passed, failed, status } = data;

  /* Status-to-visual mapping */
  const statusConfig = {
    passed: {
      modifier:  'val-status--passed',
      label:     'Passed',
      outcome:   'Validation passed. The repository test suite completed successfully.',
    },
    failed: {
      modifier:  'val-status--failed',
      label:     'Failed',
      outcome:   'Validation completed with failing tests. Review the test results before accepting the repair.',
    },
    error: {
      modifier:  'val-status--error',
      label:     'Error',
      outcome:   'Validation could not complete successfully. Review the validation environment or test runner.',
    },
  };

  const cfg = statusConfig[status] ?? statusConfig.error;

  return (
    <section className="validation-results">

      {/* ── Header ── */}
      <div className="validation-results__header">
        <h2 className="validation-results__title">Validation Results</h2>
        <span className={`val-status ${cfg.modifier}`}>{cfg.label}</span>
      </div>

      {/* ── Counts ── */}
      <div className="val-counts">
        <div className="val-count-card">
          <div className="val-count-card__number">{tests_run}</div>
          <div className="val-count-card__label">Tests Run</div>
        </div>
        <div className="val-count-card val-count-card--passed">
          <div className="val-count-card__number val-count-card__number--passed">{passed}</div>
          <div className="val-count-card__label">Passed</div>
        </div>
        <div className="val-count-card val-count-card--failed">
          <div className="val-count-card__number val-count-card__number--failed">{failed}</div>
          <div className="val-count-card__label">Failed</div>
        </div>
      </div>

      {/* ── Outcome sentence ── */}
      <div className={`val-outcome val-outcome--${status}`}>
        {cfg.outcome}
      </div>

      {/* ── Re-run option ── */}
      <div className="val-rerun">
        <button className="btn btn--ghost" onClick={onRetry}>
          Run Validation Again
        </button>
      </div>

    </section>
  );
}
