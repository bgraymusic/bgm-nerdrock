"""Utility classes supporting configration, context, printing, OS commands, and help"""

from __future__ import annotations
import colorama
import dataclasses
import os
from pathlib import Path
import re
import shlex
import subprocess
from textwrap import fill
import yaml

from cli.bgnr_command import Command


class Config(yaml.YAMLObject):
    """Object representation of the bgnr_config.yml file"""

    _instance = None
    yaml_tag = '!Config'

    def __init__(
        self, org: str, project: str, min_bootstrap_ver: int, cdk_bootstrap_stack: str, domain: str,
        ipv4_check: str, ipv6_check: str, allowed_ips_key: str, cf_hosted_zone: str, default_prod_color: str
    ) -> None:
        self.org = org
        self.project = project
        self.min_bootstrap_ver = min_bootstrap_ver
        self.cdk_bootstrap_stack = cdk_bootstrap_stack
        self.domain = domain
        self.ipv4_check = ipv4_check
        self.ipv6_check = ipv6_check
        self.allowed_ips_key = allowed_ips_key
        self.cf_hosted_zone = cf_hosted_zone
        self.default_prod_color = default_prod_color

    # def __init__(self):
    #     with open(f'{Path(__file__).parent}/bgnr_config.yml') as config_file:
    #         config_contents = config_file.read()
    #         config: dict = yaml.load(config_contents, Loader=yaml.BaseLoader)
    #         for key, value in config.items():
    #             setattr(self, key, value)

    @classmethod
    def get(cls, force_new=False) -> Config:
        if not Config._instance or force_new:
            with open(f'{Path(__file__).parent}/bgnr_config.yml', encoding='utf-8') as config_file:
                return yaml.safe_load(config_file.read())
        return Config._instance

    def capitalize(self, s: str):
        s = re.sub(r'[\W]', '', s)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)

    def stack(self, name: str):
        return f'{self.org}-{self.project}-{name}-stack'

    def to_logical(self, construct_id: str):
        return ''.join([self.capitalize(x) for x in construct_id.split('-')])


class Context:
    """Collection of data for commands to use while processing"""

    _instance = None

    @dataclasses.dataclass
    class Flag:
        names: list[str]
        action: str
        desc: str

    def __init__(self):
        self.trace: bool = False
        self.verbose: bool = False
        self.commands: dict[str, type[Command]] = Command.load_commands()
        self.command: str = ''
        self.flags: list[Context.Flag] = []
        self.environment: str = ''

    @classmethod
    def get(cls, force_new=False):
        if not Context._instance or force_new:
            Context._instance = Context()
        return Context._instance

    def resolve_cmd_templates(self):
        for cmd in self.commands.values():
            cmd.__doc__ = Docstring.resolve_template(cmd.__doc__ or '')


class Out:
    """Helper for outputting to the console with consistent formatting"""

    class Do:
        """Consistent tracing of shell command execution and results"""
        def __init__(self, msg: str, error: str | None = None, done: str | None = None):
            self.msg: str = msg
            self.error: str = error or ''
            self.done: str = done or ''

        def __enter__(self):
            Out.target(self.msg, True)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if exc_type:
                print(f'{Out.failure(self.error)}')
                if Context.get().verbose:
                    print(Out.failure(f'Cause: {exc_type}'))
                    print(Out.failure(traceback))
            else:
                print(Out.success(f'{self.done if self.done else 'done.'}'))

    @staticmethod
    def target(msg: str, cont: bool = False):
        cont = cont and not Context.get().trace
        print(f'{Out.bold(f'({Context.get().command})>')} {msg}', end='… ' if cont else '\n', flush=True)

    @staticmethod
    def trace(cmd: str):
        if Context.get().trace:
            print(f'  ({Context.get().command}.trace)> {Out.dim(cmd)}')

    @staticmethod
    def success(msg: str):
        return f'{colorama.Fore.GREEN}{msg}{colorama.Fore.RESET}'

    @staticmethod
    def failure(msg: str):
        return f'{colorama.Fore.RED}{msg}{colorama.Fore.RESET}'

    @staticmethod
    def bold(msg: str):
        return f'{colorama.Style.BRIGHT}{msg}{colorama.Style.NORMAL}'

    @staticmethod
    def dim(msg: str):
        return f'{colorama.Style.DIM}{msg}{colorama.Style.NORMAL}'

    @staticmethod
    def commands():
        '''Return a dictionary of all commands and short descriptions'''
        return ('**COMMANDS**\n'
                f'{Out.dictionary(2, [(cmd.key(), cmd.description()) for cmd in Context.get().commands.values()])}')

    @staticmethod
    def cmd_list():
        '''Return a newline-separated list of indented command names'''
        return '\n  '.join(sorted(Context.get().commands))

    @staticmethod
    def flags():
        '''return a dictionary of flags and descriptions'''
        return ('**FLAGS**\n'
                f'{Out.dictionary(2, [(', '.join(flag.names), flag.desc) for flag in Context.get().flags])}')

    # Create a neatly lined up term-definition table
    @staticmethod
    def dictionary(indent: int, key_value_list: list[tuple[str, str]]):
        max_term_len = len(max([x[0] for x in key_value_list], key=len))
        result = ''
        for term, definition in sorted(key_value_list, key=lambda x: x[0]):
            result += (f'{' ' * indent}{term}{':  ' if definition else ''}'
                       f'{' ' * (max_term_len - len(term))}{Out.wrap(indent + max_term_len + 3, definition)}\n')
        return result.rstrip()

    # Wrap a long string at word boundaries so it never goes past the edge of the terminal. Assumes that we start
    # pre-indented and so do not need to indent the first line.
    @staticmethod
    def wrap(indent: int, text: str):
        try:
            width = os.get_terminal_size().columns - indent
        except OSError:
            width = 78 - indent
        return fill(text, width, subsequent_indent=' ' * indent)


class Proc:
    """Execution of shell commands"""

    class Process():
        def __init__(self, returncode: int, stdout: str, stderr: str):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    @staticmethod
    def exec(cmd: str, *, capture_stdout: bool = False, capture_stderr: bool = False) -> subprocess.CompletedProcess:
        Out.trace(cmd)
        proc = subprocess.run(shlex.split(cmd), check=True, text=True,
                              stdout=subprocess.PIPE if capture_stdout or not Context().get().verbose else None,
                              stderr=subprocess.PIPE if capture_stderr or not Context().get().verbose else None)
        # proc.stdout = proc.stdout.decode() if proc.stdout and proc.stdout.decode else proc.stdout
        # proc.stderr = proc.stderr.decode() if proc.stderr and proc.stderr.decode else proc.stderr
        return proc


class Docstring:
    @staticmethod
    def resolve_template(template: str) -> str:
        if template:
            template = re.sub(r'{commands}', lambda m: Out.commands(), template)
            template = re.sub(r'{cmd_list}', lambda m: Out.cmd_list(), template)
            template = re.sub(r'{flags}', lambda m: Out.flags(), template)
            template = re.sub(r'\*\*.+?\*\*', lambda m: Out.bold(m.group(0)[2:-2]), template)
        return template
