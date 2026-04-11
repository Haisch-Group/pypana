from pypana.console import console
from pypana.pana_error import ParticleAnalysisError
from pypana.plots.themes.base import PlotTheme, ThemeSet, _FIELDS


from rich.text import Text

def available_themes() -> ThemeSet:
    return PlotTheme.registered_themes()

def apply_theme(theme: type[PlotTheme] | str | None = None) -> None:
    if theme is None:
        raise ParticleAnalysisError()  # TODO: to be specified with better exception

    if isinstance(theme, str):
        match = next((cls for cls in PlotTheme.registered_themes() if cls.name == theme), None)

        if match is None:
            raise KeyError(f"Unknown theme: {theme!r}")

        theme = match

    assert isinstance(theme, type)
    theme.apply()

def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip('#')
    r, g, b = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def print_themes() -> None:
    for theme in  PlotTheme.registered_themes():
        console.print()
        console.print(Text(f"{theme.name}    ({theme.__name__})", style="bold"))
        console.print("─" * 52)

        if theme.color_cycle:
            for i, hex_color in enumerate(theme.color_cycle, 1):
                foreground = "black" if _luminance(hex_color) > 0.35 else "white"
                line = Text(f"  {i:2}.  ")
                line.append(f"  {hex_color}  ", style=f"{foreground} on {hex_color}")
                console.print(line)

        console.print()

        for attr, field in _FIELDS.items():
            if attr == "color_cycle":
                continue

            value = getattr(theme, attr, None)

            if value is None:
                continue

            keys = [field.keys] if isinstance(field.keys, str) else field.keys

            for key in keys:
                console.print(Text(f"  {key:<30}  {value}", style=""))
