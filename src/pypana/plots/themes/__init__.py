from pypana.plots.themes import (
    base as base,
)
from pypana.plots.themes import (
    colorful as colorful,
)
from pypana.plots.themes import (
    fraunhofer as fraunhofer,
)
from pypana.plots.themes import (
    ibm as ibm,
)
from pypana.plots.themes import (
    tab10 as tab10,
)
from pypana.plots.themes import (
    tol3 as tol3,
)
from pypana.plots.themes import (
    tol4 as tol4,
)
from pypana.plots.themes import (
    tol7 as tol7,
)
from pypana.plots.themes import (
    tum as tum,
)
from pypana.plots.themes import (
    wong as wong,
)
from pypana.plots.themes.base import BaseTheme
from pypana.plots.themes.base import ThemeSet as ThemeSet
from pypana.plots.themes.utils import available_themes as available_themes
from pypana.plots.themes.utils import print_themes as print_themes


def apply_theme(theme: type[BaseTheme] | str) -> None:
    """Applies the given theme globally. Only imported themes can be referenced by their string name.

    Custom themes should therefore be mainly referenced as type.
    Apart from this method, you can still always fall back to ``plt.style.use('<theme-path>.mplstyle')``
    of the matplotlib package.
    """
    if isinstance(theme, str):
        match = next(
            (
                cls
                for cls in BaseTheme.registered_themes()
                if cls.name and cls.name.lower() == theme.lower()
            ),
            None,
        )

        if match is None:
            raise KeyError(f"Unknown theme: {theme!r}")

        theme = match

    assert isinstance(theme, type)
    theme.apply()
