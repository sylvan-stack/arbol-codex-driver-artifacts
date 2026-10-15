import os, json, time, subprocess, threading, shutil, tempfile, sys
HOME = os.path.expanduser('~')
PATH = f'{HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
def clean_env(**extra):
    e = {'HOME': HOME, 'USER': os.environ.get('USER', os.path.basename(HOME)), 'LOGNAME': os.environ.get('USER', os.path.basename(HOME)),
         'TMPDIR': os.environ.get('TMPDIR', '/tmp'), 'LANG': 'en_US.UTF-8', 'PATH': PATH}
    e.update(extra); return e
def which(name): return shutil.which(name, path=PATH)
class Proc:
    """A child that speaks JSON lines; every received object is stamped with seconds since spawn."""
    def __init__(self, argv, env, cwd):
        self.t0 = time.monotonic()
        self.p = subprocess.Popen(argv, env=env, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self.out = []; self.err = []; self.lock = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._readerr, daemon=True).start()
    def _read(self):
        for line in self.p.stdout:
            t = time.monotonic() - self.t0
            try: o = json.loads(line)
            except Exception: o = {'_raw': line.decode('utf-8', 'replace')[:200]}
            with self.lock: self.out.append((t, o)); self.lock.notify_all()
        with self.lock: self.out.append((time.monotonic() - self.t0, {'_eof': True})); self.lock.notify_all()
    def _readerr(self):
        for line in self.p.stderr: self.err.append(line.decode('utf-8', 'replace'))
    def send(self, obj):
        self.p.stdin.write((json.dumps(obj) + '\n').encode()); self.p.stdin.flush()
    def wait_for(self, pred, timeout=60, start=0):
        end = time.monotonic() + timeout; i = start
        with self.lock:
            while True:
                while i < len(self.out):
                    t, o = self.out[i]; i += 1
                    if o.get('_eof'): return None
                    if pred(o): return (t, o)
                left = end - time.monotonic()
                if left <= 0: return None
                self.lock.wait(left)
    def close(self, grace=5):
        try: self.p.stdin.close()
        except Exception: pass
        try: self.p.wait(grace)
        except Exception:
            try: os.killpg(self.p.pid, 15)
            except Exception: pass
            try: self.p.wait(3)
            except Exception:
                try: os.killpg(self.p.pid, 9)
                except Exception: pass
        return self.p.returncode
