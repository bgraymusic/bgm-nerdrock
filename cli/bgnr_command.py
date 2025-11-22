"""Support for CLI commands: loader, base classes, exceptions"""

from __future__ import annotations
import abc
import argparse
import dataclasses
import importlib
import inspect
import pathlib
import re


class NotBootstrappedError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class NoGlobalStackError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Command:
    """Base class for all commands; handles class loading and sets up the interface"""

    @dataclasses.dataclass
    class Dependencies:
        pip_features: list[str]
        prerequisites: list[type[Command]]

    @classmethod
    def load_commands(cls) -> dict[str, type[Command]]:
        cmd_dir = pathlib.Path(f'{str(pathlib.Path(__file__).parent)}/commands')
        commands: dict[str, type[Command]] = {}
        for file in [x for x in cmd_dir.iterdir() if x.name.endswith('.py')]:
            module = importlib.import_module(f'cli.commands.{file.stem}')
            classes = [x[1] for x in inspect.getmembers(module)
                       if inspect.isclass(x[1]) and issubclass(x[1], cls) and x[1] is not cls and x[1].key()]
            for command in classes:
                commands[command.key()] = command
        return commands

    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def description(cls) -> str:
        if cls.__doc__ is None:
            return ''
        else:
            return cls.__doc__.split('\n', maxsplit=1)[0]

    @classmethod
    def dependencies(cls) -> Dependencies:
        return Command.Dependencies([], [])

    def parse_args(self, argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
        return (argparse.Namespace(), argv)

    @abc.abstractmethod
    def execute(self) -> None:
        pass


class EnvCommand(Command):
    """Base class for commands that take an '--environment' (-e) argument"""

    def parse_args(self, argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
        ns, argv = super().parse_args(argv)
        parser = argparse.ArgumentParser(usage=self.__class__.__doc__, add_help=False)
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
