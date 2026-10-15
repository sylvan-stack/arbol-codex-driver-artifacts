import sys, json
sys.path.insert(0, '../probe')
from common import *
exec(open('t_codex3.py').read().split("SUBJOB =")[0])
print('=== H: a command left running at the end of the reply (codex)')
s = boot('bgend'); th = tstart(s)
send_turn(s, th, "Start the command `sleep 40; echo bg-finished` with your shell tool so that it keeps running in the background, using the tool's own way of leaving a command running (do not use nohup or &). Do not wait for it. Reply at once with the single word STARTED.")
done = wait_done(s, th, 120); t_done = time.monotonic() - s.pr.t0; mark = len(s.pr.out)
print(f'  turn ended at {t_done:.1f} with status', ((done or {}).get('params') or {}).get('turn', {}).get('status'), '| command processes at that moment:', [(p['cmd'], p['ppid'], p['sid']) for p in procs('sleep 40')])
for t, o in s.pr.out[:mark]:
    it = (o.get('params') or {}).get('item') or {}
    if o.get('method') in ('item/started', 'item/completed') and it.get('type') not in ('reasoning', 'userMessage'): print(f"   {t:6.1f} {o['method']} [{it.get('type')}] " + json.dumps({k: (it[k] if not isinstance(it[k], str) else it[k][:90]) for k in ('command', 'status', 'exitCode', 'text', 'tool', 'processId') if k in it}))
for k in range(10):
    time.sleep(5); s.pump()
print('  50 s later: command processes', len(procs('sleep 40')), '| what arrived after the turn ended:')
show(s, th, mark)
for t, o in s.pr.out[mark:]:
    it = (o.get('params') or {}).get('item') or {}
    if o.get('method') == 'item/completed' and it.get('type') == 'commandExecution': print('   late command item:', json.dumps({k: str(it.get(k))[:80] for k in ('status', 'exitCode', 'aggregatedOutput')}))
print('  app-server:', own_exit(s)); time.sleep(1); print('  command processes after it ended:', len(procs('sleep 40')))
for p in procs('sleep 40'): os.kill(p['pid'], 9)
