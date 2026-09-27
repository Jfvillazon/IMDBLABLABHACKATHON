import { PageHeading, Badge, Button, Icon, Empty, FileList, Confidence, ResultText } from './UI';
export default function Investigation({
  issue,
  onIssueChange,
  selectedFinding,
  investigation,
  onRun,
  busy,
  navigate
}) {
  return <>
    <PageHeading eyebrow="FROM SYMPTOM TO SOURCE" title="Investigation">Follow the evidence to a likely root cause and a practical repair recommendation.</PageHeading>
    <div className="investigation-grid">
      <section className="panel issue-panel">
        <div className="panel-title">
          <h2>Issue / problem</h2>
          <Icon name="investigate" />
        </div>
        {selectedFinding && <div className="selected-finding">
          <Badge tone={selectedFinding.severity}>
            {selectedFinding.severity}
          </Badge>
          <strong>
            {selectedFinding.title}
          </strong>
          <code>
            {selectedFinding.file}
            {selectedFinding.line != null ? `:${selectedFinding.line}` : ''}
          </code>
        </div>}
        <form onSubmit={e => {
          e.preventDefault();
          onRun();
        }}>
          <label htmlFor="issue">Describe the behavior to investigate</label>
          <textarea id="issue" rows={8} maxLength={10000} value={issue} disabled={!!busy} onChange={e => onIssueChange(e.target.value)} placeholder="What went wrong? Include expected behavior, symptoms, or a file reference." required />
          <p className="field-help">Select a finding or describe a problem in your own words.</p>
          <Button disabled={!!busy || !issue.trim()} type="submit">
            {busy === 'Investigating issue…' ? 'Investigating…' : 'Investigate issue'}
            <Icon name="arrow" size={16} />
          </Button>
        </form>
        <div className="note">
          <Icon name="validation" size={17} />
          <p>Recommendations are guidance. Repairs and regression tests are not applied automatically.</p>
        </div>
      </section>
      <div className="investigation-result">
        {investigation ? <>
          <section className="panel">
            <div className="panel-title">
              <h2>Investigation results</h2>
              <Badge tone="accent">COMPLETE</Badge>
            </div>
            <ResultText label="Likely root cause">
              {investigation.root_cause}
            </ResultText>
            <h3 className="section-label">Relevant files</h3>
            <FileList files={investigation.relevant_files} />
            <Confidence value={investigation.confidence} />
          </section>
          <ResultText label="Recommended repair" tone="repair">
            {investigation.suggested_fix}
          </ResultText>
          <ResultText label="Regression test recommendation" tone="regression">
            {investigation.test_generated}
          </ResultText>
          <div className="next-action">
            <p>Next, check the validation outcome.</p>
            <Button onClick={() => navigate('Validation')}>Continue to Validation<Icon name="arrow" size={16} /></Button>
          </div>
        </> : <section className="panel">
          <Empty title="Start with a question">Investigate the selected finding or describe a bug. Relevant files, root cause, confidence, and repair guidance will appear here.</Empty>
        </section>}
      </div>
    </div>
  </>;
}
