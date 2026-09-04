"""Phase 0 smoke test: the environment and package are importable."""


def test_package_imports() -> None:
    import copper_hedge  # noqa: F401


def test_core_dependencies_import() -> None:
    import numpy  # noqa: F401
    import pandas  # noqa: F401
    import statsmodels  # noqa: F401
