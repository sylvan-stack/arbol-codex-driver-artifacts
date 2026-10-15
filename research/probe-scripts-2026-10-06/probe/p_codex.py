import sys; sys.path.insert(0, '.')
from common import *
CODEX = which('codex')
ROOT = os.path.abspath('work-codex'); shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT)
NEW = 'check_for_update_on_startup = false\nweb_search = "live"\n\n[analytics]\nenabled = false\n\n[features]\nmemories = false\n'
OLD = ('notify = []\nweb_search = "disabled"\ncheck_for_update_on_startup = false\n\n[analytics]\nenabled = false\n\n[mcp_servers]\n\n[features]\n' +
       ''.join(f'{k} = false\n' for k in 'plugins apps remote_plugin memories multi_agent multi_agent_v2 image_generation browser_use computer_use hooks shell_snapshot skill_search tool_suggest workspace_dependencies goals'.split()))
def mk(name, cfg, extra=''):
    d = os.path.join(ROOT, name); os.makedirs(d); open(os.path.join(d, 'config.toml'), 'w').write(cfg + extra); return d
def cwd_with(name, files):
    d = os.path.join(ROOT, name); os.makedirs(d, exist_ok=True)
    for f, t in files.items(): open(os.path.join(d, f), 'w').write(t)
    return d
def is_id(i): return lambda o: o.get('id') == i and ('result' in o or 'error' in o)
def run(home, cwd, more=()):
    pr = Proc([CODEX, 'app-server'], clean_env(CODEX_HOME=home), cwd)
    pr.send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'arbol-probe', 'version': '0.0.1'}}})
    a = pr.wait_for(is_id(1), 120); pr.send({'method': 'initialized'})
    pr.send({'id': 2, 'method': 'thread/start', 'params': {'cwd': cwd, 'ephemeral': True, 'approvalPolicy': 'never', 'sandbox': 'read-only'}})
    b = pr.wait_for(is_id(2), 120)
    out = {'t_init': round(a[0], 2) if a else None, 't_thread': round(b[0], 2) if b else None}
    if b and 'result' in b[1]: out['instructionSources'] = b[1]['result'].get('instructionSources')
    elif b: out['thread_error'] = b[1].get('error')
    n = 10
    for method, params in more:
        pr.send({'id': n, 'method': method, 'params': params}); r = pr.wait_for(is_id(n), 60); out[method] = (r[1].get('result', r[1].get('error')) if r else None); n += 1
    return pr, out
RULE = '# Project rules\n\nThe project code word is PAPAYA-3310.\n'
cwd_agents = cwd_with('cwd-agents', {'AGENTS.md': RULE}); cwd_claude = cwd_with('cwd-claude', {'CLAUDE.md': RULE}); cwd_empty = cwd_with('cwd-empty', {})
def size(d):
    return subprocess.run(['du', '-sh', d], capture_output=True, text=True).stdout.split()[0]
print('== start time without a login: spawn -> answer to initialize -> thread started (seconds)')
for label, cfg in (('nothing switched off', NEW), ('old switched-off configuration', OLD)):
    home = mk('home-' + label[:3], cfg)
    for n in range(4):
        pr, o = run(home, cwd_empty)
        if n == 0:
            time.sleep(25)   # give a first start time to fetch what it fetches
            notes = sorted({x.get('method') for t, x in pr.out if x.get('method')})
        pr.close()
        print(f'  {label} #{n+1}: initialize {o["t_init"]}, thread {o["t_thread"]}' + (f'; home is {size(home)} after 25 s; notifications seen: {notes}' if n == 0 else '') + (f'; error {o["thread_error"]}' if 'thread_error' in o else ''))
    if label.startswith('nothing'): home_new = home
print('== instruction files (home with nothing switched off)')
for label, cwd in (('folder with AGENTS.md', cwd_agents), ('folder with only CLAUDE.md', cwd_claude), ('empty folder', cwd_empty)):
    pr, o = run(home_new, cwd); pr.close(); print(f'  {label}: instructionSources = {o.get("instructionSources")}')
print('== skills by link and an MCP server in the configuration')
home = mk('home-skills', NEW, '\n[mcp_servers.probe-server]\ncommand = "/usr/bin/true"\nargs = []\n')
sk = os.path.join(ROOT, 'owner-skills', 'probe-skill'); os.makedirs(sk)
open(os.path.join(sk, 'SKILL.md'), 'w').write('---\nname: probe-skill\ndescription: Probe skill for discovery tests. Use when asked for the probe word.\n---\nThe probe word is BANANA.\n')
os.symlink(os.path.join(ROOT, 'owner-skills'), os.path.join(home, 'skills'))
pr, o = run(home, cwd_empty, more=(('skills/list', {'cwds': [cwd_empty], 'forceReload': True}), ('mcpServerStatus/list', {})))
time.sleep(3)
sl = o.get('skills/list'); names = []
for e in (sl or {}).get('data', []) if isinstance(sl, dict) else []:
    for s in e.get('skills', []): names.append((s.get('name'), s.get('scope')))
print('  skills/list:', len(names), 'skills; probe-skill listed:', [x for x in names if x[0] == 'probe-skill'], '; scopes:', sorted({x[1] for x in names}))
ms = o.get('mcpServerStatus/list'); print('  mcpServerStatus/list:', json.dumps(ms)[:500])
print('  startup notifications:', [(x.get('params') or {}) for t, x in pr.out if x.get('method') == 'mcpServer/startupStatus/updated'][:6])
pr.close()
