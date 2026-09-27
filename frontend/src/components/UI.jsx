export function Icon({
  name = 'pulse',
  size = 20
}) {
  const paths = {
    pulse: 'M2 12h5l3-8 4 16 3-8h5',
    overview: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    findings: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
    investigate: 'M21 21l-6-6 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
    validation: 'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z M8 12l3 3 5-6',
    report: 'M14 2H5v20h14V7z M14 2v6h5 M8 12h8M8 16h8',
    arrow: 'M4 12h16M14 6l6 6-6 6',
    upload: 'M12 16V3M7 8l5-5 5 5M4 16v5h16v-5',
    code: 'M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16',
    refresh: 'M20 7v5h-5M4 17v-5h5 M5 8a8 8 0 0 1 14-2l1 6 M4 12l1 6a8 8 0 0 0 14-2',
    plus: 'M12 5v14M5 12h14',
    file: 'M14 2H5v20h14V7zM14 2v6h5',
    check: 'M4 12l5 5L20 6'
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={paths[name] || paths.code} />
  </svg>;
}
export function Brand() {
  return <div className="brand"><span className="brand-mark">
      <Icon />
    </span>RepoMedic<span className="brand-version">/</span></div>;
}
export function Badge({
  children,
  tone = ''
}) {
  return <span className={`badge ${tone}`}>
    {children}
  </span>;
}
export function Button({
  children,
  secondary = false,
  ...props
}) {
  return <button className={`button ${secondary ? 'secondary' : ''}`} {...props}>
    {children}
  </button>;
}
export function Empty({
  title,
  children
}) {
  return <div className="empty">
    <span className="empty-icon">
      <Icon name="investigate" size={28} />
    </span>
    <h3>
      {title}
    </h3>
    <p>
      {children}
    </p>
  </div>;
}
export function PageHeading({
  eyebrow,
  title,
  children,
  action
}) {
  return <header className="page-heading">
    <div>
      <div className="eyebrow">
        {eyebrow}
      </div>
      <h1>
        {title}
      </h1>
      <p>
        {children}
      </p>
    </div>
    {action}
  </header>;
}
export function FileList({
  files
}) {
  return <div className="file-list">
    {files.length ? files.map(file => <div key={file}>
      <Icon name="file" size={16} />
      <code>
        {file}
      </code>
    </div>) : <p>No relevant files identified.</p>}
  </div>;
}
export function Confidence({
  value
}) {
  const percent = Math.round(value * 100);
  return <div className="confidence">
    <div>
      <span>Investigation confidence</span>
      <strong>{percent}%</strong>
    </div>
    <meter min="0" max="100" value={percent} aria-label="Investigation confidence" />
    <p>Engine estimate · review against the source</p>
  </div>;
}
export function ResultText({
  label,
  children,
  tone = ''
}) {
  return <section className={`result-text ${tone}`}>
    <h3>
      {label}
    </h3>
    <p>
      {children}
    </p>
  </section>;
}
