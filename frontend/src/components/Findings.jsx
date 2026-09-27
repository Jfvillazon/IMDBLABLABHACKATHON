import { useState } from 'react';
import { PageHeading, Empty, Icon } from './UI';
import { FindingRow, severityOrder } from './Overview';
export default function Findings({
  analysis,
  onInvestigate,
  busy
}) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('all');
  const [category, setCategory] = useState('all');
  const categories = [...new Set(analysis.findings.map(f => f.category))];
  const filtered = analysis.findings.filter(f => (severity === 'all' || f.severity === severity) && (category === 'all' || category === f.category) && [f.title, f.file, f.description, f.recommendation, f.category].join(' ').toLowerCase().includes(search.toLowerCase())).sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
  return <>
    <PageHeading eyebrow="RISK TRIAGE" title="Findings">{analysis.findings.length} findings across your repository. Inspect the evidence and choose what to investigate.</PageHeading>
    <section className="panel findings-panel">
      <div className="filter-bar">
        <label className="search-box">
          <span className="sr-only">Search findings</span>
          <Icon name="investigate" size={18} />
          <input placeholder="Search title, file, or description…" value={search} onChange={e => setSearch(e.target.value)} />
        </label>
        <label>
          <span className="sr-only">Severity</span>
          <select value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="all">All severities</option>
            {['high', 'medium', 'low'].map(s => <option key={s} value={s}>
              {s[0].toUpperCase() + s.slice(1)}
            </option>)}
          </select>
        </label>
        <label>
          <span className="sr-only">Category</span>
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option value="all">All categories</option>
            {categories.map(c => <option key={c} value={c}>
              {c.replaceAll('_', ' ')}
            </option>)}
          </select>
        </label>
      </div>
      <div className="list-caption">{filtered.length} RESULTS <span>Ordered by severity</span></div>
      {filtered.length ? filtered.map(f => <FindingRow key={f.id} finding={f} detailed onInvestigate={onInvestigate} disabled={!!busy} />) : <Empty title={analysis.findings.length ? 'No matching findings' : 'No findings detected'}>
        {analysis.findings.length ? 'Try another search or clear your filters.' : 'The static checks found no issues. Manual investigation is available for reported problems.'}
      </Empty>}
    </section>
  </>;
}
