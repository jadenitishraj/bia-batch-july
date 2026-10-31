"""Pause, resume or inspect only the instance in this demo's Terraform state."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    action = sys.argv[1]
    operations = {'pause': 'stop-instances', 'resume': 'start-instances', 'status': 'describe-instances'}
    if action not in operations:
        raise SystemExit('Choose pause, resume or status.')
    instance = subprocess.check_output(['terraform', f'-chdir={ROOT / "terraform"}',
                                        'output', '-raw', 'instance_id'], text=True).strip()
    response = subprocess.check_output(['aws', 'ec2', operations[action], '--instance-ids', instance,
                                        '--region', 'us-east-1', '--output', 'json', '--no-cli-pager'], text=True)
    json.loads(response)
    print(f'Demo {action} request completed. Paused instances still incur storage charges.')


if __name__ == '__main__':
    main()
