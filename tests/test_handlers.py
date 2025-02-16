import logging

import pytest

from pactum import (
    ContractViolationException,
    contract_violation_handler,
    handlers,
    pre,
)


def test_raising_handler():
    with (
        pytest.raises(ContractViolationException),
        contract_violation_handler(handlers.raise_on_contract_violation),
    ):

        @pre(lambda: False)
        def test():
            pass

        test()


def test_logging_handler_stderr(capsys):
    with contract_violation_handler(handlers.log_on_contract_violation()):

        @pre(lambda: False)
        def test():
            pass

        test()

        out, err = capsys.readouterr()
        assert "Precondition violation" in err


def test_logging_handler_logging(caplog):
    with contract_violation_handler(handlers.log_on_contract_violation(logging.root)):

        @pre(lambda: False)
        def test():
            pass

        test()

        assert any("Precondition violation" in l.message for l in caplog.records)
