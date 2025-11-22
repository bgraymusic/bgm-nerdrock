"""Control configuration, build, and deployment of the NerdRock web site

**USAGE**
  bgnr [flags] <command> [options]

{commands}

{flags}

For help on a specific command, use: bgnr [flags] help <command>
"""

import argparse
import sys

from cli import bgnr_util, bgnr_command


class CLI:
    """Control configuration, build, and deployment of the NerdRock web site"""

    def __init__(self, argv: list[str] | None = None):
        self.argv = argv or sys.argv[1:]
        args = self._parse_global_args(self.argv)
        for key, value in vars(args).items():
            setattr(bgnr_util.Context.get(), key, value)
        self._set_command(args.command)

    def execute(self):
        cmd_class = bgnr_util.Context.get().commands[self.command]
        dependencies = self._get_dependencies(cmd_class)
        dependencies.pip_features = list(dict.fromkeys(dependencies.pip_features))
        dependencies.prerequisites = list(dict.fromkeys(dependencies.prerequisites))
        if dependencies.pip_features:
            with bgnr_util.Out.Do('Upgrading pip'):
                bgnr_util.Proc.exec('pip install --upgrade pip')
            with bgnr_util.Out.Do(f'Installing dependencies for features: {dependencies.pip_features}'):
                bgnr_util.Proc.exec(f'pip install \'.{dependencies.pip_features}\'')
            if 'cdk' in dependencies.pip_features:
                with bgnr_util.Out.Do('Updating aws-cdk'):
                    bgnr_util.Proc.exec('npm install -g aws-cdk')

        cmd: bgnr_command.Command = cmd_class()
        ns, _ = cmd.parse_args(self.cmd_argv[1:])
        for key, value in vars(ns).items():
            setattr(bgnr_util.Context.get(), key, value)
        for prerequisite in dependencies.prerequisites:
            prerequisite().execute()
        cmd.execute()

    @staticmethod
    def flags() -> list[bgnr_util.Context.Flag]:
        return [
            bgnr_util.Context.Flag(['-t', '--trace'], 'store_true', 'Echo out the shell commands as they execute'),
            bgnr_util.Context.Flag(['-v', '--verbose'], 'store_true', 'Allow sub-tasks to output their details')
        ]

    def _parse_global_args(self, argv: list[str] | None = None) -> argparse.Namespace:
        global_parser = argparse.ArgumentParser(prog='bgnr', usage=__doc__, add_help=False)
        for flag in bgnr_util.Context.get().flags:
            global_parser.add_argument(*flag.names, action=flag.action)
        global_parser.add_argument('command', choices=bgnr_util.Context.get().commands.keys())
        return global_parser.parse_known_args(argv)[0]

    def _set_command(self, command):
        self.command = command
        self.cmd_argv = self.argv[self.argv.index(self.command):]

    def _get_dependencies(self, cmd_class: type[bgnr_command.Command]) -> bgnr_command.Command.Dependencies:
        local_deps = cmd_class.dependencies()
        for dep_class in reversed(local_deps.prerequisites.copy()):
            dep_deps = self._get_dependencies(dep_class)
            local_deps.pip_features = [*dep_deps.pip_features, *local_deps.pip_features]
            local_deps.prerequisites = [*dep_deps.prerequisites, *local_deps.prerequisites]
        return local_deps


bgnr_util.Context.get().flags = CLI.flags()
__doc__ = bgnr_util.Docstring.resolve_template(__doc__ or '')
bgnr_util.Context.get().resolve_cmd_templates()


def cli():
    CLI().execute()


if __name__ == '__main__':
    cli()
