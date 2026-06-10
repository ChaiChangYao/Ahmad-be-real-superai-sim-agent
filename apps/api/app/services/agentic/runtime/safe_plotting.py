"""Suppress native matplotlib/Qt popups in web mode."""
from __future__ import annotations


def suppress_native_matplotlib() -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
    except Exception:
        pass


def patch_plt_show_for_web() -> None:
    try:
        import matplotlib.pyplot as plt

        def _noop_show(*_args, **_kwargs):
            return None

        plt.show = _noop_show  # type: ignore[method-assign]
    except Exception:
        pass


def save_matplotlib_figure_if_created() -> None:
    pass
