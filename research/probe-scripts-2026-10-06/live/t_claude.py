import sys, json, collections
sys.path.insert(0, '../probe')
from common import *
CLAUDE = which('claude')
H = os.path.join(HOME, 'Library/Application Support/Arbol/drivers/arbol-claude-driver/subscriptions/test-anthropic/home')
ROOT = os.path.abspath('work-claude'); shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT)
ENV = clean_env(CLAUDE_CONFIG_DIR=H, CLAUDE_CODE_DISABLE_AUTO_MEMORY='1', BASH_DEFAULT_TIMEOUT_MS='300000', BASH_MAX_TIMEOUT_MS='1800000')
STD = [CLAUDE, '-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose', '--include-partial-messages',
       '--model', 'haiku', '--permission-mode', 'bypassPermissions', '--strict-mcp-config', '--no-session-persistence']
def user(text): return {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'text', 'text': text}]}}
def shape(o):
    t = o.get('type'); extra = ''
    if t == 'stream_event':
        e = o.get('event', {}); extra = e.get('type', '')
        if extra == 'content_block_start': extra += ':' + e.get('content_block', {}).get('type', '') + (':' + e['content_block'].get('name', '') if e.get('content_block', {}).get('type') == 'tool_use' else '')
        if extra == 'content_block_delta': extra += ':' + e.get('delta', {}).get('type', '')
    elif t in ('assistant', 'user'):
        c = o.get('message', {}).get('content'); 
        extra = ','.join((b.get('type', '?') + (':' + b.get('name', '') if b.get('type') == 'tool_use' else '')) for b in c) if isinstance(c, list) else 'text'
    elif t in ('system', 'result', 'control_request', 'control_response'):
        extra = str(o.get('subtype') or o.get('request', {}).get('subtype') or o.get('response', {}).get('subtype'))
    return t, extra
def run(label, extra_args, prompt, on_control=None, limit=240):
    cwd = os.path.join(ROOT, label); os.makedirs(cwd)
    pr = Proc(STD + extra_args, ENV, cwd); pr.send(user(prompt)); i = 0; res = None; end = time.monotonic() + limit
    while time.monotonic() < end:
        r = pr.wait_for(lambda o: o.get('type') in ('result', 'control_request'), max(1, end - time.monotonic()), start=i)
        if not r: break
        idx = next(k for k, (t, o) in enumerate(pr.out) if o is r[1]); i = idx + 1
        if r[1]['type'] == 'result': res = r[1]; break
        if on_control: on_control(pr, r[1])
    rc = pr.close(); return pr, res, rc

print('=== T1a: a sub-agent on claude (haiku, trusted mode)')
pr, res, rc = run('subagent', [], "Use the Task tool to start exactly one sub-agent with this job: 'Run the shell command `echo sub-agent-says-PLUM` and report exactly what it printed.' When the sub-agent has finished, reply with one line: MAIN-DONE followed by what the sub-agent reported.")
seq = [(shape(o), o.get('parent_tool_use_id')) for t, o in pr.out if not o.get('_eof')]
c = collections.Counter((s, 'child' if p else 'main') for s, p in seq)
print('records by kind (main = the agent itself, child = carries parent_tool_use_id):')
for (s, who), n in sorted(c.items(), key=lambda x: (x[0][1], x[0][0])): print(f'   {who:5} {s[0]:15} {s[1]:45} x{n}')
parents = {p for s, p in seq if p}
task_ids = [b.get('id') for t, o in pr.out if o.get('type') == 'assistant' and not o.get('parent_tool_use_id') for b in o.get('message', {}).get('content', []) if b.get('type') == 'tool_use']
task_names = [b.get('name') for t, o in pr.out if o.get('type') == 'assistant' and not o.get('parent_tool_use_id') for b in o.get('message', {}).get('content', []) if b.get('type') == 'tool_use']
print('tool calls of the main agent:', task_names, '| parent ids seen on child records equal a main tool call id:', parents <= set(task_ids), len(parents))
child_text = [b.get('text', '')[:60] for t, o in pr.out if o.get('type') == 'assistant' and o.get('parent_tool_use_id') for b in o.get('message', {}).get('content', []) if b.get('type') == 'text']
child_tools = [b.get('name') for t, o in pr.out if o.get('type') == 'assistant' and o.get('parent_tool_use_id') for b in o.get('message', {}).get('content', []) if b.get('type') == 'tool_use']
print('child text blocks:', child_text, '| child tool calls:', child_tools)
sysk = sorted({(o.get('subtype'), tuple(sorted(k for k in o.keys() if k not in ('type', 'subtype', 'session_id', 'uuid')))[:12]) for t, o in pr.out if o.get('type') == 'system' and o.get('subtype') not in ('init', 'status')})
print('other system records:', sysk)
tr = [o for t, o in pr.out if o.get('type') == 'user' and not o.get('parent_tool_use_id') and isinstance(o.get('message', {}).get('content'), list) and any(b.get('type') == 'tool_result' for b in o['message']['content'])]
if tr:
    b = [b for b in tr[0]['message']['content'] if b.get('type') == 'tool_result'][0]; cont = b.get('content')
    print('result of the Task call as the main agent got it: content is', type(cont).__name__, '| tool_use_result keys:', sorted((tr[0].get('tool_use_result') or {}).keys())[:14] if isinstance(tr[0].get('tool_use_result'), dict) else type(tr[0].get('tool_use_result')).__name__)
print('final:', None if not res else {k: res.get(k) for k in ('subtype', 'is_error', 'num_turns', 'total_cost_usd')}, '| answer:', None if not res else str(res.get('result'))[:120], '| exit', rc)

print('=== T3: a question from the agent on claude in the trusted mode')
asked = []
def answer(pr, req):
    r = req.get('request', {}); asked.append({k: (v if k != 'input' else '<input>') for k, v in r.items()}); inp = r.get('input') or {}
    if r.get('tool_name') == 'AskUserQuestion':
        qs = inp.get('questions') or []; ans = {q.get('question'): 'Pear' for q in qs}
        asked[-1]['question_keys'] = sorted(qs[0].keys()) if qs else None; asked[-1]['options'] = [o.get('label') for o in (qs[0].get('options') or [])] if qs else None
        resp = {'behavior': 'allow', 'updatedInput': dict(inp, answers=ans)}
    else: resp = {'behavior': 'allow'}
    pr.send({'type': 'control_response', 'response': {'subtype': 'success', 'request_id': req.get('request_id'), 'response': resp}})
pr, res, rc = run('question', ['--permission-prompt-tool', 'stdio'], "Before anything else, use the AskUserQuestion tool to ask me exactly one question, 'Which fruit?', with the two options 'Apple' and 'Pear'. After I have answered, run the shell command `echo answered` and then reply with one line: CHOSEN: followed by my choice.", on_control=answer)
init = next((o for t, o in pr.out if o.get('type') == 'system' and o.get('subtype') == 'init'), {})
print('mode reported:', init.get('permissionMode'), '| AskUserQuestion among the tools:', 'AskUserQuestion' in (init.get('tools') or []), '| tools:', len(init.get('tools') or []))
print('requests the tool sent:', json.dumps(asked)[:700])
calls = [b.get('name') for t, o in pr.out if o.get('type') == 'assistant' for b in o.get('message', {}).get('content', []) if b.get('type') == 'tool_use']
print('tool calls:', calls)
print('final:', None if not res else {k: res.get(k) for k in ('subtype', 'is_error', 'num_turns', 'total_cost_usd')}, '| answer:', None if not res else str(res.get('result'))[:120], '| exit', rc)
