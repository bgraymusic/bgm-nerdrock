"""Base class and common errors for API handlers"""

from __future__ import annotations
from abc import ABC, abstractmethod
from http import HTTPMethod


class MethodDescription:
    def __init__(self, method: HTTPMethod, errors: list[type[BgnrError]]):
        self.method: HTTPMethod = method
        self.errors: list[type[BgnrError]] = errors or []


class ResourceDescription:
    def __init__(self, path: str, methods: list[MethodDescription]):
        self.path: str = path
        self.methods: list[MethodDescription] = methods or []


class HandlerDescription:
    def __init__(self, name: str, resources: list[ResourceDescription], keep_warm: bool = False) -> None:
        self.name: str = name
        self.resources: list[ResourceDescription] = resources
        self.keep_warm = keep_warm


class BgnrError(ABC, Exception):
    code = -1  # shouldn't ever be queried, because this is an abstract class

    def __init__(self, code: int, *args: object) -> None:
        super().__init__(*args)
        self.code = code

class InvalidTokenError(BgnrError):
    code = 401

    def __init__(self, badToken, goodToken, badges, discography=None):
        super().__init__(InvalidTokenError.code, {
            "error": self.__class__.__name__,
            "badges": badges,
            "bad_token": badToken,
            "token": goodToken,
            "discography": discography
        })


class InvalidKeyError(BgnrError):
    code = 403

    def __init__(self, badKey, token, badges):
        super().__init__(InvalidKeyError.code, {
            "error": self.__class__.__name__,
            "bad_key": badKey,
            "badges": badges,
            "token": token
        })


class InternalError(BgnrError):
    code = 500

    def __init__(self):
        super().__init__(InternalError.code, {
            "error": self.__class__.__name__
        })


class HandlerBase(ABC):
    @abstractmethod
    def handle(self, event, context) -> dict:
        pass

    @classmethod
    @abstractmethod
    def describe(cls) -> HandlerDescription:
        pass
