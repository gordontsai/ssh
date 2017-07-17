import os
import boto3

instance_path = os.path.expanduser("~/.ec2_instances")

def initialize():
  open(instance_path, 'w').close()

def compute_options(options, print_error, print_warning, read_fileline):
  if not 'instance-id' in options:
    print_error('instance-id')
    return

  if not 'nickname' in options:
    print_error('nickname')
    return

  instance_id = read_fileline(options['instance-id'])
  nickname = options['nickname']

  ec2 = boto3.resource('ec2')
  instance = ec2.Instance(instance_id)

  with open(instance_path, 'a') as f:
    f.write('%s %s\n' % (nickname, instance_id))

  instance_state = instance.state['Name']
  if not instance_state == 'running':
    print_warning("Instance is not running. State: %s" % instance_state)

  options['ssh_config'] = {
    'HostKeyAlias': nickname
  }
  options['hostname'] = instance.public_ip_address
  return options
