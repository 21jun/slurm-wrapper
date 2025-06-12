import argparse
import subprocess
import sys
import tempfile

SLURM_TEMPLATE = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={output}
#SBATCH --gres=gpu:{num_gpus}
#SBATCH --ntasks={ntasks}
#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --mem={mem}
{extra}
"""

def main():
    parser = argparse.ArgumentParser(description="Slurm sbatch wrapper.")
    parser.add_argument('--num_gpus', type=int, default=1, help='Number of GPUs')
    parser.add_argument('--ntasks', type=int, default=1, help='Number of tasks')
    parser.add_argument('--cpus_per_task', type=int, default=4, help='CPUs per task')
    parser.add_argument('--mem', type=str, default='16G', help='Memory per node')
    parser.add_argument('--job_name', type=str, default='job', help='Job name')
    parser.add_argument('--output', type=str, default='slurm-%j.out', help='Output file')
    parser.add_argument('--extra', type=str, default='', help='Extra SBATCH lines')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run')
    args = parser.parse_args()

    if not args.command:
        print('Error: You must provide a command to run.')
        sys.exit(1)

    script = SLURM_TEMPLATE.format(
        job_name=args.job_name,
        output=args.output,
        num_gpus=args.num_gpus,
        ntasks=args.ntasks,
        cpus_per_task=args.cpus_per_task,
        mem=args.mem,
        extra=args.extra,
        command=' '.join(args.command)
    )

    with tempfile.NamedTemporaryFile('w', suffix='.slurm', delete=False) as f:
        f.write(script)
        script_path = f.name

    print(f"Generated script: {script_path}")
    subprocess.run(['sbatch', script_path])

if __name__ == '__main__':
    main()
