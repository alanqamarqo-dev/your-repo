#!/usr/bin/env python3
"""
watch_and_train.py
Simple watcher that monitors `artifacts/harvested_facts.jsonl` for changes
and triggers a configurable set of training/automation commands.

Default behavior (no args): run a small set of repo scripts if they exist:
 - py scripts/calibrate_fusion_weights.py # type: ignore # type: ignore
 - py scripts/phase_g_save_patterns.py

It writes logs to `artifacts/auto_train.log` and rate-limits triggers.
"""
import os
import time
import subprocess
import argparse
import logging
import shlex

LOG_PATH = os.path.join('artifacts', 'auto_train.log')
DEFAULT_CMDS = [
    'py scripts/calibrate_fusion_weights.py',
    'py scripts/phase_g_save_patterns.py'
]


def setup_logger():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger('watch_and_train')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    # also echo to stdout
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def command_exists(cmd):
    # Heuristic: accept commands that invoke python or reference a .py file.
    lowered = cmd.lower().strip()
    # common forms: 'py ...', 'python ...', full path to python.exe, module invocations '-m module'
    if lowered.startswith('py ') or lowered.startswith('python ') or 'python.exe' in lowered or 'python3.exe' in lowered:
        return True
    if ' -m ' in lowered or lowered.startswith('-m '):
        return True
    parts = shlex.split(cmd)
    for p in parts:
        if p.endswith('.py'):
            # accept even if the exact path doesn't exist in this check; subprocess will report errors
            return True
    # Also accept commands that look like an absolute path invocation (e.g. "C:\...\python.exe \"path\to\script.py\"")
    # (handled above by 'python.exe' check) — otherwise be permissive and allow other commands to be attempted
    return True


def run_commands(cmds, logger):
    for cmd in cmds:
        try:
            logger.info('Running: %s', cmd)
            # run via shell for windows-friendly invocation (py ...)
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            logger.info('Exit %s', p.returncode)
            if p.stdout:
                logger.info('stdout:\n%s', p.stdout)
            if p.stderr:
                logger.warning('stderr:\n%s', p.stderr)
        except Exception as e:
            logger.exception('Failed running %s: %s', cmd, e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default=os.path.join('artifacts', 'harvested_facts.jsonl'))
    parser.add_argument('--interval', type=int, default=300, help='minimum seconds between triggers')
    parser.add_argument('--check-delay', type=int, default=2, help='seconds to wait after change before running')
    parser.add_argument('--cmds', help='semicolon-separated commands to run instead of defaults')
    parser.add_argument('--cmds-file', help='path to a file containing one command per line; overrides --cmds if present')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()

    logger = setup_logger()
    logger.info('watch_and_train starting; monitoring %s', args.file)

    if args.cmds_file:
        # If the file isn't present yet, wait a bit for the launcher to write it.
        max_wait = 10
        waited = 0
        while waited < max_wait and not os.path.exists(args.cmds_file):
            logger.info('Waiting for cmds-file to appear: %s (waited %ds)', args.cmds_file, waited)
            time.sleep(1)
            waited += 1
        if os.path.exists(args.cmds_file):
            with open(args.cmds_file, 'r', encoding='utf-8') as fh:
                cmds = [line.strip() for line in fh.readlines() if line.strip()]
        else:
            logger.warning('Specified --cmds-file does not exist after waiting: %s', args.cmds_file)
            cmds = DEFAULT_CMDS
    elif args.cmds:
        cmds = [c.strip() for c in args.cmds.split(';') if c.strip()]
    else:
        cmds = DEFAULT_CMDS

    # filter commands by existence when they look like local py scripts
    cmds = [c for c in cmds if command_exists(c)]
    if not cmds:
        logger.warning('No valid commands to run (checked defaults and --cmds). Will continue monitoring but no commands available.')
        # don't exit; keep monitoring in case commands-file appears later
        cmds = []

    last_mtime = None
    last_size = None
    last_run = 0

    try:
        while True:
            if os.path.exists(args.file):
                st = os.stat(args.file)
                mtime = st.st_mtime
                size = st.st_size
                if last_mtime is None:
                    last_mtime, last_size = mtime, size
                if (mtime != last_mtime) or (size != last_size):
                    now = time.time()
                    if now - last_run < args.interval:
                        logger.info('Change detected but within interval (%ds), skipping trigger', args.interval)
                    else:
                        logger.info('Change detected, waiting %ds to allow writer to finish', args.check_delay)
                        time.sleep(args.check_delay)
                        logger.info('Triggering training/automation commands')
                        run_commands(cmds, logger)
                        last_run = time.time()
                    last_mtime, last_size = mtime, size
                    if args.once:
                        logger.info('Once-mode: exiting after one trigger')
                        return
            else:
                logger.info('Waiting for file to exist: %s', args.file)
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info('watch_and_train interrupted; exiting')


if __name__ == '__main__':
    main()
