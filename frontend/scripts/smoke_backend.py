"""Exercise real demo/ZIP contracts and emit temporary UI-render inputs. No Git."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

# Keep all backend, sample-repository, and test files unchanged.
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTEST_ADDOPTS'] = '-p no:cacheprovider'
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fastapi.testclient import TestClient
from backend.main import app


def result(response):
    assert response.is_success, (response.status_code, response.text)
    return response.json()


with tempfile.TemporaryDirectory(prefix='repomedic-ui-smoke-') as workspace:
    os.environ['REPOMEDIC_WORKSPACE_ROOT'] = workspace
    with TestClient(app) as client:
        demo = result(client.post('/api/repositories/demo'))
        assert demo['source'] == 'demo' and demo['capabilities']['validate']
        path = '/api/repositories/' + demo['repository_id']
        analysis = result(client.post(path + '/analyze'))['analysis']
        assert analysis['findings']
        finding = analysis['findings'][0]
        issue = finding['title'] + '\n' + finding['description']
        investigation = result(client.post(path + '/investigate', json={'issue': issue}))['investigation']
        validation = result(client.post(path + '/validate'))['validation']
        assert validation['status'] in ('passed', 'failed', 'error')
        report = result(client.post(path + '/workflow', json={'issue': issue}))['report']
        assert report['issue'] == issue
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr('project/app.py', 'def divide(a, b):\n    return a / b\n')
            zipped.writestr('project/README.md', '# UI verification repository\n')
        uploaded = result(client.post('/api/repositories/zip', files={'file': ('ui-check.zip', archive.getvalue(), 'application/zip')}))
        imported_path = '/api/repositories/' + uploaded['repository_id']
        imported_analysis = result(client.post(imported_path + '/analyze'))['analysis']
        imported_validation = result(client.post(imported_path + '/validate'))['validation']
        assert imported_validation == {'tests_run': 0, 'passed': 0, 'failed': 0, 'status': 'not_run', 'reason': 'untrusted_repository'}
        imported_report = result(client.post(imported_path + '/workflow', json={'issue': 'Division by zero'}))['report']
        assert imported_report['validation_status'] == 'not_run'
        assert client.post('/api/repositories/github', json={'url': 'not-a-url'}).status_code == 422
        assert client.post('/api/repositories/zip', files={'file': ('bad.zip', b'not a zip', 'application/zip')}).status_code == 422
        for descriptor in (demo, uploaded):
            assert client.delete('/api/repositories/' + descriptor['repository_id']).status_code == 204
        output = {'repository': demo, 'analysis': analysis, 'investigation': investigation, 'validation': validation, 'report': report,
                  'imported_repository': uploaded, 'imported_analysis': imported_analysis, 'imported_validation': imported_validation, 'imported_report': imported_report}
        output_path = Path(tempfile.gettempdir()) / 'repomedic-frontend-smoke.json'
        output_path.write_text(json.dumps(output))
        print(f'Demo: {analysis["files_analyzed"]} files, {len(analysis["findings"])} findings, health {analysis["health_score"]}; validation {validation}')
        print(f'ZIP: {imported_analysis["files_analyzed"]} files; execution protected. Invalid GitHub/ZIP inputs rejected. Handles released.')
        print(f'Real response render inputs: {output_path}')
