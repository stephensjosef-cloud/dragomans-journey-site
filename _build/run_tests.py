"""Run every section of test_new.py in parallel, and print each one as it finishes (T-31, Nov 19, 2026).

    python _build/run_tests.py                    every section, on CPU cores minus one workers (at most 6)
    python _build/run_tests.py --only T-30,T-29   just those sections
    python _build/run_tests.py --jobs 1           one worker, the sections in the file's order (serial)
    python _build/run_tests.py --list             the section ids, with each one's time from the last run

It builds nothing: build _build/out/ first (the steps in _build/README.md). It serves _build/out/ on a free port,
starts the workers (each its own python running test_new.py --worker, with its own browser and its own port for
T-21's temp server), hands each the next section, longest first by the last run's times, and collects every check.
A section's line prints when it finishes, and a failing check the moment it fails. At the end: "<passed>/<total>
passed in <m> min <s> s (<N> workers)" and every failure. The full result, every check in the serial order, goes to
dj-test-results.json in the system temp folder; the section times to dj-test-times.json beside it.
"""
import argparse, json, os, queue, re, socket, subprocess, sys, tempfile, threading, time
from urllib.request import urlopen

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(HERE, 'test_new.py')
OUT = os.path.join(HERE, 'out')
TMP = tempfile.gettempdir()
TIMES = os.path.join(TMP, 'dj-test-times.json')
RESULTS = os.path.join(TMP, 'dj-test-results.json')
SHOTS = os.path.join(TMP, 'dj-test-shots')
MARK = '\x1eDJ '


def sections():
    """The section ids in the file's order, with each one's length in lines (a first guess at its time)."""
    src = open(TEST, encoding='utf-8').read()
    found = [(m.group(1), m.start()) for m in re.finditer(r"^@section\('([^']+)'\)$", src, re.M)]
    ends = [s for _i, s in found[1:]] + [src.index('# ================================================================ running the sections')]
    return [(sid, src.count('\n', a, e)) for (sid, a), e in zip(found, ends)]


def load_times():
    try:
        return json.load(open(TIMES, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def fmt(secs):
    return f'{int(secs // 60)} min {int(secs % 60)} s'


def serve(port):
    """_build/out/ on its own python -m http.server, as the serial runs serve it (one in this process ran out of memory
    under six workers on Windows and stalled a section)."""
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=OUT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _i in range(100):
        try:
            urlopen(f'http://127.0.0.1:{port}/index.html', timeout=2).read()
            return srv
        except OSError:
            if srv.poll() is not None:
                break
            time.sleep(0.1)
    srv.kill()
    sys.exit(f'the page server on port {port} did not start')


class Worker:
    def __init__(self, wid, base, events):
        self.wid, self.cur, self.alive = wid, None, True
        self.proc = subprocess.Popen([sys.executable, TEST, base, SHOTS, '--worker'], cwd=os.path.dirname(HERE),
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)
        threading.Thread(target=self.read, args=(events,), daemon=True).start()

    def read(self, events):
        for line in self.proc.stdout:
            if line.startswith(MARK):
                events.put((self, json.loads(line[len(MARK):])))
            else:
                sys.stderr.write(f'[worker {self.wid}] {line}')
        events.put((self, {'t': 'eof'}))

    def give(self, sid):
        self.cur = sid
        try:
            self.proc.stdin.write((sid or 'END') + '\n')
            self.proc.stdin.flush()
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description='Run test_new.py in parallel, section by section.')
    ap.add_argument('--jobs', type=int, default=max(1, min(6, (os.cpu_count() or 2) - 1)), help='worker processes (1 runs serially)')
    ap.add_argument('--only', help='comma-separated section ids, e.g. T-30,T-29')
    ap.add_argument('--list', action='store_true', help='print the section ids with their times from the last run')
    a = ap.parse_args()
    secs = sections()
    ids = [sid for sid, _n in secs]
    times = load_times()
    if a.list:
        for sid, _n in secs:
            t = times.get(sid)
            print(f'{sid:<22} ' + (f'{t:>7.1f} s' if t is not None else '      -'))
        return 0
    if a.only:
        want = [x.strip().lower() for x in a.only.split(',') if x.strip()]
        unknown = [x for x in want if x not in [i.lower() for i in ids]]
        if unknown:
            print(f'unknown section id(s): {", ".join(unknown)}. The ids: {", ".join(ids)}', file=sys.stderr)
            return 2
        ids = [i for i in ids if i.lower() in want]
    if not os.path.exists(os.path.join(OUT, 'index.html')):
        print('_build/out/ has no index.html: build it first (the steps in _build/README.md)', file=sys.stderr)
        return 2
    jobs = max(1, min(a.jobs, len(ids)))
    size = dict(secs)
    # Longest first, by the last run's times (a section with none yet goes by its length), so the slowest starts at once.
    # One worker keeps the file's order.
    todo = list(ids) if jobs == 1 else sorted(ids, key=lambda s: -(times[s] if s in times else 1000 + size[s]))

    os.makedirs(SHOTS, exist_ok=True)
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    srv = serve(port)
    base = f'http://127.0.0.1:{port}/'
    print(f'serving _build/out/ at {base}, {len(ids)} sections on {jobs} worker{"s" if jobs > 1 else ""}')

    t0 = time.time()
    events = queue.Queue()
    workers = [Worker(i + 1, base, events) for i in range(jobs)]
    checks = {sid: [] for sid in ids}
    done, errors, fonts_said, spawned = {}, [], False, jobs
    for w in workers:
        w.give(todo.pop(0) if todo else None)
    try:
        while any(w.alive for w in workers):
            w, ev = events.get()
            t = ev['t']
            if t == 'hello' and not fonts_said:
                print(ev['fonts']); fonts_said = True
            elif t == 'check':
                checks[ev['section']].append({k: ev[k] for k in ('section', 'name', 'passed', 'detail')})
                if not ev['passed']:
                    print(f'FAIL {ev["name"]}  {ev["detail"]}')
            elif t == 'done':
                done[ev['section']] = ev
                print(ev['line'])
                w.give(todo.pop(0) if todo else None)
            elif t == 'end':
                errors += ev['errors']
            elif t == 'eof':
                w.alive = False
                w.proc.wait()
                if w.cur and w.cur not in done:   # the worker stopped mid-section
                    sid = w.cur
                    rec = {'section': sid, 'name': f'{sid}: the section runs to the end', 'passed': False,
                           'detail': f'worker {w.wid} stopped (exit code {w.proc.returncode})'}
                    checks[sid].append(rec)
                    print(f'FAIL {rec["name"]}  {rec["detail"]}')
                    done[sid] = {'section': sid, 'checks': len(checks[sid]), 'failed': sum(not c['passed'] for c in checks[sid]), 'seconds': None}
                    if todo and spawned < 3 * jobs:   # keep the rest going on a fresh worker
                        spawned += 1
                        nw = Worker(spawned, base, events)
                        workers.append(nw)
                        nw.give(todo.pop(0))
    finally:
        for w in workers:
            if w.proc.poll() is None:
                w.proc.kill()
        srv.kill()
        srv.wait()
    secs = time.time() - t0

    for sid in todo:   # never started: every worker stopped
        checks[sid].append({'section': sid, 'name': f'{sid}: the section runs to the end', 'passed': False, 'detail': 'never started: no worker left'})
    every = [c for sid in ids for c in checks[sid]]   # the serial order: sections as in the file, checks as each made them
    pe = {'section': None, 'name': 'no page errors', 'passed': not errors, 'detail': '' if not errors else '; '.join(errors[:3])}
    every.append(pe)
    if not pe['passed']:
        print(f'FAIL no page errors  {pe["detail"]}')
    passed = sum(c['passed'] for c in every)

    times.update({sid: d['seconds'] for sid, d in done.items() if d.get('seconds') is not None})
    json.dump(times, open(TIMES, 'w', encoding='utf-8'), indent=1)
    json.dump({'base': base, 'workers': jobs, 'seconds': round(secs, 1), 'passed': passed, 'total': len(every),
               'sections': [{'id': sid, 'checks': len(checks[sid]), 'failed': sum(not c['passed'] for c in checks[sid]),
                             'seconds': done.get(sid, {}).get('seconds')} for sid in ids],
               'checks': every}, open(RESULTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

    print(f'{passed}/{len(every)} passed in {fmt(secs)} ({jobs} worker{"s" if jobs > 1 else ""})')
    for c in every:
        if not c['passed']:
            print(f'FAIL {c["name"]}  {c["detail"]}')
    print(f'results: {RESULTS}')
    return 0 if passed == len(every) else 1


if __name__ == '__main__':
    sys.exit(main())
