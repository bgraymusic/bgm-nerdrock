from colorama import Style, Fore
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import subprocess
from textwrap import fill
import yaml

from cli.bgnr_command import Command


class Config:
    __instance = None

    def __init__(self):
        with open(f'{Path(__file__).parent}/bgnr_config.yml') as config_file:
            config_contents = config_file.read()
            config: dict = yaml.load(config_contents, Loader=yaml.BaseLoader)
            for key, value in config.items():
                setattr(self, key, value)

    @classmethod
    def get(cls, force_new=False):
        if not Config.__instance or force_new:
            Config.__instance = Config()
        return Config.__instance

    def stack(self, name: str):
        return f'{self.org}-{self.project}-{name}-stack'


class Context:
    __instance = None

    @dataclass
    class Flag:
        names: list[str]
        action: str
        desc: str

    def __init__(self):
        self.trace: bool = False
        self.verbose: bool = False
        self.commands: dict[str, type[Command]] = Command.load_commands()
        self.command: str = None
        self.flags: list[Context.Flag] = []
        self.environment: str = None

    @classmethod
    def get(cls, force_new=False):
        if not Context.__instance or force_new:
            Context.__instance = Context()
        return Context.__instance

    def resolve_cmd_templates(self):
        for cmd in self.commands.values():
            cmd.__doc__ = Docstring.resolve_template(cmd.__doc__)


class Out:

    class Do:
        def __init__(self, msg: str, error: str = None, done: str = None):
            self.msg: str = msg
            self.error: str = error
            self.done: str = done

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
        return f'{Fore.GREEN}{msg}{Fore.RESET}'

    @staticmethod
    def failure(msg: str):
        return f'{Fore.RED}{msg}{Fore.RESET}'

    @staticmethod
    def bold(msg: str):
        return f'{Style.BRIGHT}{msg}{Style.NORMAL}'

    @staticmethod
    def dim(msg: str):
        return f'{Style.DIM}{msg}{Style.NORMAL}'

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
    def wrap(indent: int, text: str):
        return fill(text, os.get_terminal_size().columns - indent, subsequent_indent=' ' * indent)


class Proc:

    @staticmethod
    def exec(cmd: str, *, capture_stdout: bool = False, capture_stderr: bool = False):
        Out.trace(cmd)
        proc = subprocess.run(shlex.split(cmd), check=True,
                              stdout=subprocess.PIPE if capture_stdout or not Context().get().verbose else None,
                              stderr=subprocess.PIPE if capture_stderr or not Context().get().verbose else None)
        proc.stdout = proc.stdout.decode() if proc.stdout and proc.stdout.decode else proc.stdout
        proc.stderr = proc.stderr.decode() if proc.stderr and proc.stderr.decode else proc.stderr
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
