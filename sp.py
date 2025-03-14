#!/usr/bin/env python3

import subprocess


# result: subprocess.CompletedProcess = \
#     subprocess.run(['cdk', 'synth', '-c', 'ENV=sandbox'], check=True, text=True, stdout=subprocess.PIPE)
result: subprocess.CompletedProcess = \
    subprocess.run('cdk synth -c ENV=sandbox', shell=True, check=True)
print(vars(result))
