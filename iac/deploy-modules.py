#!/usr/bin/env python3

__author__ = "Brian Gray"
__copyright__ = "Copyright 2024, Brian Gray"
__credits__ = ["Brian Gray"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Brian Gray"
__email__ = "bgraymusic@gmail.com"
__status__ = "Development"

import os
import subprocess
import boto3
from pathlib import Path
import json
from datetime import datetime

def collectRegisteredModules():
  cf = boto3.client('cloudformation')
  typeSummaries = cf.list_types(Visibility='PRIVATE', Type='MODULE')['TypeSummaries']
  return {module['TypeName']: module['LastUpdated'].timestamp() for module in typeSummaries}

def collectLocalModules():
  localModules = []
  for rpdkConfigPath in Path('.').rglob('.rpdk-config'):
    typeName = None
    with open(rpdkConfigPath) as configFile:
      typeName = json.load(configFile)['typeName']
    moduleDirPath = rpdkConfigPath.parent
    lastModSeconds = 0
    for fragmentPath in Path(moduleDirPath).rglob('fragments/*.yml'):
      print(f'git log -n 1 -- {fragmentPath}')
      os.system(f'git log -n 1 -- {fragmentPath}')
      lastModSeconds = max(lastModSeconds, int(subprocess.check_output(f'git log -1 --format=%ct {fragmentPath}', shell=True)))
    localModules.append({'typeName': typeName, 'moduleDir': moduleDirPath, 'lastMod': lastModSeconds})
  return localModules

def submitModule(moduleDirPath):
  cwd = os.getcwd()
  os.chdir(moduleDirPath)
  os.system('cfn generate')
  os.system('cfn submit --set-default')
  os.chdir(cwd)

registeredModules = collectRegisteredModules()
localModules = collectLocalModules()

for localModule in localModules:
  typeName, moduleDir, lastMod = localModule.values()
  if typeName in registeredModules:
    if lastMod > registeredModules[typeName]:
      print(f'Local module {typeName} ({lastMod}) is newer than AWS version ({registeredModules[typeName]}), updating…')
      submitModule(moduleDir)
    else:
      print(f'Local module {typeName} is up to date.')
  else:
    print(f'Local module {typeName} is new, creating…')
    submitModule(moduleDir)
