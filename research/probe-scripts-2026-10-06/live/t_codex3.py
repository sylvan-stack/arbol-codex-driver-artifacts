import sys, json, signal
sys.path.insert(0, '../probe')
from common import *
src = open('t_codex.py').read(); exec(src.split("s = Session('main')")[0])
def procs(pattern):
    r = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True); out = []
    for x in r.stdout.split():
        p = int(x)
        try:
            ps = subprocess.run(['ps', '-o', 'ppid=,command=', '-p', str(p)], capture_output=True, text=True).stdout.strip()
            out.append({'pid': p, 'sid': os.getsid(p), 'pgid': os.getpgid(p), 'ppid': int(ps.split()[0]), 'cmd': ' '.join(ps.split()[1:])[:60]})
        except Exception: pass
    return out
def boot(label):
    s = Session(label); s.req('initialize', {'clientInfo': {'name': 'arbol-codex-driver', 'version': '1.0.0'}}); s.pr.send({'method': 'initialized'}); return s
def tstart(s, **extra):
    p = {'cwd': s.cwd, 'approvalPolicy': 'never', 'sandbox': 'danger-full-access'}; p.update(extra)
    r = s.req('thread/start', p); return ((r or {}).get('result') or {}).get('thread', {}).get('id')
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
        time.sleep(0.2)
def show(s, th, mark):
    for t, o in s.pr.out[mark:]:
        m = o.get('method'); p = o.get('params') or {}
        if not m or m in ('item/agentMessage/delta', 'account/rateLimits/updated', 'thread/tokenUsage/updated', 'item/commandExecution/outputDelta', 'item/reasoning/summaryTextDelta', 'item/reasoning/summaryPartAdded'): continue
        who = 'run' if p.get('threadId') == th else ('sub' if p.get('threadId') else '   '); it = p.get('item') or {}
        print(f'   {t:6.1f} {who} {m}' + (f" [{it.get('type')}] " + json.dumps({k: it[k] for k in ('kind', 'tool', 'status', 'exitCode') if k in it}) if it else '') + (' status=' + str((p.get('turn') or {}).get('status')) if m == 'turn/completed' else '') + (' ' + json.dumps(p.get('status'))[:50] if m == 'thread/status/changed' else ''))
def own_exit(s, wait=10):
    try: s.pr.p.stdin.close()
    except Exception: pass
    try: s.pr.p.wait(wait); return f'ended by itself with exit {s.pr.p.returncode}'
    except Exception: return 'still running after closing its input'
SUBJOB = "Start exactly one sub-agent with your tool for spawning agents. Its job: 'Run the shell command `sleep 45; echo late-result` and report what it printed.' Wait until it has finished, then reply with one line: MAIN-DONE followed by its report."
def to_subcommand(s, th):
    turn_id = send_turn(s, th, SUBJOB)
    sub = s.pr.wait_for(lambda o: o.get('method') == 'item/started' and (o.get('params') or {}).get('threadId') not in (None, th) and ((o.get('params') or {}).get('item') or {}).get('type') == 'commandExecution', 180)
    sub_th = (sub[1]['params'] or {}).get('threadId') if sub else None
    sub_turn = next(((o['params'].get('turn') or {}).get('id') or o['params'].get('turnId') for t, o in s.pr.out if o.get('method') == 'turn/started' and (o.get('params') or {}).get('threadId') == sub_th), None)
    time.sleep(1.5); return turn_id, sub_th, sub_turn

print('=== E2: stop only the run, then watch the sub-agent')
s = boot('stop2'); th = tstart(s); turn_id, sub_th, sub_turn = to_subcommand(s, th); mark = len(s.pr.out)
print('  server pid/session:', s.pr.p.pid, os.getsid(s.pr.p.pid), '| command processes:', procs('sleep 45'), '| sub-agent turn id known:', bool(sub_turn))
s.req('turn/interrupt', {'threadId': th, 'turnId': turn_id}, 20)
for k in range(11):
    time.sleep(5); s.pump(); n = len(procs('sleep 45'))
    if k in (0, 3, 7, 10): print(f'  {5*(k+1)} s after the stop: {n} command processes')
show(s, th, mark)
print('  app-server:', own_exit(s)); time.sleep(1); print('  command processes after it ended:', len(procs('sleep 45')))

print('=== E3: stop the run and the sub-agent, then end the app-server by closing its input only')
s = boot('stop3'); th = tstart(s); turn_id, sub_th, sub_turn = to_subcommand(s, th); mark = len(s.pr.out)
r1 = s.req('turn/interrupt', {'threadId': th, 'turnId': turn_id}, 20); r2 = s.req('turn/interrupt', {'threadId': sub_th, 'turnId': sub_turn}, 20)
time.sleep(4); s.pump()
print('  answers:', json.dumps((r1 or {}).get('result', (r1 or {}).get('error')))[:80], '|', json.dumps((r2 or {}).get('result', (r2 or {}).get('error')))[:120], '| command processes 4 s later:', len(procs('sleep 45')))
show(s, th, mark); print('  app-server:', own_exit(s))

print('=== E4: end the app-server while a sub-agent command runs (close its input only)')
s = boot('stop4'); th = tstart(s); to_subcommand(s, th)
print('  before:', len(procs('sleep 45')), '| app-server:', own_exit(s)); time.sleep(1); left = procs('sleep 45'); print('  command processes after:', left)
if s.pr.p.poll() is None: os.killpg(s.pr.p.pid, 15); time.sleep(2); print('  after signal 15 to the group:', procs('sleep 45'))
for p in procs('sleep 45'): os.kill(p['pid'], 9)

print('=== G2: commands that detach themselves')
s = boot('bg2'); th = tstart(s)
import threading
seen = {}; stop = False
def sampler():
    while not stop:
        for pat in ('sleep 66', 'sleep 67'):
            for p in procs(pat):
                if 'sleep' in p['cmd'].split()[0]: seen.setdefault(pat, {}).setdefault(p['pid'], {'first': time.monotonic() - s.pr.t0, **p})['last'] = time.monotonic() - s.pr.t0
        time.sleep(0.05)
threading.Thread(target=sampler, daemon=True).start()
send_turn(s, th, "Run these two commands with your shell tool, each as a call of its own, exactly as written, then reply with the single word STARTED.\n1. `nohup sleep 66 >/dev/null 2>&1 & echo launched-1`\n2. `perl -MPOSIX -e 'fork and exit; POSIX::setsid(); close STDIN; close STDOUT; close STDERR; exec \"sleep\",\"67\"'; echo launched-2`")
wait_done(s, th); t_end = time.monotonic() - s.pr.t0; time.sleep(1)
for t, o in s.pr.out:
    it = (o.get('params') or {}).get('item') or {}
    if o.get('method') in ('item/started', 'item/completed') and it.get('type') == 'commandExecution': print(f"   {t:6.1f} {o['method']} pid={it.get('processId')} exit={it.get('exitCode')} {str(it.get('command'))[:70]!r}")
print('  turn ended at', round(t_end, 1), '| server pid/session:', s.pr.p.pid, os.getsid(s.pr.p.pid))
for pat, d in seen.items():
    for pid, v in d.items(): print(f"   {pat}: pid {pid} parent {v['ppid']} session {v['sid']} group {v['pgid']} first seen {v['first']:.1f} last seen {v['last']:.1f}")
print('  alive after the turn:', [(p['cmd'], p['ppid'], p['sid']) for pat in ('sleep 66', 'sleep 67') for p in procs(pat)])
print('  app-server:', own_exit(s)); time.sleep(1); stop = True
left = [p for pat in ('sleep 66', 'sleep 67') for p in procs(pat)]; print('  alive after the app-server ended:', [(p['cmd'], p['ppid'], p['sid']) for p in left])
for p in left: os.kill(p['pid'], 9)
