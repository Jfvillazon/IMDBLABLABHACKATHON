import React, { useState, useEffect } from 'react';
import { analyzeRepo, investigateIssue, validateRepo } from './services/api.js';
import HealthOverview from './components/HealthOverview.jsx';
import FindingsList from './components/FindingsList.jsx';
import IssueInput from './components/IssueInput.jsx';
import InvestigationResults from './components/InvestigationResults.jsx';
import ValidationResults from './components/ValidationResults.jsx';
import EngineeringSummary from './components/EngineeringSummary.jsx';

/* ── Helpers ─────────────────────────────────────────────── */

function buildIssueText(finding) {
  return `${finding.title}\n\n${finding.description}`;
}

/* ── Workflow step indicator ─────────────────────────────── */

const STEPS = ['Analyse', 'Investigate', 'Validate', 'Summary'];

function WorkflowSteps({ status }) {
  const activeIndex =
    status === 'IDLE' || status === 'ANALYZING' || status === 'ANALYZED' || status === 'ERROR'
      ? 0
      : status === 'INVESTIGATING' || status === 'INVESTIGATED'
      ? 1
      : status === 'VALIDATING' || status === 'VALIDATED'
      ? 2
      : 3; // SUMMARIZED (not a real state, reuse VALIDATED for summary)

  const summaryActive = status === 'VALIDATED';

  return (
    <div className="workflow-steps" aria-label="Workflow progress">
      {STEPS.map((label, i) => {
        const done    = i < activeIndex || (i === 3 && summaryActive);
        const current = i === activeIndex && !(i === 3 && summaryActive);
        return (
          <React.Fragment key={label}>
            <div
              className={`workflow-step ${done ? 'workflow-step--done' : ''} ${current ? 'workflow-step--current' : ''}`}
              aria-current={current ? 'step' : undefined}
            >
              <span className="workflow-step__dot" aria-hidden="true">
                {done ? '✓' : i + 1}
              </span>
              <span className="workflow-step__label">{label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`workflow-connector ${done ? 'workflow-connector--done' : ''}`} aria-hidden="true" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ── Stateless UI pieces ─────────────────────────────────── */

function Header() {
  return (
    <header className="header">
      <div className="header__inner">
        <span className="header__logo">RepoMedic</span>
        <span className="header__tag">IBM Bob 2.0 Hackathon</span>
      </div>
    </header>
  );
}

function LoadingSpinner({ message }) {
  return (
    <div className="spinner-wrap" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <span>{message || 'Loading…'}</span>
    </div>
  );
}

function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner" role="alert">
      <div className="error-banner__title">Something went wrong</div>
      <div>{message}</div>
      {onRetry && (
        <button className="btn btn--ghost error-banner__retry" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

/* ── App state machine ───────────────────────────────────── */
// IDLE → ANALYZING → ANALYZED → INVESTIGATING → INVESTIGATED → VALIDATING → VALIDATED
// Any async step can → ERROR (analyze) or soft-fail back to prior state

export default function App() {
  const [status,          setStatus]          = useState('IDLE');
  const [analyzeData,     setAnalyzeData]     = useState(null);
  const [investigateData, setInvestigateData] = useState(null);
  const [validateData,    setValidateData]    = useState(null);
  const [error,           setError]           = useState(null);
  const [errorContext,    setErrorContext]     = useState(null); // 'analyze'|'investigate'|'validate'
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [issueText,       setIssueText]       = useState('');

  /* Pre-fill textarea when a finding is selected */
  useEffect(() => {
    if (selectedFinding) {
      setIssueText(buildIssueText(selectedFinding));
    }
  }, [selectedFinding]);

  /* ── Analyse ── */
  async function handleAnalyze() {
    setStatus('ANALYZING');
    setError(null); setErrorContext(null);
    setAnalyzeData(null); setInvestigateData(null); setValidateData(null);
    setSelectedFinding(null); setIssueText('');
    try {
      const data = await analyzeRepo();
      setAnalyzeData(data);
      setStatus('ANALYZED');
    } catch (err) {
      setError(err.message);
      setErrorContext('analyze');
      setStatus('ERROR');
    }
  }

  /* ── Investigate ── */
  async function handleInvestigate() {
    const trimmed = issueText.trim();
    if (!trimmed) return;
    setStatus('INVESTIGATING');
    setError(null); setErrorContext(null);
    setInvestigateData(null);
    try {
      const data = await investigateIssue(trimmed);
      setInvestigateData(data);
      setStatus('INVESTIGATED');
    } catch (err) {
      setError(err.message);
      setErrorContext('investigate');
      setStatus('ANALYZED'); // preserve dashboard
    }
  }

  /* ── Investigate Another Issue ── */
  /* Returns to the issue-input state without re-running analysis */
  function handleInvestigateAnother() {
    setStatus('ANALYZED');
    setInvestigateData(null);
    setValidateData(null);
    setError(null); setErrorContext(null);
    setSelectedFinding(null);
    setIssueText('');
  }

  /* ── Validate ── */
  async function handleValidate() {
    setStatus('VALIDATING');
    setError(null); setErrorContext(null);
    setValidateData(null);
    try {
      const data = await validateRepo();
      setValidateData(data);
      setStatus('VALIDATED');
    } catch (err) {
      setError(err.message);
      setErrorContext('validate');
      setStatus('INVESTIGATED'); // preserve investigation results
    }
  }

  /* ── Full Reset ── */
  function handleReset() {
    setStatus('IDLE');
    setAnalyzeData(null); setInvestigateData(null); setValidateData(null);
    setError(null); setErrorContext(null);
    setSelectedFinding(null); setIssueText('');
  }

  /* ── Finding selection ── */
  function handleSelectFinding(finding) {
    if (selectedFinding?.id === finding.id) {
      setSelectedFinding(null);
      setIssueText('');
    } else {
      setSelectedFinding(finding);
    }
  }

  function handleClearFinding() {
    setSelectedFinding(null);
  }

  /* ── Derived flags ── */
  const isAnalyzing     = status === 'ANALYZING';
  const isInvestigating = status === 'INVESTIGATING';
  const isValidating    = status === 'VALIDATING';
  const isBusy          = isAnalyzing || isInvestigating || isValidating;

  const showDashboard     = analyzeData !== null && !isAnalyzing && status !== 'ERROR';
  const showIssueInput    = showDashboard && (status === 'ANALYZED');
  const showInvestigation = investigateData !== null &&
    ['INVESTIGATED', 'VALIDATING', 'VALIDATED'].includes(status);
  const showValidation    = validateData !== null && status === 'VALIDATED';
  const showSummary       = showValidation; // summary lives below validation

  return (
    <>
      <Header />
      <main className="page">

        {/* ── Hero ── */}
        <div className="hero">
          <h1 className="hero__title">Repository Diagnosis &amp; Debugging</h1>
          <p className="hero__subtitle">
            Analyse a repository, identify engineering findings, investigate bugs,
            and validate repairs — powered by IBM Bob.
          </p>
          <div className="hero__actions">
            <button
              className="btn btn--primary"
              onClick={handleAnalyze}
              disabled={isBusy}
              aria-busy={isAnalyzing}
            >
              {isAnalyzing ? 'Analysing…' : 'Analyse Repository'}
            </button>
            {(showDashboard || status === 'ERROR') && (
              <button
                className="btn btn--ghost"
                onClick={handleReset}
                disabled={isBusy}
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* ── Workflow progress steps ── */}
        {(showDashboard || status === 'ERROR') && (
          <WorkflowSteps status={status} />
        )}

        {/* ── Loading states ── */}
        {isAnalyzing     && <LoadingSpinner message="Analysing repository…" />}
        {isInvestigating && <LoadingSpinner message="Investigating problem…" />}
        {isValidating    && <LoadingSpinner message="Running validation…" />}

        {/* ── Hard error: analyze (no dashboard to preserve) ── */}
        {status === 'ERROR' && errorContext === 'analyze' && error && (
          <ErrorBanner message={error} onRetry={handleAnalyze} />
        )}

        {/* ── Soft error: investigate (dashboard preserved) ── */}
        {status === 'ANALYZED' && errorContext === 'investigate' && error && (
          <div className="inv-error-banner" role="alert">
            <div className="inv-error-banner__title">Investigation failed</div>
            <div className="inv-error-banner__message">{error}</div>
            <div className="inv-error-banner__hint">
              Your issue text is preserved — edit the description or try again.
            </div>
          </div>
        )}

        {/* ── Soft error: validate (investigation preserved) ── */}
        {status === 'INVESTIGATED' && errorContext === 'validate' && error && (
          <div className="val-error-banner" role="alert">
            <div className="val-error-banner__title">Validation request failed</div>
            <div className="val-error-banner__message">{error}</div>
            <div className="val-error-banner__actions">
              <button className="btn btn--ghost" onClick={handleValidate}>
                Retry Validation
              </button>
            </div>
          </div>
        )}

        {/* ── Analysis dashboard ── */}
        {showDashboard && (
          <div className="section-block">
            <HealthOverview data={analyzeData} />
            <FindingsList
              findings={analyzeData.findings}
              selectedFinding={selectedFinding}
              onSelect={handleSelectFinding}
            />
          </div>
        )}

        {/* ── Issue input ── */}
        {showIssueInput && (
          <IssueInput
            selectedFinding={selectedFinding}
            issueText={issueText}
            onIssueChange={setIssueText}
            onClearFinding={handleClearFinding}
            onInvestigate={handleInvestigate}
            isInvestigating={isInvestigating}
          />
        )}

        {/* ── Investigation results (stays visible through validation + summary) ── */}
        {showInvestigation && (
          <InvestigationResults
            data={investigateData}
            onRunValidation={handleValidate}
            isValidating={isValidating}
            validationDone={showValidation}
            onInvestigateAnother={handleInvestigateAnother}
          />
        )}

        {/* ── Validation results ── */}
        {showValidation && (
          <ValidationResults
            data={validateData}
            onRetry={handleValidate}
          />
        )}

        {/* ── Engineering summary ── */}
        {showSummary && (
          <EngineeringSummary
            analyzeData={analyzeData}
            investigateData={investigateData}
            validateData={validateData}
          />
        )}

      </main>
    </>
  );
}
