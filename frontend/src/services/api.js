export async function analyzeRepo() {
  const response = await fetch('/api/analyze', {
    method: 'POST',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Analysis failed (${response.status}): ${detail}`);
  }

  return response.json();
}

async function analyzeSelectedRepo(sourceType, repository) {
  const response = await fetch('/api/repository/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      source_type: sourceType,
      repository: repository,
    }),
  });

  if (!response.ok) {
    let message = `Repository analysis failed (${response.status})`;

    try {
      const data = await response.json();

      if (data && data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep generic message.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function analyzeLocalRepo(repository) {
  return analyzeSelectedRepo('local', repository);
}

export async function analyzeGitHubRepo(repository) {
  return analyzeSelectedRepo('github', repository);
}

export async function investigateIssue(issue) {
  const response = await fetch('/api/investigate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      issue: issue,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Investigation failed (${response.status}): ${detail}`);
  }

  return response.json();
}

export async function validateRepo() {
  const response = await fetch('/api/validate', {
    method: 'POST',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Validation failed (${response.status}): ${detail}`);
  }

  return response.json();
}