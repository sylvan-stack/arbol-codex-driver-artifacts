import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

home = Path('/Users/msix')
repo = home / 'repos/sylvan-stack/arbol-codex-driver'
arbol = repo.parent / 'arbol'
node = home / '.nvm/versions/node/v24.21.0/bin/node'
uv = home / '.cache/arbol-driver-build/uv-0.12.23/uv-aarch64-apple-darwin'
state = home / 'Library/Application Support/Arbol/drivers/arbol-codex-driver'
registry = home / 'Library/Application Support/Arbol/builds'
evidence = home / 'Artifacts/arbol-codex-driver/research/first-working-build-2026-10-07'
evidence.mkdir(parents=True, exist_ok=True)
temporary = Path(tempfile.mkdtemp(prefix='syl94-build-'))
checkout = temporary / 'checkout'
env = {'HOME': str(home), 'PATH': f'{node.parent}:{uv}:{home / ".local/bin"}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
       'LANG': 'en_US.UTF-8', 'ARBOL_NODE': str(node), 'ARBOL_CONFORMANCE_REPO': str(arbol),
       'ARBOL_BUILD_TEST_STATE_DIR': str(state)}
tool = [str(home / '.local/bin/arbol-builds')]
report = {'check': 'build.first-working', 'task': 'SYL-94', 'at': datetime.now(UTC).isoformat(),
          'nodeVersion': subprocess.check_output([str(node), '--version'], text=True).strip(),
          'checks': [], 'temporaryCheckout': str(checkout)}


def save():
    (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')


def run(arguments, label, expected=0, environment=None, cwd=None):
    result = subprocess.run(arguments, cwd=cwd or temporary, env=environment or env,
                            capture_output=True, text=True, timeout=900)
    (evidence / f'{label}.stdout.txt').write_text(result.stdout)
    (evidence / f'{label}.stderr.txt').write_text(result.stderr)
    if result.returncode != expected:
        raise AssertionError(f'{label}: expected exit {expected}, got {result.returncode}; see saved output')
    return result


def result(arguments, label, expected=0, **kwargs):
    return json.loads(run(arguments, label, expected, **kwargs).stdout)


def passed(name):
    report['checks'].append({'check': name, 'passed': True})
    save()
    print(f'Passed {name}', flush=True)


def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


try:
    run(['git', 'clone', '--quiet', '--no-hardlinks', str(repo), str(checkout)], 'clone')
    commit = run(['git', 'rev-parse', 'HEAD'], 'source-commit', cwd=checkout).stdout.strip()
    assert not run(['git', 'status', '--porcelain'], 'clean-checkout', cwd=checkout).stdout.strip()
    assert result([*tool, 'list', 'arbol-codex-driver'], 'registry-before') == []
    print(f'Building clean commit {commit}', flush=True)
    working = result([*tool, 'build', 'arbol-codex-driver', '--repo', str(checkout)], 'working-build')
    report['working'] = working
    save()
    number = working['build']
    assert number == '1' and working['status'] == 'working'
    assert working['source']['commit'] == commit and not working['source']['uncommittedChanges']
    assert working['contract'] == working['dataFormat'] == 1
    assert working['packageVersion'] == '1.0.0'
    folder = registry / 'arbol-codex-driver' / number
    shutil.copy2(folder / 'build.log', evidence / 'working-build.log')
    log = (folder / 'build.log').read_text()
    assert working['checks'] == [{'name': name, 'passed': True} for name in ('build.unit', 'build.contract', 'dev.build-check')]
    assert 'Ran 128 tests' in log and '38/38' in log
    passed('build.clean-working')
    passed('build.checks')
    manifest = json.loads((folder / 'package-manifest.json').read_text())
    assert manifest['source'] == working['source']
    assert manifest['candidate'] is False and manifest['build'] == number
    assert manifest['entry'] == working['entry'] and manifest['packageVersion'] == '1.0.0'
    python = manifest['python']
    assert python['version'] == '3.14.8' and python['target'] == 'aarch64-apple-darwin'
    assert python['release'] == '20261003'
    assert python['archiveSha256'] == 'd15291f940cfecd2e54010d5e37d2e03aa192f076a65d26ab741372fff2dabfe'
    assert python['executableSha256'] == digest(folder / python['executable'])
    metadata = result([str(folder / python['executable']), '-I', str(folder / 'scripts/check_build.py'), 'metadata'],
                      'metadata', environment={**env, 'ARBOL_BUILD_DIR': str(folder), 'ARBOL_BUILD_NUMBER': number})
    assert metadata['passed'] is True
    report['package'] = {'path': str(folder), 'manifestSha256': digest(folder / 'package-manifest.json'),
                         'source': manifest['source'], 'python': python, 'metadata': metadata}
    passed('build.source-and-runtime')
    live = [json.loads(line) for line in log.splitlines() if line.startswith('{') and '"check":"dev.build-check"' in line][-1]
    assert live['outcome'] == 'passed' and live['subscriptionId'] == 'test-chatgpt'
    assert live['turnsAttempted'] == live['inferenceRequests'] == 1
    assert not live['spendMayBeIncomplete'] and live['provenance']['build'] == number
    assert live['usageBefore']['outcome'] == live['usageAfter']['outcome'] == 'ok'
    assert live['checks'][0]['outcome'] == 'completed' and live['checks'][0]['exit'] == 0
    assert not any(kind.startswith('tool_') for kind in live['checks'][0]['eventTypes'])
    assert not live['childTokenUsage']
    report['live'] = live
    shutil.copy2(live['reportPath'], evidence / 'dev-build-check.json')
    passed('dev.build-check')
    launcher = home / '.local/bin/arbol-codex-driver'
    infos = {}
    for label, arguments in [('default', [str(launcher), 'info']),
                             ('named', [str(launcher), '-v', number, 'info']),
                             ('direct', [str(folder / working['entry']), 'info'])]:
        info = result(arguments, f'launcher-{label}')
        assert (info['driver'], info['version'], info['build'], info['contract']) == ('codex', '1.0.0', number, 1)
        infos[label] = info
    report['launcher'] = infos
    passed('build.launcher-default')
    passed('build.launcher-named')
    caller = temporary / 'caller'
    caller.mkdir()
    minimal = {'HOME': str(caller), 'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    standalone = result([str(folder / working['entry']), 'info'], 'folder-alone', environment=minimal, cwd=caller)
    assert standalone['build'] == number and standalone['version'] == '1.0.0'
    report['folderAlone'] = {'info': standalone, 'environmentKeys': list(minimal), 'path': minimal['PATH']}
    passed('build.folder-alone')
    assert not list((state / 'runs').iterdir()) and not list((state / 'tmp').iterdir())
    assert (state / 'format').read_text().strip() == '1'
    passed('build.test-state-cleanup')
    description = json.loads((checkout / 'arbol-build.json').read_text())
    description['checks'].insert(0, {'name': 'build.intentional-failure', 'kind': 'unit',
                                    'command': '"$ARBOL_BUILD_DIR/bin/arbol-codex-driver" definitely-invalid-command'})
    (checkout / 'arbol-build.json').write_text(json.dumps(description, indent=2) + '\n')
    print('Building intentional failed-check example before any live gate', flush=True)
    failed = result([*tool, 'build', 'arbol-codex-driver', '--repo', str(checkout)], 'failed-build', expected=1)
    report['failed'] = failed
    assert failed['build'] == '2' and failed['status'] == 'failed'
    assert failed['failure']['stage'] == 'check' and failed['failure']['name'] == 'build.intentional-failure'
    assert failed['checks'] == [{'name': 'build.intentional-failure', 'passed': False}]
    assert failed['source']['uncommittedChanges'] is True
    failed_folder = registry / 'arbol-codex-driver' / failed['build']
    assert (failed_folder / 'build.json').is_file() and (failed_folder / 'build.log').is_file()
    failed_log = (failed_folder / 'build.log').read_text()
    assert '"check":"dev.build-check"' not in failed_log
    shutil.copy2(failed_folder / 'build.log', evidence / 'failed-build.log')
    default = result([*tool, 'show', 'arbol-codex-driver'], 'default-after-failure')
    assert default['build'] == number and default['status'] == 'working'
    assert result([str(launcher), 'info'], 'launcher-after-failure')['build'] == number
    refusal = result([str(launcher), '-v', failed['build'], 'info'], 'failed-selection-refusal', expected=1)
    assert refusal['error']['available'] == [number]
    listing = result([*tool, 'list', 'arbol-codex-driver'], 'registry-final')
    assert [(record['build'], record['default']) for record in listing] == [('2', False), ('1', True)]
    report.update(defaultAfterFailure=number, failedSelection=refusal, registry=listing,
                  intentionalFailureInferenceRequests=0)
    passed('build.failed-check-preserves-default')
    report['outcome'] = 'passed'
    report['finishedAt'] = datetime.now(UTC).isoformat()
    save()
    print(json.dumps({'outcome': 'passed', 'build': number, 'failedExample': failed['build'],
                      'evidence': str(evidence / 'verification.json'), 'tokenUsage': live['tokenUsage']}), flush=True)
except BaseException as error:
    report.update(outcome='failed', failure=str(error), finishedAt=datetime.now(UTC).isoformat())
    save()
    raise
