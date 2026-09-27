import test from 'node:test';
import assert from 'node:assert/strict';
import { api, errorMessage } from './api.js';
test('bodyless operations and scoped issue requests follow the backend contract', async t => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({
      url,
      ...options
    });
    return {
      ok: true,
      status: 200,
      json: async () => ({
        repository_id: 'repo'
      })
    };
  });
  await api.demo();
  await api.analyze('repo');
  await api.validate('repo');
  for (const call of calls) {
    assert.equal(call.method, 'POST');
    assert.equal(call.body, undefined);
    assert.equal(call.headers, undefined);
  }
  await api.github('https://github.com/owner/repo');
  assert.deepEqual(JSON.parse(calls.at(-1).body), {
    url: 'https://github.com/owner/repo'
  });
  await api.investigate('a/b', 'A reported issue');
  assert.equal(calls.at(-1).url, '/api/repositories/a%2Fb/investigate');
  assert.deepEqual(JSON.parse(calls.at(-1).body), {
    issue: 'A reported issue'
  });
  await api.workflow('repo', 'A reported issue');
  assert.equal(calls.at(-1).url, '/api/repositories/repo/workflow');
  assert.deepEqual(JSON.parse(calls.at(-1).body), {
    issue: 'A reported issue'
  });
});
test('backend failures and disconnected backends produce actionable errors', async t => {
  const mock = t.mock.method(globalThis, 'fetch', async () => ({
    ok: false,
    status: 404,
    json: async () => ({
      detail: 'Repository not found'
    })
  }));
  await assert.rejects(api.analyze('expired'), /expired/);
  mock.mock.mockImplementation(async () => {
    throw new TypeError('Failed to fetch');
  });
  await assert.rejects(api.demo(), /backend is running on port 8000/);
  assert.match(errorMessage(422, {
    detail: [{
      msg: 'Field required'
    }]
  }), /Field required/);
});
test('repository release accepts an empty 204 response', async t => {
  let call;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    call = {
      url,
      ...options
    };
    return {
      status: 204
    };
  });
  await api.release('repo');
  assert.equal(call.method, 'DELETE');
  assert.equal(call.body, undefined);
});
test('ZIP uses a single multipart file, upload progress, and backend protection result', async t => {
  let xhr;
  class UploadRequest {
    constructor() {
      xhr = this;
      this.upload = {};
    }
    open(method, url) {
      this.method = method;
      this.url = url;
    }
    send(body) {
      this.body = body;
    }
  }
  globalThis.XMLHttpRequest = UploadRequest;
  t.after(() => delete globalThis.XMLHttpRequest);
  const file = new File(['archive'], 'project.zip', {
    type: 'application/zip'
  });
  const progress = [];
  const promise = api.upload(file, value => progress.push(value));
  assert.equal(xhr.url, '/api/repositories/zip');
  assert.deepEqual([...xhr.body.keys()], ['file']);
  assert.equal(xhr.body.get('file').name, 'project.zip');
  xhr.upload.onprogress({
    lengthComputable: true,
    loaded: 5,
    total: 10
  });
  xhr.status = 201;
  xhr.responseText = JSON.stringify({
    source: 'zip',
    capabilities: {
      validate: false
    }
  });
  xhr.onload();
  assert.equal((await promise).capabilities.validate, false);
  assert.deepEqual(progress, [50]);
});
test('malformed upload responses reject instead of silently entering a workspace', async t => {
  let xhr;
  class UploadRequest {
    constructor() {
      xhr = this;
      this.upload = {};
    }
    open() {}
    send() {}
  }
  globalThis.XMLHttpRequest = UploadRequest;
  t.after(() => delete globalThis.XMLHttpRequest);
  const promise = api.upload(new File(['bad'], 'bad.zip'), () => {});
  xhr.status = 502;
  xhr.responseText = '<html>Bad gateway</html>';
  xhr.onload();
  await assert.rejects(promise, /unreadable upload response/);
});
