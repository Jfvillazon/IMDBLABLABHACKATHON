import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { build } from 'esbuild';
const inputs = JSON.parse(readFileSync(join(tmpdir(), 'repomedic-frontend-smoke.json'), 'utf8'));
const temporary = mkdtempSync(join(tmpdir(), 'repomedic-render-'));
const names = ['Connect', 'Overview', 'Findings', 'Investigation', 'Validation', 'Report', 'Layout'];
await build({
  absWorkingDir: resolve(import.meta.dirname, '..'),
  stdin: {
    contents: names.map(name => `export {default as ${name}} from './src/components/${name}.jsx';`).join('\n') + "\nexport {createElement} from 'react'; export {renderToStaticMarkup} from 'react-dom/server';",
    resolveDir: resolve(import.meta.dirname, '..')
  },
  bundle: true,
  platform: 'node',
  format: 'cjs',
  jsx: 'automatic',
  outfile: join(temporary, 'components.cjs'),
  logLevel: 'silent'
});
const components = createRequire(import.meta.url)(join(temporary, 'components.cjs'));
const React = {
  createElement: components.createElement
};
const noop = () => {};
async function render(name, props) {
  return components.renderToStaticMarkup(React.createElement(components[name], props));
}
try {
  const shared = {
    ...inputs,
    busy: '',
    navigate: noop,
    onInvestigate: noop
  };
  const welcome = await render('Connect', {
    onConnect: noop,
    busy: '',
    progress: null,
    error: '',
    repository: null,
    onRetry: noop,
    onReset: noop
  });
  assert.match(welcome, /Connect your repository/);
  assert.match(welcome, /Try Demo/);
  const overview = await render('Overview', shared);
  assert.match(overview, new RegExp(`Repository health ${inputs.analysis.health_score} out of 100`));
  assert.match(overview, /Priority findings/);
  const findings = await render('Findings', shared);
  assert.match(findings, /Recommendation/);
  const investigation = await render('Investigation', {
    ...shared,
    issue: inputs.investigation.issue,
    onIssueChange: noop,
    onRun: noop,
    selectedFinding: inputs.analysis.findings[0]
  });
  assert.match(investigation, /Regression test recommendation/);
  assert.match(investigation, /Investigation confidence/);
  const validation = await render('Validation', {
    ...shared,
    onRun: noop
  });
  assert.match(validation, /Validation error/);
  const imported = await render('Validation', {
    ...shared,
    repository: inputs.imported_repository,
    validation: inputs.imported_validation,
    onRun: noop
  });
  assert.match(imported, /Execution protected/);
  assert.match(imported, /No tests were executed/);
  const report = await render('Report', {
    ...shared,
    issue: inputs.report.issue,
    onGenerate: noop
  });
  assert.match(report, /Diagnostic report/);
  assert.match(report, /Validation error/);
  const importedReport = await render('Report', {
    ...shared,
    repository: inputs.imported_repository,
    analysis: inputs.imported_analysis,
    report: inputs.imported_report,
    issue: inputs.imported_report.issue,
    onGenerate: noop
  });
  assert.match(importedReport, /Not run · execution protected/);
  const empty = await render('Overview', {
    ...shared,
    analysis: {
      ...inputs.analysis,
      health_score: 100,
      findings: [],
      languages: []
    }
  });
  assert.match(empty, /No findings detected/);
  const layout = await render('Layout', {
    ...shared,
    section: 'Overview',
    onReset: noop,
    onAnalyze: noop,
    children: React.createElement('p', null, 'Workspace')
  });
  assert.match(layout, /aria-current="page"/);
  const safe = await render('Report', {
    ...shared,
    report: {
      ...inputs.report,
      issue: '<script>alert(1)</script>'
    },
    issue: 'problem',
    onGenerate: noop
  });
  assert.ok(!safe.includes('<script>'));
  console.log('11 render checks passed using real demo/ZIP responses plus empty and escaping cases.');
} finally {
  rmSync(temporary, {
    recursive: true,
    force: true
  });
}
