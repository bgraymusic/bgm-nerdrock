from __future__ import annotations
from abc import abstractmethod
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import importlib
import inspect
from pathlib import Path
import re


class NotBootstrappedError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class NoGlobalStackError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Command:
    @dataclass
    class Dependencies:
        pip_features: list[str]
        prerequisites: list[type[Command]]

    @classmethod
    def load_commands(cls) -> dict[str, type[Command]]:
        cmd_dir = Path(f'{str(Path(__file__).parent)}/commands')
        commands: dict[str, type[Command]] = {}
        for file in [x for x in cmd_dir.iterdir() if x.name.endswith('.py')]:
            module = importlib.import_module(f'cli.commands.{file.stem}')
            classes = [x[1] for x in inspect.getmembers(module)
                       if inspect.isclass(x[1]) and issubclass(x[1], cls) and x[1] is not cls and x[1].key()]
            for command in classes:
                commands[command.key()] = command
        return commands

    @classmethod
    @abstractmethod
    def key(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        return cls.__doc__.split('\n')[0]

    @classmethod
    def dependencies(cls) -> Dependencies:
        return Command.Dependencies([], [])

    def parse_args(self, argv: list[str]) -> tuple[Namespace, list[str]]:
        return (Namespace(), argv)

    @abstractmethod
    def execute(self) -> None:
        pass


class EnvCommand(Command):

    def parse_args(self, argv: list[str]) -> tuple[Namespace, list[str]]:
        ns, argv = super().parse_args(argv)
        parser = ArgumentParser(usage=self.__class__.__doc__, add_help=False)
        parser.add_argument('-e', '--environment')
        parsed_ns, parsed_argv = parser.parse_known_args(argv)
        ns.environment = parsed_ns.environment or 'sandbox'
        ns.environment = self.normalize_env_name(ns.environment)
        return (ns, parsed_argv)

    def normalize_env_name(self, env: str) -> str:
        env = re.sub('[^A-Za-z0-9-]+', '-', env)
        env = re.sub('^[-]', '', env)
        env = re.sub('[-]$', '', env)
        return env
