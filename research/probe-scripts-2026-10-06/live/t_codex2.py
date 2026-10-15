import sys, json, signal
sys.path.insert(0, '../probe')
from common import *
src = open('t_codex.py').read(); exec(src.split("s = Session('main')")[0])
def alive(pattern):
    r = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True); return [int(x) for x in r.stdout.split()]
def boot(label):
    s = Session(label); s.req('initialize', {'clientInfo': {'name': 'arbol-codex-driver', 'version': '1.0.0'}}); s.pr.send({'method': 'initialized'}); return s
MODEL = 'gpt-6.1-sol'
def tstart(s, **extra):
    p = {'cwd': s.cwd, 'approvalPolicy': 'never', 'sandbox': 'danger-full-access', 'model': MODEL}; p.update(extra)
    r = s.req('thread/start', p); return ((r or {}).get('result') or {}).get('thread', {}).get('id'), r
def send_turn(s, th, text):
    s.n += 1; i = s.n
    s.pr.send({'id': i, 'method': 'turn/start', 'params': {'threadId': th, 'input': [{'type': 'text', 'text': text}], 'approvalPolicy': 'never', 'sandboxPolicy': {'type': 'dangerFullAccess'}, 'effort': 'low'}})
    r = s.pr.wait_for(is_id(i), 60); return ((r[1].get('result') or {}).get('turn') or {}).get('id') if r else None
def wait_done(s, th, limit=240):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        s.pump()
        for t, o in s.pr.out:
            if o.get('method') == 'turn/completed' and (o.get('params') or {}).get('threadId') == th: return o
        time.sleep(0.3)
def last_answer(s, th):
    a = [((o.get('params') or {}).get('item') or {}).get('text') for t, o in s.pr.out if o.get('method') == 'item/completed' and (o.get('params') or {}).get('threadId') == th and ((o.get('params') or {}).get('item') or {}).get('type') == 'agentMessage']
    return a[-1] if a else None

print('=== E: stop while a sub-agent works (codex)')
s = boot('stop'); th, _ = tstart(s)
turn_id = send_turn(s, th, "Start exactly one sub-agent with your tool for spawning agents. Its job: 'Run the shell command `sleep 45; echo late-result` and report what it printed.' Wait until it has finished, then reply with one line: MAIN-DONE followed by its report.")
sub = s.pr.wait_for(lambda o: o.get('method') == 'item/started' and (o.get('params') or {}).get('threadId') not in (None, th) and ((o.get('params') or {}).get('item') or {}).get('type') == 'commandExecution', 180)
time.sleep(1.5); mark = len(s.pr.out); before = alive('sleep 45'); t_int = time.monotonic() - s.pr.t0
r = s.req('turn/interrupt', {'threadId': th, 'turnId': turn_id}, 20)
time.sleep(8); s.pump(); after8 = alive('sleep 45')
print(f'sub-agent command seen: {bool(sub)}; sleep processes before the stop: {len(before)}; answer to turn/interrupt: {json.dumps((r or {}).get("result", (r or {}).get("error")))[:80]}; sleep processes 8 s later: {len(after8)}')
for t, o in s.pr.out[mark:]:
    m = o.get('method'); p = o.get('params') or {}
    if not m or m in ('item/agentMessage/delta', 'account/rateLimits/updated', 'thread/tokenUsage/updated', 'item/commandExecution/outputDelta'): continue
    who = 'run' if p.get('threadId') == th else ('sub' if p.get('threadId') else '   '); it = p.get('item') or {}
    print(f'   {t:6.1f} {who} {m}' + (f" [{it.get('type')}] " + json.dumps({k: it[k] for k in ('kind', 'tool', 'status', 'exitCode') if k in it}) if it else '') + (' status=' + str((p.get('turn') or {}).get('status')) if m == 'turn/completed' else '') + (' ' + json.dumps(p.get('status'))[:50] if m == 'thread/status/changed' else ''))
s.req('thread/delete', {'threadId': th}, 20); s.pr.close(); time.sleep(1)
left = alive('sleep 45'); print('after the process ended, sleep processes:', len(left))
for p in left:
    try: os.kill(p, signal.SIGKILL)
    except Exception: pass

print('=== F: a changed system prompt on a continued thread (codex)')
ASK = 'Do your instructions name a project code word? Reply with the code word only, or NONE.'
s = boot('sp1'); th, raw = tstart(s, developerInstructions='The project code word is ALPHA-1.')
send_turn(s, th, 'Reply with the single word READY.'); wait_done(s, th); a = last_answer(s, th); s.pr.close()
s = boot('sp2'); r = s.req('thread/resume', {'threadId': th, 'developerInstructions': 'The project code word is BETA-2.'}); ok = 'result' in (r or {})
send_turn(s, th, ASK); wait_done(s, th); b = last_answer(s, th); s.pr.close()
s = boot('sp3'); r2 = s.req('thread/resume', {'threadId': th}); send_turn(s, th, ASK); wait_done(s, th); c = last_answer(s, th)
print(f'  first run -> {a!r}; resume accepted with new instructions: {ok}; continued with BETA-2 -> {b!r}; continued with none -> {c!r}')
s.req('thread/delete', {'threadId': th}, 20); s.pr.close()

print('=== G: a command that detaches itself (codex)')
s = boot('bg'); th, _ = tstart(s); server = s.pr.p.pid
send_turn(s, th, "Run exactly this with your shell tool: `nohup sleep 66 >/dev/null 2>&1 & echo launched`. Then reply with the single word STARTED."); wait_done(s, th)
items = [((o.get('params') or {}).get('item') or {}) for t, o in s.pr.out if o.get('method') == 'item/completed' and ((o.get('params') or {}).get('item') or {}).get('type') == 'commandExecution']
pids = alive('sleep 66'); info = []
for p in pids:
    try: info.append({'pid': p, 'sid': os.getsid(p), 'pgid': os.getpgid(p), 'parent': int(subprocess.run(['ps', '-o', 'ppid=', '-p', str(p)], capture_output=True, text=True).stdout or 0)})
    except Exception as e: info.append({'pid': p, 'error': str(e)})
print('  app-server: pid', server, 'session', os.getsid(server), 'group', os.getpgid(server))
print('  command items:', [{k: it.get(k) for k in ('processId', 'status', 'exitCode')} for it in items])
print('  detached process while the app-server runs:', info, '| answer:', last_answer(s, th))
s.req('thread/delete', {'threadId': th}, 20); s.pr.close(); time.sleep(1)
after = alive('sleep 66'); print('  alive after the app-server ended:', after)
for p in after:
    try: os.kill(p, signal.SIGKILL)
    except Exception: pass
print('  cleaned up:', not alive('sleep 66'))
