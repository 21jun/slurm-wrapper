import argparse
import subprocess
import sys
import tempfile
from datetime import datetime

SLURM_TEMPLATE = """#!/bin/bash
#SBATCH -j {job_name}
#SBATCH -o %x-%j.{job_name}.{date_str}.out
#SBATCH -p {partition}
{queue_line}
#SBATCH --gres=gpu:{num_gpus}
#SBATCH -t 72:00:00 # Run time (hh:mm:ss)
#SBATCH --nodes=1
#SBATCH --ntasks={ntasks}
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task={cpus_per_task}
{extra}

hostname
date
export OMP_NUM_THREADS={cpus_per_task}

{command}
"""

def check_update():
    import requests
    import subprocess
    import sys
    import os
    GITHUB_REPO = "21jun/slurm-wrapper"  # Change to your repo if needed
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = requests.get(API_URL, timeout=5)
        resp.raise_for_status()
        latest = resp.json()["tag_name"]
    except Exception as e:
        print(f"Could not check for updates: {e}")
        sys.exit(1)
    # Get current version from pyproject.toml
    import toml
    try:
        with open("pyproject.toml") as f:
            current = toml.load(f)["project"]["version"]
    except Exception:
        print("Could not determine current version.")
        sys.exit(1)
    if latest.lstrip('v') == current:
        print(f"You are already using the latest version: {current}")
        return
    print(f"Updating from {current} to {latest}...")
    # Pull and install latest from GitHub
    repo_url = f"git+https://github.com/{GITHUB_REPO}.git@{latest}"
    subprocess.run([sys.executable, "-m", "pip", "install", repo_url], check=True)
    print("Update complete.")
    sys.exit(0)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        check_update()

    parser = argparse.ArgumentParser(description="Slurm sbatch wrapper.")
    parser.add_argument('--num_gpus', type=int, default=1, help='Number of GPUs')
    parser.add_argument('--ntasks', type=int, default=1, help='Number of tasks')
    parser.add_argument('--cpus_per_task', type=int, default=16, help='CPUs per task')
    parser.add_argument('--job_name', type=str, default='job', help='Job name')
    parser.add_argument('--partition', '-p', type=str, default='A6000', help='Partition name')
    parser.add_argument('--extra', type=str, default='', help='Extra SBATCH lines')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run')
    args = parser.parse_args()

    # Scan for .sb file and use as command prefix if present
    prefix = ''
    try:
        with open('.sb', 'r') as f:
            prefix = f.read().strip()
    except FileNotFoundError:
        pass
    if prefix:
        prefix = prefix.replace('{num_gpus}', str(args.num_gpus))

    if args.partition == 'A100-80GB':
        queue_line = '#SBATCH -q hpgpu'
    elif args.partition == '4A100':
        queue_line = '#SBATCH -q 4A100'
    else:
        queue_line = ''

    if not args.command:
        print('Error: You must provide a command to run.')
        sys.exit(1)

    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Prepend prefix to command if present
    full_command = (prefix + ' ' if prefix else '') + ' '.join(args.command)

    script = SLURM_TEMPLATE.format(
        job_name=args.job_name,
        num_gpus=args.num_gpus,
        ntasks=args.ntasks,
        cpus_per_task=args.cpus_per_task,
        partition=args.partition,
        queue_line=queue_line,
        extra=args.extra,
        command=full_command,
        date_str=date_str
    )

    with tempfile.NamedTemporaryFile('w', suffix='.slurm', delete=False) as f:
        f.write(script)
        script_path = f.name

    print(f"Generated script: {script_path}")
    # subprocess.run(['sbatch', script_path])

if __name__ == '__main__':
    main()
