import sys, json, time, os
sys.path.insert(0, "../probe")
from common import *
S = "<this folder>"; H = os.environ.get("ARBOL_CODEX_SIGNED_HOME", os.path.join(os.path.expanduser("~"), "Library/Application Support/Arbol/drivers/arbol-codex-driver/subscriptions/test-chatgpt/home"))
pr = Proc([which('codex'), 'app-server'], clean_env(CODEX_HOME=H), S)
def req(i, method, params=None, timeout=60):
    m = {'id': i, 'method': method}
    if params is not None: m['params'] = params
    pr.send(m); r = pr.wait_for(lambda o: o.get('id') == i and ('result' in o or 'error' in o), timeout); return r[1] if r else None
init = req(1, 'initialize', {'clientInfo': {'name': 'arbol-codex-driver', 'version': '1.0.0'}}); pr.send({'method': 'initialized'})
before = req(2, 'account/read', {})
start = req(3, 'account/login/start', {'type': 'chatgpt'}, 90)
out = {'codexHome': (init or {}).get('result', {}).get('codexHome'), 'accountBefore': (before or {}).get('result', {}).get('account') is not None}
if not start or 'result' not in start:
    out['error'] = (start or {}).get('error', 'no answer to account/login/start'); open(S + '/codex_done', 'w').write(json.dumps(out)); pr.close(); print(out); sys.exit(1)
open(S + '/codex_url.tmp', 'w').write(start['result'].get('authUrl', '')); os.replace(S + '/codex_url.tmp', S + '/codex_url')
t0 = time.time()
done = pr.wait_for(lambda o: o.get('method') == 'account/login/completed', 600)
out['waited'] = round(time.time() - t0)
out['completed'] = (done[1].get('params') if done else 'timeout after 10 minutes')
if done and done[1].get('params', {}).get('success'):
    acc = req(4, 'account/read', {}); a = ((acc or {}).get('result') or {}).get('account') or {}
    out['account'] = {'type': a.get('type'), 'planType': a.get('planType'), 'hasEmail': bool(a.get('email'))}
    rl = req(5, 'account/rateLimits/read', None, 60); out['rateLimits'] = (rl or {}).get('result', (rl or {}).get('error'))
    out['notifications'] = sorted({x.get('method') for t, x in pr.out if x.get('method')})
out['homeFiles'] = sorted(os.listdir(H))[:30]
open(S + '/codex_done', 'w').write(json.dumps(out)); pr.close(); print(json.dumps(out)[:1500])
