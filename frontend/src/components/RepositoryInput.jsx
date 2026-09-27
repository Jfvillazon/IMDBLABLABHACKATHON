import { useState } from 'react';

export default function RepositoryInput({
  onAnalyzeLocal,
  onAnalyzeGitHub,
  onAnalyzeDemo,
  loading = false,
}) {
  const [mode, setMode] = useState('local');
  const [repository, setRepository] = useState('');

  const isGitHub = mode === 'github';

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setRepository('');
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const value = repository.trim();

    if (!value || loading) {
      return;
    }

    if (isGitHub) {
      onAnalyzeGitHub(value);
    } else {
      onAnalyzeLocal(value);
    }
  };

  return (
    <section className="repository-selector">
      <div className="repository-selector__header">
        <span className="repository-selector__eyebrow">
          REPOSITORY DIAGNOSTICS
        </span>

        <h2>Analyze a Repository</h2>

        <p>
          Select a local project or paste a public GitHub repository URL.
          RepoMedic will inspect its architecture, code quality, security,
          testing, and documentation.
        </p>
      </div>

      <div className="repository-selector__tabs">
        <button
          type="button"
          className={`repository-selector__tab ${
            mode === 'local' ? 'repository-selector__tab--active' : ''
          }`}
          onClick={() => handleModeChange('local')}
          disabled={loading}
        >
          Local Repository
        </button>

        <button
          type="button"
          className={`repository-selector__tab ${
            mode === 'github' ? 'repository-selector__tab--active' : ''
          }`}
          onClick={() => handleModeChange('github')}
          disabled={loading}
        >
          GitHub Repository
        </button>
      </div>

      <form
        className="repository-selector__form"
        onSubmit={handleSubmit}
      >
        <label htmlFor="repository-source">
          {isGitHub ? 'GitHub repository URL' : 'Repository path'}
        </label>

        <div className="repository-selector__input-row">
          <input
            id="repository-source"
            type={isGitHub ? 'url' : 'text'}
            value={repository}
            onChange={(event) => setRepository(event.target.value)}
            placeholder={
              isGitHub
                ? 'https://github.com/owner/repository'
                : 'C:\\Users\\Yacine\\Projects\\my-repository'
            }
            disabled={loading}
            autoComplete="off"
          />

          <button
            type="submit"
            className="repository-selector__analyze"
            disabled={!repository.trim() || loading}
          >
            {loading
              ? isGitHub
                ? 'Cloning & Analyzing...'
                : 'Analyzing...'
              : 'Analyze Repository'}
          </button>
        </div>

        <span className="repository-selector__hint">
          {isGitHub
            ? 'Public GitHub repositories only. RepoMedic uses a shallow clone for analysis.'
            : 'Enter a folder path accessible by the RepoMedic backend.'}
        </span>
      </form>

      <div className="repository-selector__divider">
        <span>OR</span>
      </div>

      <button
        type="button"
        className="repository-selector__demo"
        onClick={onAnalyzeDemo}
        disabled={loading}
      >
        {loading ? 'Analyzing...' : 'Try Demo Repository'}
      </button>

      <div className="repository-selector__features">
        <span>✓ Architecture</span>
        <span>✓ Code Quality</span>
        <span>✓ Security</span>
        <span>✓ Testing</span>
        <span>✓ Documentation</span>
      </div>
    </section>
  );
}