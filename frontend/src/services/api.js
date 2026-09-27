/**
 * RepoMedic API service.
 *
 * All fetch calls go through /api — Vite's dev proxy rewrites these to
 * http://localhost:8000/api in development. No base URL is hardcoded.
 */

/**
 * POST /api/analyze
 * No request body. Returns AnalyzeResponse.
 *
 * @returns {Promise<{
 *   repository: string,
 *   files_analyzed: number,
 *   languages: string[],
 *   health_score: number,
 *   findings: Array<{
 *     id: string,
 *     category: string,
 *     severity: "high"|"medium"|"low",
 *     title: string,
 *     file: string,
 *     line: number|null,
 *     description: string,
 *     recommendation: string
 *   }>
 * }>}
 */
export async function analyzeRepo() {
  const response = await fetch('/api/analyze', { method: 'POST' });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Analysis failed (${response.status}): ${detail}`);
  }
  return response.json();
}

/**
 * POST /api/investigate
 * Request body: { issue: string }
 * Returns InvestigateResponse.
 *
 * @param {string} issue
 * @returns {Promise<{
 *   issue: string,
 *   relevant_files: string[],
 *   root_cause: string,
 *   suggested_fix: string,
 *   test_generated: string,
 *   confidence: number
 * }>}
 */
export async function investigateIssue(issue) {
  const response = await fetch('/api/investigate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ issue }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Investigation failed (${response.status}): ${detail}`);
  }
  return response.json();
}

/**
 * POST /api/validate
 * No request body. Returns ValidateResponse.
 *
 * @returns {Promise<{
 *   tests_run: number,
 *   passed: number,
 *   failed: number,
 *   status: "passed"|"failed"|"error"
 * }>}
 */
export async function validateRepo() {
  const response = await fetch('/api/validate', { method: 'POST' });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Validation failed (${response.status}): ${detail}`);
  }
  return response.json();
}
