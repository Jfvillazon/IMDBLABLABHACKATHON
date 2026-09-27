import { PageHeading, Button, Icon, Empty, FileList, Confidence, ResultText, Badge } from './UI';
import { ValidationResult } from './Validation';
export default function Report({
  repository,
  analysis,
  report,
  issue,
  onGenerate,
  busy,
  navigate
}) {
  return <>
    <PageHeading eyebrow="ENGINEERING SUMMARY" title="Diagnostic report" action={report && <Button secondary onClick={() => window.print()}>Print report</Button>}>A clear record of the issue, the evidence, and the recommended next steps.</PageHeading>
    <div className="report-toolbar">
      <div>
        <strong>
          {report ? 'Refresh this diagnostic report' : 'Generate your engineering report'}
        </strong>
        <p>The workflow reruns investigation and {repository.source === 'demo' ? 'the trusted demo tests' : 'the validation policy check'}. It does not apply repairs.</p>
      </div>
      <Button onClick={onGenerate} disabled={!!busy || !issue.trim()}>
        {busy === 'Generating report…' ? 'Generating…' : report ? 'Refresh report' : 'Generate report'}
        <Icon name="arrow" size={16} />
      </Button>
    </div>
    {report ? <article className="panel engineering-report">
      <header className="report-header">
        <div>
          <div className="eyebrow">REPOMEDIC / DIAGNOSTIC REPORT</div>
          <h2>
            {repository.display_name}
          </h2>
          <p>{repository.source.toUpperCase()} · {analysis.files_analyzed} files analyzed · {analysis.findings.length} findings</p>
        </div>
        <div className="report-score">
          <strong>
            {analysis.health_score}
            <small>/100</small>
          </strong>
          <span>Repository health</span>
        </div>
      </header>
      <ResultText label="Investigated issue">
        {report.issue}
      </ResultText>
      <div className="report-columns">
        <div>
          <h3 className="section-label">Relevant files</h3>
          <FileList files={report.relevant_files} />
        </div>
        <Confidence value={report.confidence} />
      </div>
      <ResultText label="Likely root cause">
        {report.root_cause}
      </ResultText>
      <ResultText label="Repair recommendation" tone="repair">
        {report.suggested_fix}
      </ResultText>
      <ResultText label="Regression recommendation" tone="regression">
        {report.regression_test}
      </ResultText>
      <section className="report-validation">
        <h3>Validation status</h3>
        <ValidationResult result={{
          ...report,
          status: report.validation_status
        }} />
        <p className="report-outcome">
          {report.outcome}
        </p>
      </section>
      <footer>
        <Badge>READ-ONLY DIAGNOSTIC</Badge>
        <span>Recommendations require engineering review.</span>
      </footer>
    </article> : <section className="panel">
      <Empty title={issue.trim() ? 'Ready to compile the evidence' : 'Choose an issue to report on'}>
        {issue.trim() ? 'Generate the report to combine a fresh investigation with the actual validation outcome.' : 'Start an investigation with a finding or a manual problem description.'}
      </Empty>
      {!issue.trim() && <div className="empty-action">
        <Button secondary onClick={() => navigate('Investigate')}>Go to Investigation<Icon name="arrow" size={16} /></Button>
      </div>}
    </section>}
  </>;
}
