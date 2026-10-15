import sys, json
sys.path.insert(0, '../probe')
from common import *
src = open('t_claude.py').read().split('def shape')[0]; exec(src)
DEAD = {'HTTPS_PROXY': 'http://127.0.0.1:9', 'https_proxy': 'http://127.0.0.1:9', 'ALL_PROXY': 'http://127.0.0.1:9'}
print('=== claude, vendor unreachable')
cwd = os.path.join(ROOT, 'offline'); os.makedirs(cwd)
env = dict(ENV); env.update(DEAD); env['CLAUDE_CODE_MAX_RETRIES'] = '3'
pr = Proc(STD, env, cwd); pr.send(user('Reply with the single word OK.'))
r = pr.wait_for(lambda o: o.get('type') == 'result', 150)
for t, o in pr.out:
    ty = o.get('type'); st = o.get('subtype')
    if ty == 'system' and st == 'api_retry': print(f'  {t:6.1f} api_retry', json.dumps({k: v for k, v in o.items() if k not in ('uuid', 'session_id', 'type', 'subtype')})[:300])
    elif ty == 'assistant' and (o.get('error') or o.get('message', {}).get('model') == '<synthetic>'): print(f'  {t:6.1f} assistant error={o.get("error")!r} text={json.dumps(o.get("message", {}).get("content"))[:200]}')
    elif ty == 'result': print(f'  {t:6.1f} result', json.dumps({k: o.get(k) for k in ('subtype', 'is_error', 'terminal_reason', 'api_error_status', 'num_turns', 'result', 'errors')})[:420])
    elif ty == 'system' and st not in ('init', 'status', 'thinking_tokens', 'commands_changed'): print(f'  {t:6.1f} system {st}')
try: pr.p.stdin.close()
except Exception: pass
try: pr.p.wait(15)
except Exception: pass
print('  result seen:', bool(r), '| exit:', pr.p.returncode, '| stderr end:', ''.join(pr.err)[-300:].strip()); pr.close(1)

print('=== codex, vendor unreachable')
exec(open('t_codex.py').read().split("s = Session('main')")[0].split('CODEX = ')[1].join(['CODEX = ', '']) if False else '')
CODEX = which('codex'); HC = os.path.join(HOME, 'Library/Application Support/Arbol/drivers/arbol-codex-driver/subscriptions/test-chatgpt/home')
cwd = os.path.join(os.path.abspath('work-codex'), 'offline'); os.makedirs(cwd, exist_ok=True)
pr = Proc([CODEX, 'app-server'], clean_env(CODEX_HOME=HC, **DEAD), cwd); n = 0
def req(method, params=None, timeout=60):
    global n; n += 1; i = n; m = {'id': i, 'method': method}
    if params is not None: m['params'] = params
    pr.send(m); r = pr.wait_for(lambda o: o.get('id') == i and ('result' in o or 'error' in o) and 'method' not in o, timeout); return r[1] if r else None
req('initialize', {'clientInfo': {'name': 'arbol-codex-driver', 'version': '1.0.0'}}); pr.send({'method': 'initialized'})
a = req('account/read', {}); print('  account/read:', json.dumps((a or {}).get('result', (a or {}).get('error')))[:160])
ml = req('model/list', {}); print('  model/list:', ('%d models' % len(((ml or {}).get('result') or {}).get('data') or [])) if ml and 'result' in ml else json.dumps((ml or {}).get('error'))[:200])
th = req('thread/start', {'cwd': cwd, 'approvalPolicy': 'never', 'sandbox': 'danger-full-access'}); tid = ((th or {}).get('result') or {}).get('thread', {}).get('id')
print('  thread/start ok:', bool(tid), json.dumps((th or {}).get('error'))[:200] if th and 'error' in th else '')
mark = len(pr.out)
if tid:
    req('turn/start', {'threadId': tid, 'input': [{'type': 'text', 'text': 'Reply with the single word OK.'}], 'approvalPolicy': 'never', 'sandboxPolicy': {'type': 'dangerFullAccess'}, 'effort': 'low'})
    done = pr.wait_for(lambda o: o.get('method') == 'turn/completed', 150, mark)
    for t, o in pr.out[mark:]:
        m = o.get('method'); p = o.get('params') or {}
        if m == 'error': print(f'  {t:6.1f} error', json.dumps({k: p.get(k) for k in ('willRetry', 'error')})[:420])
        elif m == 'turn/completed': print(f'  {t:6.1f} turn/completed', json.dumps({k: (p.get('turn') or {}).get(k) for k in ('status', 'error')})[:420])
        elif m and m not in ('thread/status/changed', 'turn/started', 'item/started', 'item/completed', 'account/rateLimits/updated', 'thread/tokenUsage/updated', 'thread/started'): print(f'  {t:6.1f} {m}', json.dumps(p)[:200])
    print('  turn ended:', bool(done))
print('  exit:', pr.close(3), '| log end:', ''.join(pr.err)[-400:].strip().replace('\n', ' | '))
