#!/usr/bin/env python3

__author__ = "Brian Gray"
__copyright__ = "Copyright 2024, Brian Gray"
__credits__ = ["Brian Gray"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Brian Gray"
__email__ = "bgraymusic@gmail.com"
__status__ = "Development"

import os, sys, subprocess
import boto3
from pathlib import Path
import json

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
      lastModSeconds = max(lastModSeconds, int(subprocess.check_output(f'git log -1 --format=%ct {fragmentPath}', shell=True)))
    localModules.append({'typeName': typeName, 'moduleDir': moduleDirPath, 'lastMod': lastModSeconds})
  return localModules

def getModulesToSubmit():
  registeredModules = collectRegisteredModules()
  modulesToSubmit = []
  for localModule in collectLocalModules():
    typeName, moduleDir, lastMod = localModule.values()
    if typeName in registeredModules:
      if lastMod > registeredModules[typeName]:
        print(f'Local module {typeName} ({lastMod}) is newer than AWS version ({registeredModules[typeName]}), updating…')
        modulesToSubmit.append(moduleDir)
      else:
        print(f'Registered module {typeName} is up to date.')
    else:
      print(f'Local module {typeName} is new, creating…')
      modulesToSubmit.append(moduleDir)
  jsonModuleList = json.dumps(modulesToSubmit)
  print(f'Adding {jsonModuleList} to env')
  with open(os.environ['GITHUB_OUTPUT'], 'a') as env:
    print(f'MODULES_TO_SUBMIT={jsonModuleList}', file=env)
  return modulesToSubmit

def submitModules(modulesToSubmit):
  moduleDirs = json.loads(modulesToSubmit)
  print(f'Submitting {len(moduleDirs)} modules…')
  for moduleDir in moduleDirs:
    cwd = os.getcwd()
    os.chdir(moduleDir)
    os.system('cfn generate')
    os.system('cfn submit --set-default')
    os.chdir(cwd)

if __name__ == '__main__':
    globals()[sys.argv[1]](*sys.argv[2:])
