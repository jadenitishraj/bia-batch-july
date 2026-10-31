"""Install the uploaded backend on our demo instance through AWS Systems Manager."""
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


def aws(*args):
    output = subprocess.check_output(['aws', *args, '--region', 'us-east-1',
                                      '--output', 'json', '--no-cli-pager'], text=True)
    return json.loads(output)


def main():
    outputs = json.loads(Path(sys.argv[1]).read_text())
    instance = outputs['instance_id']['value']
    bucket = outputs['code_bucket']['value']
    settings = ('AWS_REGION=us-east-1\nCHAT_MODEL=us.amazon.nova-2-lite-v1:0\n'
                + 'PUBLIC_ORIGIN=' + outputs['website_url']['value'] + '\n')
    commands = ['set -eu', 'cd /opt/travel-demo/backend',
                f'aws s3 cp s3://{bucket}/backend.tar.gz /tmp/backend.tar.gz --region us-east-1',
                'tar -xzf /tmp/backend.tar.gz -C /opt/travel-demo/backend',
                '/opt/travel-demo/venv/bin/pip install -r requirements.txt',
                'printf %s ' + shlex.quote(settings) + ' > /opt/travel-demo/backend/.env',
                'chown -R travel-demo:travel-demo /opt/travel-demo/backend',
                'systemctl restart travel-demo', 'systemctl is-active travel-demo nginx']
    response = aws('ssm', 'send-command', '--instance-ids', instance,
                   '--document-name', 'AWS-RunShellScript', '--parameters',
                   json.dumps({'commands': commands}))
    command = response['Command']['CommandId']
    for _ in range(90):
        response = aws('ssm', 'list-command-invocations', '--command-id', command, '--details')
        invocations = response['CommandInvocations']
        if invocations:
            status = invocations[0]['Status']
            if status == 'Success':
                print('Backend update completed.')
                return
            if status in ('Failed', 'Cancelled', 'TimedOut'):
                raise SystemExit('Backend update failed. Inspect the SSM command output.')
        time.sleep(3)
    raise SystemExit('Backend update is still pending; inspect Systems Manager before retrying.')


if __name__ == '__main__':
    main()
