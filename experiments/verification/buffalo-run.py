import datetime
import os
from pathlib import Path
import shlex
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
env_root = root / 'experiments/envs/buffalo'
results = root / 'experiments/results/upstream-verification/buffalo'
name, cwd, *command = sys.argv[1:]
environment = os.environ.copy()
environment.update(
    TMPDIR=str(env_root / 'tmp'),
    XDG_CACHE_HOME=str(env_root / 'cache'),
    PIP_CACHE_DIR=str(env_root / 'pip-cache'),
    PYTHONDONTWRITEBYTECODE='1',
    OMP_NUM_THREADS='2',
    PATH=str(env_root / 'venv/bin') + ':' + str(root / 'experiments/tools/buffalo') + ':' + environment['PATH'],
)
with (results / (name + '.log')).open('w') as log:
    log.write(f'TIME: {datetime.datetime.now().isoformat()}\nCWD: {cwd}\nCOMMAND: {shlex.join(command)}\n')
    log.write('ENV: ' + repr({key: environment[key] for key in ['TMPDIR', 'XDG_CACHE_HOME', 'PIP_CACHE_DIR', 'PYTHONDONTWRITEBYTECODE', 'OMP_NUM_THREADS', 'PATH']}) + '\n')
    log.flush()
    result = subprocess.run(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT)
    log.write(f'\nEXIT_CODE: {result.returncode}\n')
print(f'{name}: exit={result.returncode}; {results / (name + ".log")}', flush=True)
sys.exit(result.returncode)
