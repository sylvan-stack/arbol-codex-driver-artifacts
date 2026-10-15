import sys, json, collections
sys.path.insert(0, '../probe')
from common import *
CODEX = which('codex')
H = os.path.join(HOME, 'Library/Application Support/Arbol/drivers/arbol-codex-driver/subscriptions/test-chatgpt/home')
ROOT = os.path.abspath('work-codex'); shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT)
def is_id(i): return lambda o: o.get('id') == i and ('result' in o or 'error' in o) and 'method' not in o
class Session:
    def __init__(self, label):
        self.cwd = os.path.join(ROOT, label, 'cwd'); os.makedirs(self.cwd)
        self.pr = Proc([CODEX, 'app-server'], clean_env(CODEX_HOME=H), self.cwd); self.n = 0; self.answered = set(); self.server_requests = []
    def req(self, method, params=None, timeout=90):
        self.n += 1; m = {'id': self.n, 'method': method}
        if params is not None: m['params'] = params
        self.pr.send(m); r = self.pr.wait_for(is_id(self.n), timeout); return r[1] if r else None
    def pump(self):   # answer requests the tool sends
        for t, o in list(self.pr.out):
            if 'method' in o and 'id' in o and o['id'] not in self.answered:
                self.answered.add(o['id']); self.server_requests.append((o['method'], sorted((o.get('params') or {}).keys())))
                if o['method'] in ('item/commandExecution/requestApproval', 'item/fileChange/requestApproval'): self.pr.send({'id': o['id'], 'result': {'decision': 'accept'}})
                else: self.pr.send({'id': o['id'], 'error': {'code': -32601, 'message': 'not supported by this client'}})
    def turn(self, thread, text, limit=300, **extra):
        mark = len(self.pr.out)
        p = {'threadId': thread, 'input': [{'type': 'text', 'text': text}], 'approvalPolicy': 'never', 'sandboxPolicy': {'type': 'dangerFullAccess'}, 'summary': 'detailed'}; p.update(extra)
        r = self.req('turn/start', p); end = time.monotonic() + limit; done = None
        while time.monotonic() < end and not done:
            self.pump()
            for t, o in self.pr.out[mark:]:
                if o.get('method') == 'turn/completed' and (o.get('params') or {}).get('threadId') == thread: done = (t, o)
            if not done: time.sleep(0.3)
        return r, done, self.pr.out[mark:]
def describe(recs, thread):
    c = collections.Counter(); items = []; final = ''
    for t, o in recs:
        m = o.get('method'); p = o.get('params') or {}
        if not m: continue
        same = 'own' if p.get('threadId') in (None, thread) else 'OTHER-THREAD'
        if m in ('item/started', 'item/completed'):
            it = p.get('item') or {}; c[(same, m, it.get('type'))] += 1
            if m == 'item/completed':
                d = {'thread': same, 'type': it.get('type')}
                for k in ('command', 'exitCode', 'status', 'tool', 'server', 'query', 'action', 'senderThreadId', 'receiverThreadIds', 'receiverThreadId', 'newThreadId', 'prompt', 'agentsStates', 'agentStatus'):
                    if k in it: d[k] = (it[k] if not isinstance(it[k], str) else it[k][:110])
                if it.get('type') == 'commandExecution': d['output'] = str(it.get('aggregatedOutput'))[:80]
                if it.get('type') == 'agentMessage': final = it.get('text', ''); d['text'] = final[:140]
                d['keys'] = sorted(it.keys()); items.append(d)
        else: c[(same, m, '')] += 1
    return c, items, final
s = Session('main')
init = s.req('initialize', {'clientInfo': {'name': 'arbol-codex-driver', 'version': '1.0.0'}}); s.pr.send({'method': 'initialized'})
acc = s.req('account/read', {}); ml = s.req('model/list', {})
models = (ml or {}).get('result', {}).get('data') or []
dflt = next((m for m in models if m.get('isDefault')), models[0] if models else {})
print('account:', ((acc or {}).get('result') or {}).get('account', {}).get('planType'), '| models:', [m.get('id') for m in models], '| default:', dflt.get('id'), 'efforts:', [e.get('reasoningEffort') for e in dflt.get('supportedReasoningEfforts', [])])
rl0 = s.req('account/rateLimits/read'); print('weekly window used before:', (((rl0 or {}).get('result') or {}).get('rateLimits') or {}).get('primary', {}).get('usedPercent'))
def start_thread(**extra):
    p = {'cwd': s.cwd, 'approvalPolicy': 'never', 'sandbox': 'danger-full-access', 'model': dflt.get('id')}; p.update(extra)
    r = s.req('thread/start', p); res = (r or {}).get('result') or {}
    return (res.get('thread') or {}).get('id'), res, r
print('\n=== T2: full access (write in the folder, write outside it, the network)')
th, res, raw = start_thread()
print('thread:', bool(th), '| sandbox reported:', json.dumps(res.get('sandbox'))[:120], '| approvalPolicy:', res.get('approvalPolicy'), '| multiAgentMode:', res.get('multiAgentMode'), '| error:', (raw or {}).get('error'))
r, done, recs = s.turn(th, "Do exactly these three things with your shell tool, one command each, then answer. 1) `echo full-access-ok > probe.txt && cat probe.txt` 2) `echo outside-ok > ../outside-probe.txt && cat ../outside-probe.txt` 3) `curl -s -o /dev/null -w '%{http_code}' https://example.com`. Reply with exactly one line: FILE=<output of 1> OUTSIDE=<output of 2> HTTP=<output of 3>", effort='low')
c, items, final = describe(recs, th)
print('turn status:', ((done[1]['params'].get('turn') or {}).get('status') if done else 'no completion'), '| answer:', final[:160])
for d in items:
    if d['type'] != 'agentMessage': print('   item:', {k: v for k, v in d.items() if k != 'keys'})
print('requests the tool sent to the client:', s.server_requests)
print('files:', os.path.exists(os.path.join(s.cwd, 'probe.txt')), os.path.exists(os.path.join(s.cwd, '..', 'outside-probe.txt')))
print('\n=== T4: web search and the list of tools')
th2, res2, _ = start_thread()
r, done, recs = s.turn(th2, "First list the exact names of all tools you can call right now, one per line. Then use your web search tool once for the query: IANA example domains. On the last line write RESULT: followed by the title of one result, or RESULT: NO-SEARCH-TOOL if you have no web search tool.", effort='low')
c, items, final = describe(recs, th2)
print('turn status:', ((done[1]['params'].get('turn') or {}).get('status') if done else 'no completion')); print('answer:\n' + final[:900])
print('item types:', sorted({(k[1], k[2]) for k in c if k[2]}))
for d in items:
    if d['type'] not in ('agentMessage', 'reasoning'): print('   item:', d)
print('\n=== T1b: a sub-agent on codex')
th3, res3, _ = start_thread()
r, done, recs = s.turn(th3, "Start exactly one sub-agent with your tool for spawning agents. Its job: 'Run the shell command `echo sub-agent-says-FIG` and report exactly what it printed.' Wait until it has finished. Then reply with exactly one line: MAIN-DONE followed by what the sub-agent reported. If you have no tool for spawning agents, reply NO-AGENT-TOOL.", effort='low', limit=360)
time.sleep(2); recs = s.pr.out[-len(recs) - 200:] if False else recs + [x for x in s.pr.out if x not in recs][-0:]
c, items, final = describe(recs, th3)
print('turn status:', ((done[1]['params'].get('turn') or {}).get('status') if done else 'no completion'), '| answer:', final[:200])
print('notifications by thread:'); 
for (same, m, ty), n in sorted(c.items()): print(f'   {same:13} {m:45} {ty or "":22} x{n}')
for d in items: print('   item:', json.dumps(d)[:420])
threads = sorted({(o.get('params') or {}).get('threadId') for t, o in recs if (o.get('params') or {}).get('threadId')}); print('thread ids seen:', len(threads), '(own is one of them:', th3 in threads, ')')
print('requests the tool sent to the client:', s.server_requests)
rl1 = s.req('account/rateLimits/read'); print('\nweekly window used after:', (((rl1 or {}).get('result') or {}).get('rateLimits') or {}).get('primary', {}).get('usedPercent'))
json.dump([[round(t, 2), o] for t, o in s.pr.out], open('codex-all.json', 'w'))
for t in (th, th2, th3):
    if t: s.req('thread/delete', {'threadId': t})
s.pr.close()
