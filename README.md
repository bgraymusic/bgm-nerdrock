## Prerequisites
* Python 3.13 installed (verify a successful response from `python3.13 --version` and `python3 --version`)

## CLI Install
* `pip install '.[cli]'`

## CLI Usage
### USAGE
  `bgnr [flags] <command> [options]`

### COMMANDS

__bootstrap__
: Set up AWS account with the ability to deploy CDK infrastructure

__clean__
: Remove build assets

__deploy__
: Deploy current code to the specified AWS environment

__global__
: Deploy the global stack by itself, without an environment stack

__help__
: Output this message if by itself, or get help for a command if followed by a command name

__package-lambdas__
: Build lambdas package into assets directory

__package-web__
: Build web package into assets directory

__rollback__
: Rollback to previous deployment by repointing the DNS domain record

__synth__
: Synthesize CloudFormation and output to the cdk.out directory

__test__
: Run all tests with coverage on current code

__undeploy__
: Destroy the specified AWS environment

__update-loc__
: Set your current IP as the allowed_ip for non-prod access

### FLAGS

__-t, --trace__
: Echo out the shell commands as they execute

__-v, --verbose__
: Allow sub-tasks to output their details

For help on a specific command, use: bgnr [flags] help <command>
