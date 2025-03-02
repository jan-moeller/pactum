import inspect

from pactum import (
    AssertionKind,
    ContractViolation,
    EvaluationSemantic,
)


def test_contract_violation_stringification_pre_predicate_check():
    c = ContractViolation(
        comment="comment",
        kind=AssertionKind.pre,
        location=inspect.Traceback(
            filename="foo.py",
            index=0,
            function="foo",
            positions=None,
            lineno=10,
            code_context=["@pre(foobar)"],
        ),
        semantic=EvaluationSemantic.check,
        kwargs={"x": 42},
    )

    assert c.comment in str(c)
    assert f"{c.location.filename}:{c.location.lineno}" in str(c)
    assert c.location.code_context[0] in str(c)
    assert "Precondition" in str(c)
    assert "'x': 42" in str(c)


def test_contract_violation_stringification_post_predicate_check():
    c = ContractViolation(
        comment="something something",
        kind=AssertionKind.post,
        location=inspect.Traceback(
            filename="foo.py",
            index=0,
            function="foo",
            positions=None,
            lineno=42,
            code_context=["@post(foobar)"],
        ),
        semantic=EvaluationSemantic.check,
        kwargs={"foo": 42},
    )

    assert c.comment in str(c)
    assert f"{c.location.filename}:{c.location.lineno}" in str(c)
    assert c.location.code_context[0] in str(c)
    assert "Postcondition" in str(c)
    assert "'foo': 42" in str(c)
