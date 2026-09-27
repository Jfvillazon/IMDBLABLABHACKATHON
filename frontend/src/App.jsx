import { useRef, useState } from 'react';
import { api } from './services/api';
import Connect from './components/Connect';
import Layout from './components/Layout';
import Overview from './components/Overview';
import Findings from './components/Findings';
import Investigation from './components/Investigation';
import Validation from './components/Validation';
import Report from './components/Report';
export default function App() {
  const [repository, setRepository] = useState(null),
    [analysis, setAnalysis] = useState(null),
    [section, setSection] = useState('Overview');
  const [selectedFinding, setSelectedFinding] = useState(null),
    [issue, setIssue] = useState(''),
    [investigation, setInvestigation] = useState(null),
    [validation, setValidation] = useState(null),
    [report, setReport] = useState(null);
  const [busy, setBusy] = useState(''),
    [error, setError] = useState(''),
    [progress, setProgress] = useState(null);
  const locked = useRef(false);
  async function perform(label, task) {
    if (locked.current) return;
    locked.current = true;
    setBusy(label);
    setError('');
    try {
      await task();
    } catch (err) {
      setError(err.message || 'The operation failed. Please retry.');
    } finally {
      locked.current = false;
      setBusy('');
      setProgress(null);
    }
  }
  function clearResults() {
    setSelectedFinding(null);
    setIssue('');
    setInvestigation(null);
    setValidation(null);
    setReport(null);
  }
  async function analyze(target = repository) {
    return perform('Analyzing repository…', async () => {
      const result = await api.analyze(target.repository_id);
      setAnalysis(result.analysis);
      clearResults();
      setSection('Overview');
    });
  }
  async function connect(source, value) {
    await perform(source === 'zip' ? 'Uploading and importing project…' : source === 'github' ? 'Importing GitHub repository…' : 'Connecting demo repository…', async () => {
      const descriptor = source === 'demo' ? await api.demo() : source === 'github' ? await api.github(value) : await api.upload(value, setProgress);
      setRepository(descriptor);
      setProgress(null);
      setBusy('Analyzing repository…');
      const result = await api.analyze(descriptor.repository_id);
      setAnalysis(result.analysis);
      clearResults();
      setSection('Overview');
    });
  }
  function reset() {
    perform('Closing repository session…', async () => {
      // Releasing the handle prevents repeated sessions from exhausting backend capacity.
      let cleanupError = '';
      if (repository) await api.release(repository.repository_id).catch(err => {
        if (!err.message.includes('session has expired')) cleanupError = 'The previous session could not be released. It will expire automatically. ' + err.message;
      });
      setRepository(null);
      setAnalysis(null);
      clearResults();
      setSection('Overview');
      if (cleanupError) setError(cleanupError);
    });
  }
  function changeIssue(value) {
    setIssue(value);
    setInvestigation(null);
    setReport(null);
    setValidation(null);
  }
  function selectFinding(finding) {
    if (locked.current) return;
    setSelectedFinding(finding);
    changeIssue(`${finding.title}\n\n${finding.description}\n\nFile: ${finding.file}${finding.line != null ? `:${finding.line}` : ''}`);
    setError('');
    setSection('Investigate');
  }
  function investigate() {
    perform('Investigating issue…', async () => {
      const result = await api.investigate(repository.repository_id, issue.trim());
      setInvestigation(result.investigation);
      setReport(null);
    });
  }
  function validate() {
    perform('Checking validation…', async () => {
      const result = await api.validate(repository.repository_id);
      setValidation(result.validation);
      setReport(null);
    });
  }
  function generate() {
    perform('Generating report…', async () => {
      const {
        report: result
      } = await api.workflow(repository.repository_id, issue.trim());
      setReport(result);
      setInvestigation({
        issue: result.issue,
        relevant_files: result.relevant_files,
        root_cause: result.root_cause,
        suggested_fix: result.suggested_fix,
        test_generated: result.regression_test,
        confidence: result.confidence
      });
      setValidation({
        tests_run: result.tests_run,
        passed: result.passed,
        failed: result.failed,
        status: result.validation_status,
        reason: result.validation_reason
      });
    });
  }
  if (!analysis) return <Connect onConnect={connect} busy={busy} progress={progress} error={error} repository={repository} onRetry={() => analyze()} onReset={reset} />;
  const common = {
    repository,
    analysis,
    busy,
    navigate: setSection
  };
  return <>
    <a className="skip-link" href="#workspace-content">Skip to workspace</a>
    <Layout {...common} section={section} onReset={reset} onAnalyze={() => analyze()}>
      {busy && <div className="operation-status workspace-status" role="status">
        <span className="spinner" />
        {busy}
      </div>}
      {error && <div className="alert error" role="alert">
        {error}
      </div>}
      {repository.warnings.length > 0 && <details className="import-warnings">
        <summary>{repository.warnings.length} repository import {repository.warnings.length === 1 ? 'notice' : 'notices'}</summary>
        <ul>
          {repository.warnings.map((warning, i) => <li key={i}>
            {warning}
          </li>)}
        </ul>
      </details>}
      {section === 'Overview' && <Overview {...common} onInvestigate={selectFinding} />}
      {section === 'Findings' && <Findings {...common} onInvestigate={selectFinding} />}
      {section === 'Investigate' && <Investigation {...common} issue={issue} onIssueChange={value => {
        setSelectedFinding(null);
        changeIssue(value);
      }} selectedFinding={selectedFinding} investigation={investigation} onRun={investigate} />}
      {section === 'Validation' && <Validation {...common} validation={validation} onRun={validate} />}
      {section === 'Report' && <Report {...common} report={report} issue={issue} onGenerate={generate} />}
    </Layout>
  </>;
}
