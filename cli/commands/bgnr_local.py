'''Commands that operate locally'''

import argparse
import subprocess

from cli import bgnr_command
from cli import bgnr_util


class HelpCommand(bgnr_command.Command):
    '''Get general help, or help with specific commands

    **USAGE**
      bgnr help [CMD]

    **OPTIONS**
      A command can optionally be supplied to get help with using that command, or
      no command to get general help with the bgnr utility

    Available commands:
      {cmd_list}

    **EXAMPLES**
      $ bgnr help
      $ bgnr help update-loc
    '''

    @classmethod
    def key(cls):
        return 'help'

    @classmethod
    def description(cls):
        return 'Output this message if by itself, or get help for a command if followed by a command name'

    def parse_args(self, argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
        ns, argv = super().parse_args(argv)
        parser = argparse.ArgumentParser(usage=self.__class__.__doc__, add_help=False)
        parser.add_argument('help_cmd', nargs='?')
        parsed_ns, parsed_argv = parser.parse_known_args(argv)
        self.help_cmd = parsed_ns.help_cmd
        return (ns, parsed_argv)

    def execute(self):
        if self.help_cmd:
            try:
                print(bgnr_util.Context.get().commands[self.help_cmd].__doc__)
            except KeyError:
                print(self.__class__.__doc__)
        else:
            print(self.__class__.__doc__)


class TestCommand(bgnr_command.Command):
    '''Test the NerdRock API, including coverage

    **USAGE**
      bgnr [flags] test

    {flags}

    **EXAMPLES**
      $ bgnr test
      $ bgnr -c test
    '''

    @classmethod
    def key(cls):
        return 'test'

    @classmethod
    def description(cls):
        return 'Run all tests with coverage on current code'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(pip_features=['test'], prerequisites=[])

    def execute(self):
        bgnr_util.Out.trace('pytest')
        subprocess.run('pytest', check=False)  # Always output subprocess out regardless of verbose settings


class PackageLambdasCommand(bgnr_command.EnvCommand):
    '''Call out to make to build a lambdas package

    **USAGE**
      bgnr [flags] lambdas [options]

    **OPTIONS**
      -e, --environment  The name of the environment to build a package for.
                         Supplying 'prod' will literally result in 'prod'
                         being used as part of the package name.
                         [default == 'sandbox']

    {flags}

    **EXAMPLES**
      $ bgnr -t lambdas
      $ bgnr lambdas -e staging
      $ bgnr -v lambdas -e 'feature/guitar-tabs'
    '''

    @classmethod
    def key(cls):
        return 'package-lambdas'

    @classmethod
    def description(cls):
        return 'Build lambdas package into assets directory'

    def execute(self):
        with bgnr_util.Out.Do(msg='Packaging lambda directory', error='Failed to package lambda directory'):
            bgnr_util.Proc.exec(f'make lambdas ENV={bgnr_util.Context.get().environment}')


class PackageWebCommand(bgnr_command.EnvCommand):
    '''Call out to make to build a web package

    **USAGE**
      bgnr [flags] lambdas [options]

    **OPTIONS**
      -e, --environment  The name of the environment to build a package for.
                         Supplying 'prod' will literally result in 'prod'
                         being used as part of the package name.
                         [default == 'sandbox']

    {flags}

    **EXAMPLES**
      $ bgnr -t web
      $ bgnr web -e staging
      $ bgnr -v web -e 'feature/guitar-tabs'
    '''

    @classmethod
    def key(cls):
        return 'package-web'

    @classmethod
    def description(cls):
        return 'Build web package into assets directory'

    def execute(self):
        with bgnr_util.Out.Do(msg='Packaging web directory', error='Failed to package web directory'):
            bgnr_util.Proc.exec(f'make web ENV={bgnr_util.Context.get().environment}')


class CleanCommand(bgnr_command.Command):
    '''Call out to remove build artifacts via make

    **USAGE**
      bgnr clean
    '''

    @classmethod
    def key(cls):
        return 'clean'

    @classmethod
    def description(cls):
        return 'Remove build assets'

    def execute(self):
        with bgnr_util.Out.Do('Removing artifacts'):
            bgnr_util.Proc.exec('make clean')
