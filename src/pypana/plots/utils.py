"""Utils for plotting the data."""


def split_kwargs(*args: str, **kwargs: object) -> tuple[dict[str, object], ...]:
    """Splits the given args into subkwargs by their prefix given in args.

    Args:
        *args: Positional prefixes.
        **kwargs: Keyword arguments to split by prefix.

    Returns:
        A tuple with each Keyword Argument sorted into its position given by the args prefix.
    """
    subkwargs: list[dict[str, object]] = []

    for arg in args:
        argkwargs: dict[str, object] = {}

        for kwarg, value in kwargs.items():
            if kwarg.startswith(arg):
                argkwargs.update({kwarg.split(arg, 1)[-1]: value})

        subkwargs.append(argkwargs)

    return tuple(subkwargs)
