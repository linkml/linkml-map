from typing import Callable

INTEGRATE_TESTS = []

def add_to_integration(func: Callable) -> Callable:
    """Decorator to register a scaffold setup function for integration tests."""
    INTEGRATE_TESTS.append(func)
    return func

def setup_integration(scaffold):
    for setup_func in INTEGRATE_TESTS:
        setup_func(scaffold)
