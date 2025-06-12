import subprocess
import sys
import os
import tempfile
import re
from pathlib import Path

def run_sb_command(args):
    """Run the sb CLI with given arguments and return the generated script path and its content."""
    result = subprocess.run(
        [sys.executable, 'slurm_wrapper.py'] + args,
        capture_output=True,
        text=True
    )
    # Find the generated script path in stdout
    match = re.search(r"Generated script: (.+\.slurm)", result.stdout)
    assert match, f"Script path not found in output: {result.stdout}"
    script_path = match.group(1)
    with open(script_path) as f:
        content = f.read()
    os.remove(script_path)
    return result, content

def test_basic_script():
    result, content = run_sb_command([
        '--num_gpus', '2', '--ntasks', '3', '--cpus_per_task', '8', '--job_name', 'testjob',
        '--partition', 'A6000', 'echo', 'hello']
    )
    assert '#SBATCH -j testjob' in content
    assert '#SBATCH --gres=gpu:2' in content
    assert '#SBATCH --ntasks=3' in content
    assert '#SBATCH --cpus-per-task=8' in content
    assert '#SBATCH -p A6000' in content
    assert 'echo hello' in content
    assert 'export OMP_NUM_THREADS=8' in content
    assert result.returncode == 0

def test_partition_queue():
    # A100-80GB triggers hpgpu queue
    _, content = run_sb_command([
        '--partition', 'A100-80GB', 'echo', 'hi']
    )
    assert '#SBATCH -q hpgpu' in content
    # 4A100 triggers 4A100 queue
    _, content = run_sb_command([
        '--partition', '4A100', 'echo', 'hi']
    )
    assert '#SBATCH -q 4A100' in content
    # Other partition does not trigger queue
    _, content = run_sb_command([
        '--partition', 'A6000', 'echo', 'hi']
    )
    assert '#SBATCH -q' not in content

def test_output_filename_has_date():
    _, content = run_sb_command(['echo', 'hi'])
    assert re.search(r'#SBATCH -o %x-%j\.job\.\d{8}_\d{6}\.out', content)

def test_error_on_no_command():
    result = subprocess.run(
        [sys.executable, 'slurm_wrapper.py'],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert 'You must provide a command to run.' in result.stdout or result.stderr

if __name__ == '__main__':
    test_basic_script()
    test_partition_queue()
    test_output_filename_has_date()
    test_error_on_no_command()
    print('All tests passed!')
