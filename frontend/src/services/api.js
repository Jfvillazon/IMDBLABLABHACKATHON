const API_BASE = (import.meta.env?.VITE_API_URL || '').replace(/\/$/, '');
const ROOT = `${API_BASE}/api/repositories`;
export function errorMessage(status, data) {
  const detail = typeof data?.detail === 'string' ? data.detail : Array.isArray(data?.detail) ? data.detail.map(item => item.msg).join('; ') : 'Repository request failed.';
  const hints = {
    404: 'The repository may be inaccessible or this session has expired. Check the public URL or start a new analysis.',
    409: 'Another operation is using this repository. Try again shortly.',
    413: 'Choose a ZIP smaller than 25 MiB and within the repository limits.',
    422: 'Check your input and try again.',
    503: 'Check that the backend is running and has available capacity.',
    504: 'Import timed out. Try a smaller repository.',
    408: 'Upload timed out. Try again.'
  };
  return `${detail} ${hints[status] || 'Please try again.'}`;
}
async function request(path, body, method = 'POST') {
  let response;
  try {
    response = await fetch(`${ROOT}${path}`, {
      method,
      ...(body === undefined ? {} : {
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      })
    });
  } catch {
    throw new Error('Cannot reach RepoMedic. Check that the backend is running on port 8000, then retry.');
  }
  if (response.status === 204) return;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(response.status, data));
  if (!data) throw new Error('The backend returned an unreadable response. Please retry.');
  return data;
}
export function upload(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${ROOT}/zip`);
    xhr.timeout = 120000;
    xhr.upload.onprogress = event => {
      if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100));
    };
    xhr.onerror = () => reject(new Error('Upload could not reach RepoMedic. Check your connection and backend, then retry.'));
    xhr.ontimeout = () => reject(new Error('Upload timed out. Try a smaller archive.'));
    xhr.onload = () => {
      let data;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        reject(new Error('The backend returned an unreadable upload response.'));
        return;
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);else reject(new Error(errorMessage(xhr.status, data)));
    };
    const body = new FormData();
    body.append('file', file);
    xhr.send(body);
  });
}
export const api = {
  demo: () => request('/demo'),
  github: url => request('/github', {
    url
  }),
  upload,
  analyze: id => request(`/${encodeURIComponent(id)}/analyze`),
  investigate: (id, issue) => request(`/${encodeURIComponent(id)}/investigate`, {
    issue
  }),
  validate: id => request(`/${encodeURIComponent(id)}/validate`),
  workflow: (id, issue) => request(`/${encodeURIComponent(id)}/workflow`, {
    issue
  }),
  release: id => request(`/${encodeURIComponent(id)}`, undefined, 'DELETE')
};
