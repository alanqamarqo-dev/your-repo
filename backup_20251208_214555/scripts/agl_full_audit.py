#!/usr/bin/env python3
import os
import hashlib
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# patterns considered as backup/legacy files
BACKUP_SUFFIXES = ('.bak', '.orig', '.old', '.backup', '.diff', '.patch', '.bundle')
BACKUP_CONTAINS = ('~', 'copy', 'backup', 'bak', 'old', 'archive')

MANIFEST_PATH = PROJECT_ROOT / 'agi_full_audit_manifest.json'


def sha256_of_file(p: Path):
    h = hashlib.sha256()
    try:
        with p.open('rb') as fh:
            for chunk in iter(lambda: fh.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def run_git_command(args, cwd=PROJECT_ROOT):
    try:
        out = subprocess.check_output(['git'] + args, cwd=str(cwd), stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return None


def scan_repo():
    print(f"Starting full audit at: {PROJECT_ROOT}")

    total_files = 0
    total_dirs = 0
    missing_inits = []
    files_by_hash = {}
    backup_files = []
    largest = []  # list of (size, path)

    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        total_dirs += 1
        pdir = Path(dirpath)

        # examine python package visibility: if dir contains .py and no __init__.py
        py_files = [f for f in filenames if f.endswith('.py')]
        if py_files and '__init__.py' not in filenames:
            # ignore virtualenv directories that might have many py files (heuristic)
            if 'site-packages' not in str(pdir) and '.venv' not in str(pdir) and 'venv' not in str(pdir):
                try:
                    missing_inits.append(str(pdir.relative_to(PROJECT_ROOT)))
                except Exception:
                    missing_inits.append(str(pdir))

        for fn in filenames:
            total_files += 1
            fp = pdir / fn
            try:
                st = fp.stat()
                size = st.st_size
            except Exception:
                size = 0

            # detect backups
            low = fn.lower()
            if low.endswith(BACKUP_SUFFIXES) or any(token in low for token in BACKUP_CONTAINS) or fn.endswith('~'):
                try:
                    backup_files.append(str(fp.relative_to(PROJECT_ROOT)))
                except Exception:
                    backup_files.append(str(fp))

            # compute hash for duplicates (skip very large binary files >100MB for performance)
            if size < 100 * 1024 * 1024:
                h = sha256_of_file(fp)
            else:
                h = None
            if h:
                files_by_hash.setdefault(h, []).append(str(fp.relative_to(PROJECT_ROOT)))

            # track largest
            try:
                largest.append((size, str(fp.relative_to(PROJECT_ROOT))))
            except Exception:
                largest.append((size, str(fp)))

    # duplicates: hashes with more than 1 path
    duplicates = {h: paths for h, paths in files_by_hash.items() if len(paths) > 1}

    largest_sorted = sorted(largest, key=lambda x: x[0], reverse=True)[:25]

    # git branches and remotes
    git_branches = run_git_command(['branch', '--all']) or ''
    git_branches_list = [l.strip() for l in git_branches.splitlines() if l.strip()]
    git_remotes = run_git_command(['remote', '-v']) or ''

    # git commit count (rough)
    git_count = run_git_command(['rev-list', '--all', '--count'])

    report = {
        'project_root': str(PROJECT_ROOT),
        'total_files': total_files,
        'total_dirs': total_dirs,
        'missing_init_dirs': missing_inits,
        'missing_init_count': len(missing_inits),
        'backup_files': backup_files,
        'backup_count': len(backup_files),
        'duplicate_groups_count': len(duplicates),
        'duplicate_groups_sample': {k: v for i, (k, v) in enumerate(duplicates.items()) if i < 10},
        'largest_files': [{'size': s, 'path': p} for s, p in largest_sorted],
        'git_branches': git_branches_list,
        'git_remotes': git_remotes,
        'git_commit_count': int(git_count) if git_count and git_count.isdigit() else git_count,
    }

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print('\nAudit complete.')
    print(f"Files scanned: {total_files}")
    print(f"Dirs scanned: {total_dirs}")
    print(f"Missing __init__.py dirs: {len(missing_inits)}")
    print(f"Backup-like files found: {len(backup_files)}")
    print(f"Duplicate file groups: {len(duplicates)}")
    print(f"Top large files (count={len(largest_sorted)}):")
    for s, p in largest_sorted[:10]:
        print(f"  - {p} ({s} bytes)")
    if git_branches_list:
        print('\nGit branches (sample):')
        try:
            print('\n'.join(['  ' + b for b in git_branches_list[:50]]))
        except Exception:
            for b in git_branches_list[:50]:
                print('  ' + b)
    else:
        print('\nNo git branches found or not a git repo.')


if __name__ == '__main__':
    scan_repo()
