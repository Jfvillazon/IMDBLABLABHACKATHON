import { PageHeading, Badge, Button, Icon } from './UI';
export const statusLabel = status => ({
  passed: 'Passed',
  failed: 'Failed',
  error: 'Validation error',
  not_run: 'Not run · execution protected'
})[status] || 'Not run yet';
export function ValidationResult({
  result
}) {
  return <>
    <div className="validation-outcome">
      <Badge tone={result.status === 'passed' ? 'success' : result.status === 'not_run' ? 'accent' : 'high'}>
        {statusLabel(result.status)}
      </Badge>
      <p>
        {result.status === 'passed' ? 'The existing test suite completed without failures. This does not confirm that a repair was applied.' : result.status === 'failed' ? 'The existing suite contains failing tests. Review the repair guidance and address failures before validating again.' : result.status === 'error' ? 'Validation could not finish reliably. Check the backend test environment and retry.' : 'No tests were executed. No conclusion about test passage or repair effectiveness can be drawn.'}
      </p>
    </div>
    <div className="validation-metrics">
      {[['Tests run', result.tests_run], ['Passed', result.passed], ['Failed', result.failed]].map(([label, value]) => <div key={label}>
        <strong>
          {value}
        </strong>
        <span>
          {label}
        </span>
      </div>)}
    </div>
  </>;
}
export default function Validation({
  repository,
  validation,
  onRun,
  busy,
  navigate
}) {
  const trusted = repository.source === 'demo' && repository.capabilities.validate;
  return <>
    <PageHeading eyebrow="VERIFY THE OUTCOME" title="Validation">Understand what has been tested and where execution is intentionally restricted.</PageHeading>
    <section className={`panel validation-panel ${!trusted ? 'protected' : ''}`}>
      <div className="validation-banner">
        <span className="shield">
          <Icon name="validation" size={34} />
        </span>
        <div>
          <div className="eyebrow">
            {trusted ? 'TRUSTED DEMO ENVIRONMENT' : 'STATIC ANALYSIS BOUNDARY'}
          </div>
          <h2>
            {trusted ? 'Run the repository test suite' : 'Execution protected'}
          </h2>
          <p>
            {trusted ? 'Run the existing tests against the prepared demo repository. Results reflect the current code; no suggested repair has been applied.' : 'RepoMedic analyzed this imported repository statically. Test execution is disabled for untrusted imported code.'}
          </p>
        </div>
      </div>
      {validation ? <ValidationResult result={validation} /> : <p className="validation-pending">
        {trusted ? 'Validation has not run yet. Run the suite to see the actual outcome.' : 'Check the repository policy to retrieve the backend’s validation status. Tests will not be executed.'}
      </p>}
      <div className="panel-actions">
        <Button disabled={!!busy} onClick={onRun}>
          {busy === 'Checking validation…' ? 'Checking validation…' : trusted ? validation ? 'Run validation again' : 'Run validation' : 'Check validation status'}
          <Icon name={trusted ? 'arrow' : 'validation'} size={16} />
        </Button>
        <Button secondary onClick={() => navigate('Report')}>Continue to Report<Icon name="arrow" size={16} /></Button>
      </div>
    </section>
  </>;
}
