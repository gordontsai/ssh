import os
import importlib.util
import sys
sys.dont_write_bytecode = True

if sys.version_info < (3, 0):
  print("Python3 is required to run this script")
  exit(1)

TAB = "  "

executed_script_paths = []

def create_configuration(options, dirpath):
  print("Configuring '%s'" % dirpath)

  print_error = lambda v: print("%sError: No '%s' provided." % (TAB, v))
  print_warning = lambda m: print("%sWarning: %s" % (TAB, m))

  if 'script.py' in options:
    script_path = options['script.py']
    module = load_module('module', script_path)
    if not script_path in executed_script_paths:
      module.initialize()
      executed_script_paths.append(script_path)
    new_options = module.compute_options(options.copy(), print_error, print_warning, read_fileline)
    if new_options == None:
      return
    options = new_options

  for option in ['nickname', 'hostname', 'id_rsa']:
    if not option in options:
      print_error(option)
      return
  if not 'username' in options:
    print_warning("No 'username' provided. Setting to 'root'")
    options['username'] = 'root'

  nickname = options['nickname']
  username = options['username']
  hostname = options['hostname']
  key_path = options['id_rsa']

  configuration_title = "Host %s" % nickname
  configuration_details = {
    "Hostname":        hostname,
    "User":            username,
    "IdentityFile":    key_path,
    "IdentitiesOnly":  "Yes",
    "CheckHostIP":     "No"
  }

  if 'ssh_config' in options:
    ssh_config = options['ssh_config']
    for detail in ssh_config:
      configuration_details[detail] = ssh_config[detail]

  configuration_details = ["%s %s" % i for i in configuration_details.items()]
  return "%s\n%s" % (configuration_title, ("\n" + TAB).join(configuration_details))

def read_fileline(filepath):
  f = open(filepath)
  line = f.read().rstrip()
  f.close()

  if len(line) == 0:
    print("Fatal: '%s' is empty" % filepath)
    exit(1)
  return line

def load_module(module_name, module_path):
  spec = importlib.util.spec_from_file_location(module_name, module_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module

def parseGroup(path, options):
  def readOption(option, kind):
    option_path = os.path.join(path, option)
    if os.path.exists(option_path):
      if os.path.isfile(option_path):
        if kind == 'line':
          options[option] = read_fileline(option_path)
        elif kind == 'file':
          options[option] = option_path
      else:
        print("'%s' is a special filename: Has to be a file" % option)
        print("Path: %s" % path)
        return

  readOptionLine = lambda o: readOption(o, kind='line')
  readOptionFile = lambda o: readOption(o, kind='file')

  readOptionLine('username')
  readOptionLine('hostname')
  readOptionLine('nickname')
  readOptionFile('id_rsa')
  readOptionFile('script.py')

  configs = []

  dirs = []
  for filename in os.listdir(path):
    if filename[0] == "." or filename == "__pycache__":
      continue

    filepath = os.path.join(path, filename)
    if os.path.isdir(filepath):
      dirs.append(filepath)
    elif os.path.isfile(filepath) and not filename in options:
      readOptionFile(filename)

  if len(dirs) == 0:
    config = create_configuration(options, path)
    if config != None:
      configs.append(config)
  else:
    for group_path in dirs:
      configs += parseGroup(group_path, options.copy())

  return configs

base_path = os.path.expanduser('~/.ssh')
config_path = os.path.join(base_path, 'config')
ids_path = os.path.join(base_path, 'ids')

configs = parseGroup(ids_path, {})

with open(config_path, 'w') as f:
  write_text = "\n\n".join(configs)
  f.write(write_text)
