from pathlib import Path
import importlib

def test_logging_port_contract_exists():
    mod = importlib.import_module('draft_punks.ports.logging')
    assert hasattr(mod, 'LoggingPort')
    cls = getattr(mod, 'LoggingPort')
    # methods expected
    for name in ('info','warn','error','markdown'):
        assert hasattr(cls, name), f"missing {name} on LoggingPort"
