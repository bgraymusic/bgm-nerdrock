from abc import ABC, abstractmethod
from typing import List
from http import HTTPMethod


class MethodDescription:
    def __init__(self, method: HTTPMethod, errors: List[Exception] = []):
        self.method: HTTPMethod = method
        self.errors: List[Exception] = errors


class ResourceDescription:
    def __init__(self, path: str, methods: List[MethodDescription] = []):
        self.path: str = path
        self.methods: List[MethodDescription] = methods


class HandlerDescription:
    def __init__(self, name: str, resources: List[ResourceDescription] = [], errors: List[Exception] = []):
        self.name: str = name
        self.resources: List[ResourceDescription] = resources


class InvalidTokenError(Exception):
    code = 401

    def __init__(self, badToken, goodToken, badges, discography=None):
        super().__init__({
            "error": self.__class__.__name__,
            "badges": badges,
            "bad_token": badToken,
            "token": goodToken,
            "discography": discography
        })


class InvalidKeyError(Exception):
    code = 403

    def __init__(self, badKey, token, badges):
        super().__init__({
            "error": self.__class__.__name__,
            "bad_key": badKey,
            "badges": badges,
            "token": token
        })


class InternalError(Exception):
    code = 500

    def __init__(self):
        super().__init__({
            "error": self.__class__.__name__
        })


class HandlerBase(ABC):
    @abstractmethod
    def handle(self, event, context):
        pass

    @classmethod
    @abstractmethod
    def describe(cls) -> HandlerDescription:
        pass
