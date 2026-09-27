import { useState } from 'react';
import { Brand, Icon, Button, Badge } from './UI';
export default function Connect({
  onConnect,
  busy,
  progress,
  error,
  repository,
  onRetry,
  onReset
}) {
  const [tab, setTab] = useState('github');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [localError, setLocalError] = useState('');
  const [dragging, setDragging] = useState(false);
  function choose(selected) {
    setLocalError('');
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith('.zip') || selected.size > 25 * 1024 * 1024) {
      setLocalError('Select a ZIP project archive no larger than 25 MiB.');
      setFile(null);
      return;
    }
    setFile(selected);
  }
  function submit(event) {
    event.preventDefault();
    setLocalError('');
    if (tab === 'github' && !/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/i.test(url.trim())) {
      setLocalError('Enter a public repository root URL: https://github.com/owner/repository');
      return;
    }
    onConnect(tab, tab === 'github' ? url.trim() : file);
  }
  return <div className="welcome">
    <header className="welcome-top">
      <Brand />
      <span className="subtle">REPOSITORY INTELLIGENCE <span className="tiny-dot" /></span>
    </header>
    <main className="welcome-main">
      <div className="welcome-copy">
        <div className="eyebrow"><span className="tiny-dot" /> A CLEARER VIEW OF YOUR CODEBASE</div>
        <h1>Healthy code.<br /><span>Confident releases.</span></h1>
        <p className="welcome-lead">Diagnose your repository before problems reach production.</p>
        <p>Find engineering risks, investigate likely root causes, and build a clear path from finding to validated repair.</p>
        <div className="welcome-proof">
          <Icon name="validation" />
          <span>Static analysis first.<br /><strong>Your repository stays unchanged.</strong></span>
        </div>
      </div>
      <section className="connector">
        <div className="connector-heading">
          <span className="eyebrow">START A DIAGNOSTIC SESSION</span>
          <h2>Connect your repository</h2>
          <p>A clearer picture starts with your code.</p>
        </div>
        <div className="connect-tabs" role="group" aria-label="Repository source">
          {[['github', 'code', 'GitHub'], ['zip', 'upload', 'Upload ZIP'], ['demo', 'pulse', 'Try Demo']].map(([key, icon, label]) => <button key={key} aria-pressed={tab === key} disabled={!!busy || !!repository} className={tab === key ? 'active' : ''} onClick={() => {
            setTab(key);
            setLocalError('');
          }}>
            <Icon name={icon} size={17} />
            {label}
          </button>)}
        </div>
        <form onSubmit={submit}>
          <fieldset disabled={!!busy || !!repository}>
            {tab === 'github' ? <>
              <label htmlFor="github-url">Public GitHub repository</label>
              <input id="github-url" type="url" value={url} maxLength={512} onChange={event => setUrl(event.target.value)} placeholder="https://github.com/owner/repository" required />
              <p className="field-help">Public repositories only. Use the repository URL, without a branch or file path.</p>
            </> : tab === 'zip' ? <>
              <label htmlFor="project-zip">Project archive</label>
              <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={event => {
                event.preventDefault();
                if (!busy && !repository) setDragging(true);
              }} onDragLeave={() => setDragging(false)} onDrop={event => {
                event.preventDefault();
                setDragging(false);
                if (!busy && !repository) choose(event.dataTransfer.files[0]);
              }}>
                <Icon name="upload" size={30} />
                <strong>
                  {file ? file.name : 'Drop your project ZIP here'}
                </strong>
                <span>or choose a file below</span>
                <input id="project-zip" type="file" accept=".zip,application/zip" onChange={event => choose(event.target.files[0])} />
              </div>
              <p className="field-help">ZIP project archive · up to 25 MiB. Imported code is never executed.</p>
            </> : <div className="demo-description">
              <span className="demo-icon">
                <Icon name="code" size={28} />
              </span>
              <div>
                <Badge tone="accent">PREPARED REPOSITORY</Badge>
                <h3>A real codebase. Real findings.</h3>
                <p>Explore the included demo repository with engineering issues, root-cause investigation, and a trusted test suite.</p>
              </div>
            </div>}
            {!repository && <Button type="submit" disabled={!!busy || tab === 'zip' && !file}>
              {busy || (tab === 'demo' ? 'Launch Demo' : 'Analyze Repository')}
              <Icon name="arrow" size={17} />
            </Button>}
          </fieldset>
        </form>
        {busy && <div className="operation-status" role="status">
          <span className="spinner" />
          {busy}
          {progress !== null && <span>{progress}% uploaded</span>}
        </div>}
        {(localError || error) && <div className="alert error" role="alert">
          {localError || error}
        </div>}
        {repository && !busy && <div className="retry-import">
          <p><strong>
              {repository.display_name}
            </strong> is connected. Retry analysis without importing again.</p>
          <Button onClick={onRetry}>Retry analysis</Button>
          <Button secondary onClick={onReset}>Choose another repository</Button>
        </div>}
        <div className="connector-foot"><Icon name="validation" size={16} /> Read-only diagnostics. No automatic code changes.</div>
      </section>
    </main>
    <section className="workflow-strip" aria-label="Diagnostic workflow">
      {[['overview', 'Repository health', 'Understand your codebase'], ['findings', 'Risk detection', 'Surface what matters'], ['investigate', 'Root-cause investigation', 'Connect issues to source'], ['code', 'Repair guidance', 'Get a practical next step'], ['validation', 'Validation', 'Check the outcome']].map(([icon, title, detail], i) => <div key={title}>
        <span className="step-number">0{i + 1}</span>
        <Icon name={icon} />
        <h3>
          {title}
        </h3>
        <p>
          {detail}
        </p>
      </div>)}
    </section>
    <footer className="welcome-footer">
      <span>RepoMedic / Engineering diagnostics</span>
      <span>Built with IBM Bob</span>
    </footer>
  </div>;
}
