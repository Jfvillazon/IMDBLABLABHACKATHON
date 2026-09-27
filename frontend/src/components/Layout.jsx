import { Brand, Icon, Badge, Button } from './UI';
export const sections = ['Overview', 'Findings', 'Investigate', 'Validation', 'Report'];
export default function Layout({
  repository,
  analysis,
  section,
  navigate,
  onReset,
  onAnalyze,
  busy,
  children
}) {
  return <div className="app-shell">
    <aside className="sidebar">
      <Brand />
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Workspace">
        {sections.map((name, index) => <button key={name} className={section === name ? 'active' : ''} aria-current={section === name ? 'page' : undefined} onClick={() => navigate(name)}>
          <Icon name={name === 'Investigate' ? 'investigate' : name.toLowerCase()} />
          <span>
            {name}
          </span>
          {name === 'Findings' ? <span className="nav-count">
            {analysis.findings.length}
          </span> : <span className="nav-index">0{index + 1}</span>}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="repository-tile">
          <span className="nav-caption">CURRENT REPOSITORY</span>
          <strong title={repository.display_name}>
            {repository.display_name}
          </strong>
          <Badge>
            {repository.source.toUpperCase()}
          </Badge>
        </div>
        <button className="new-analysis" disabled={!!busy} onClick={onReset}><Icon name="plus" size={17} />New Analysis</button>
        <p>Built with IBM Bob</p>
      </div>
    </aside>
    <div className="workspace">
      <header className="context-bar">
        <div>
          <Icon name="code" size={18} />
          <strong>
            {repository.display_name}
          </strong>
          <span className="context-divider">/</span>
          <span>
            {section}
          </span>
        </div>
        <div>
          <span className="analysis-status">
            <span className="tiny-dot" />
            {busy ? 'Working' : 'Analysis complete'}
          </span>
          <Badge tone="accent">{analysis.health_score}/100</Badge>
          <Button secondary disabled={!!busy} onClick={onAnalyze}><Icon name="refresh" size={15} />Re-analyze</Button>
        </div>
      </header>
      <main id="workspace-content" className="workspace-content">
        {children}
      </main>
    </div>
  </div>;
}
