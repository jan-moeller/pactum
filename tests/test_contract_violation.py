import inspect

from pycontractz import (
    AssertionKind,
    ContractViolation,
    DetectionMode,
    EvaluationSemantic,
)


def test_contract_violation_stringification_pre_predicate_check():
    c = ContractViolation(
        comment="comment",
        detection_mode=DetectionMode.predicate_false,
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
    )

    assert c.comment in str(c)
    assert f"{c.location.filename}:{c.location.lineno}" in str(c)
    assert c.location.code_context[0] in str(c)
    assert "Precondition" in str(c)


def test_contract_violation_stringification_post_predicate_check():
    c = ContractViolation(
        comment="something something",
        detection_mode=DetectionMode.predicate_false,
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
    )

    assert c.comment in str(c)
    assert f"{c.location.filename}:{c.location.lineno}" in str(c)
    assert c.location.code_context[0] in str(c)
    assert "Postcondition" in str(c)


def test_contract_violation_stringification_assert_exc_check():
    try:
        raise ValueError("Crazy stuff happened")
    except Exception as exc:
        c = ContractViolation(
            comment="something something",
            detection_mode=DetectionMode.evaluation_exception,
            kind=AssertionKind.assertion,
            location=inspect.Traceback(
                filename="foo.py",
                index=0,
                function="foo",
                positions=None,
                lineno=42,
                code_context=["contract_assert(foobar)"],
            ),
            semantic=EvaluationSemantic.check,
        )

        assert c.comment in str(c)
        assert f"{c.location.filename}:{c.location.lineno}" in str(c)
        assert c.location.code_context[0] in str(c)
        assert "Assertion" in str(c)
