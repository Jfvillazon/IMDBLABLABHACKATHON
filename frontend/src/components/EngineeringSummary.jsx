import React from 'react';

/**
 * EngineeringSummary — final one-screen recap after a completed validation.
 *
 * Renders ONLY data returned by the three APIs. No fabrication.
 *
 * Props:
 *   analyzeData     — AnalyzeResponse
 *   investigateData — InvestigateResponse
 *   validateData    — ValidateResponse
 */
export default function EngineeringSummary({ analyzeData, investigateData, validateData }) {
  /* ── Helpers ── */
  function healthClass(score) {
    if (score >= 70) return 'good';
    if (score >= 40) return 'medium';
    return 'poor';
  }

  function countBySev(findings, sev) {
    return findings.filter((f) => f.severity === sev).length;
  }

  const cls           = healthClass(analyzeData.health_score);
  const high          = countBySev(analyzeData.findings, 'high');
  const medium        = countBySev(analyzeData.findings, 'medium');
  const low           = countBySev(analyzeData.findings, 'low');
  const confidencePct = Math.round(investigateData.confidence * 100);

  const valStatusConfig = {
    passed: { modifier: 'summary-val-badge--passed', label: 'Passed' },
    failed: { modifier: 'summary-val-badge--failed', label: 'Failed' },
    error:  { modifier: 'summary-val-badge--error',  label: 'Error'  },
  };
  const valCfg = valStatusConfig[validateData.status] ?? valStatusConfig.error;

  return (
    <section className="eng-summary" aria-label="Engineering Summary">

      <div className="eng-summary__header">
        <h2 className="eng-summary__title">Engineering Summary</h2>
        <p className="eng-summary__subtitle">
          Complete end-to-end diagnosis for <strong>{analyzeData.repository}</strong>
        </p>
      </div>

      <div className="eng-summary__grid">

        {/* ── Block 1: Repository ── */}
        <div className="eng-block">
          <div className="eng-block__label">Repository</div>
          <div className="eng-block__rows">
            <div className="eng-block__row">
              <span className="eng-block__key">Name</span>
              <span className="eng-block__val eng-block__val--mono">{analyzeData.repository}</span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Health Score</span>
              <span className={`eng-block__val eng-block__score eng-block__score--${cls}`}>
                {analyzeData.health_score} / 100
              </span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Files Analysed</span>
              <span className="eng-block__val">{analyzeData.files_analyzed}</span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Languages</span>
              <span className="eng-block__val">
                {analyzeData.languages.length > 0 ? analyzeData.languages.join(', ') : '—'}
              </span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Total Findings</span>
              <span className="eng-block__val">
                {analyzeData.findings.length}
                {' '}
                <span className="eng-block__sev-inline">
                  (<span className="sev-high">{high}H</span>
                  {' · '}
                  <span className="sev-medium">{medium}M</span>
                  {' · '}
                  <span className="sev-low">{low}L</span>)
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* ── Block 2: Investigated Problem ── */}
        <div className="eng-block">
          <div className="eng-block__label">Investigated Problem</div>
          <p className="eng-block__prose">{investigateData.issue}</p>
        </div>

        {/* ── Block 3: Diagnosis ── */}
        <div className="eng-block">
          <div className="eng-block__label">Diagnosis</div>
          <div className="eng-block__rows">
            <div className="eng-block__row eng-block__row--stack">
              <span className="eng-block__key">Root Cause</span>
              <span className="eng-block__val">{investigateData.root_cause}</span>
            </div>
            <div className="eng-block__row eng-block__row--stack">
              <span className="eng-block__key">Suggested Fix</span>
              <span className="eng-block__val">{investigateData.suggested_fix}</span>
            </div>
            <div className="eng-block__row eng-block__row--stack">
              <span className="eng-block__key">Regression-Test Recommendation</span>
              <pre className="eng-block__code">{investigateData.test_generated}</pre>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Confidence</span>
              <span className="eng-block__val">
                <span className={`eng-block__confidence eng-block__confidence--${
                  investigateData.confidence >= 0.75 ? 'high'
                  : investigateData.confidence >= 0.4 ? 'medium'
                  : 'low'
                }`}>{confidencePct}%</span>
              </span>
            </div>
          </div>
        </div>

        {/* ── Block 4: Validation ── */}
        <div className="eng-block">
          <div className="eng-block__label">Validation</div>
          <div className="eng-block__rows">
            <div className="eng-block__row">
              <span className="eng-block__key">Validation Status</span>
              <span className={`summary-val-badge ${valCfg.modifier}`} aria-label={`Validation status: ${valCfg.label}`}>
                {valCfg.label}
              </span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Tests Run</span>
              <span className="eng-block__val">{validateData.tests_run}</span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Passed</span>
              <span className="eng-block__val eng-block__val--passed">{validateData.passed}</span>
            </div>
            <div className="eng-block__row">
              <span className="eng-block__key">Failed</span>
              <span className="eng-block__val eng-block__val--failed">{validateData.failed}</span>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
