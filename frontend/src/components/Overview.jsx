import { Badge, Button, Icon, PageHeading, Empty } from './UI';
export const severityOrder = {
  high: 0,
  medium: 1,
  low: 2
};
export function FindingRow({
  finding,
  onInvestigate,
  detailed = false,
  disabled
}) {
  return <article className="finding-row">
    <div className="finding-main">
      <div className="finding-meta">
        <Badge tone={finding.severity}>
          {finding.severity}
        </Badge>
        <span>
          {finding.category.replaceAll('_', ' ')}
        </span>
      </div>
      <h3>
        {finding.title}
      </h3>
      <div className="file-reference">
        <Icon name="file" size={14} />
        <code>
          {finding.file}
          {finding.line != null ? `:${finding.line}` : ''}
        </code>
      </div>
      {detailed && <>
        <p>
          {finding.description}
        </p>
        <div className="finding-recommendation">
          <strong>Recommendation</strong>
          <p>
            {finding.recommendation}
          </p>
        </div>
      </>}
    </div>
    <button className="text-button" disabled={disabled} onClick={() => onInvestigate(finding)}>Investigate <Icon name="arrow" size={16} /></button>
  </article>;
}
export default function Overview({
  repository,
  analysis,
  onInvestigate,
  navigate,
  busy
}) {
  const counts = Object.fromEntries(['high', 'medium', 'low'].map(s => [s, analysis.findings.filter(f => f.severity === s).length]));
  const categories = Object.entries(analysis.findings.reduce((acc, f) => ({
    ...acc,
    [f.category]: (acc[f.category] || 0) + 1
  }), {})).sort((a, b) => b[1] - a[1]);
  const score = analysis.health_score;
  return <>
    <PageHeading eyebrow="REPOSITORY OVERVIEW" title={repository.display_name} action={<Badge tone="accent">{repository.source.toUpperCase()} REPOSITORY</Badge>}>Your codebase, examined. Start with the risks that matter most.</PageHeading>
    <div className="overview-grid">
      <section className="panel health-panel">
        <div className="panel-title">
          <h2>Repository health</h2>
          <span>STATIC ANALYSIS</span>
        </div>
        <div className="health-content">
          <div className="health-ring" role="img" aria-label={`Repository health ${score} out of 100`}>
            <svg viewBox="0 0 160 160">
              <circle className="ring-track" cx="80" cy="80" r="68" />
              <circle className="ring-value" cx="80" cy="80" r="68" strokeDasharray={`${score / 100 * 427.26} 427.26`} />
            </svg>
            <div>
              <strong>
                {score}
              </strong>
              <span>OUT OF 100</span>
            </div>
          </div>
          <div>
            <Badge tone={counts.high ? 'high' : 'accent'}>
              {counts.high ? 'Needs attention' : analysis.findings.length ? 'Review findings' : 'No findings detected'}
            </Badge>
            <h3>
              {counts.high ? `${counts.high} high-severity ${counts.high === 1 ? 'risk' : 'risks'} to review` : 'Know where you stand'}
            </h3>
            <p>Health reflects the static checks performed on this repository.</p>
            <button className="text-button" onClick={() => navigate('Findings')}>Explore findings <Icon name="arrow" size={16} /></button>
          </div>
        </div>
      </section>
      <section className="metrics-grid">
        {[['Files analyzed', analysis.files_analyzed, 'Source files inspected', 'file'], ['Total findings', analysis.findings.length, 'Across all categories', 'findings'], ['High severity', counts.high, 'Prioritize for review', 'validation'], ['Languages', analysis.languages.length, analysis.languages.join(' · ') || 'None detected', 'code']].map(([label, value, help, icon]) => <div className="metric" key={label}>
          <div>
            <span>
              {label}
            </span>
            <Icon name={icon} size={17} />
          </div>
          <strong>
            {value}
          </strong>
          <p title={help}>
            {help}
          </p>
        </div>)}
      </section>
      <section className="panel">
        <div className="panel-title">
          <h2>Severity distribution</h2>
          <span>{analysis.findings.length} TOTAL</span>
        </div>
        <div className="severity-track">
          {Object.entries(counts).map(([s, count]) => count > 0 && <div key={s} className={s} style={{
            flex: count
          }} title={`${s}: ${count}`} />)}
        </div>
        <div className="severity-legend">
          {Object.entries(counts).map(([s, count]) => <div key={s}>
            <span className={`severity-dot ${s}`} />
            <span>
              {s}
            </span>
            <strong>
              {count}
            </strong>
          </div>)}
        </div>
      </section>
      <section className="panel">
        <div className="panel-title">
          <h2>Risk categories</h2>
          <span>{categories.length} CATEGORIES</span>
        </div>
        <div className="category-bars">
          {categories.length ? categories.map(([category, count]) => <div key={category}>
            <span>
              {category.replaceAll('_', ' ')}
            </span>
            <div>
              <i style={{
                width: `${count / analysis.findings.length * 100}%`
              }} />
            </div>
            <strong>
              {count}
            </strong>
          </div>) : <p>No risk categories detected.</p>}
        </div>
      </section>
    </div>
    <section className="panel priority-panel">
      <div className="panel-title">
        <div>
          <h2>Priority findings</h2>
          <p>Your next steps, ordered by severity.</p>
        </div>
        <Button secondary onClick={() => navigate('Findings')}>View all findings <Icon name="arrow" size={16} /></Button>
      </div>
      {analysis.findings.length ? [...analysis.findings].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]).slice(0, 4).map(f => <FindingRow key={f.id} finding={f} onInvestigate={onInvestigate} disabled={!!busy} />) : <Empty title="No findings detected">These static checks found no issues. You can still investigate a reported problem.</Empty>}
    </section>
    <div className="repository-metadata">
      <span>
        <strong>Source</strong>
        {repository.source.toUpperCase()}
      </span>
      <span>
        <strong>Languages</strong>
        {analysis.languages.join(', ') || 'None detected'}
      </span>
      <span>
        <strong>Files analyzed</strong>
        {analysis.files_analyzed}
      </span>
      {repository.source_details.commit_sha && <span>
        <strong>Commit</strong>
        <code>
          {repository.source_details.commit_sha.slice(0, 12)}
        </code>
      </span>}
    </div>
  </>;
}
