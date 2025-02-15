import re

from pycontractz._evaluation_semantic import EvaluationSemantic
from pycontractz._assertion_kind import AssertionKind
from pycontractz._contract_assertion_label import ContractAssertionInfo


def ignore(
    semantic: EvaluationSemantic,
    info: ContractAssertionInfo,
) -> EvaluationSemantic:
    """A contract assertion label marking everything as ignored"""
    return EvaluationSemantic.ignore


def ignore_postconditions(
    semantic: EvaluationSemantic,
    info: ContractAssertionInfo,
) -> EvaluationSemantic:
    """A contract assertion label marking all postconditions as ignored"""

    if info.kind == AssertionKind.post:
        return EvaluationSemantic.ignore
    return semantic


__expensive_assertions_enabled = True


def expensive(
    semantic: EvaluationSemantic,
    info: ContractAssertionInfo,
) -> EvaluationSemantic:
    """A contract assertion label marking an assertion as expensive to check"""

    if not __expensive_assertions_enabled:
        return EvaluationSemantic.ignore
    return semantic


def set_expensive_assertions_enabled(enabled: bool):
    """Allows to enable or disable expensive contract checks"""
    global __expensive_assertions_enabled
    __expensive_assertions_enabled = enabled


def get_expensive_assertions_enabled() -> bool:
    """Retrieves whether expensive contract checks are currently enabled"""
    return __expensive_assertions_enabled


class enable_expensive:
    def __init__(self, enable: bool = True):
        self.enable = enable

    def __enter__(self):
        self.__old_enable = get_expensive_assertions_enabled()
        set_expensive_assertions_enabled(self.enable)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_expensive_assertions_enabled(self.__old_enable)
        return False


class filter_by_module:
    """A contract assertion label factory that marks assertions as ignored if they don't pass a regex"""

    def __init__(self, regex: re.Pattern | str):
        if isinstance(regex, str):
            self.regex = re.compile(regex)
        else:
            self.regex = regex

    def __call__(
        self,
        semantic: EvaluationSemantic,
        info: ContractAssertionInfo,
    ) -> EvaluationSemantic:
        if self.regex.search(info.module_name) is None:
            return EvaluationSemantic.ignore
        return semantic
