from dash import dcc, html
import theme


def StyledLoading(children, id=None):
    """Themed loading wrapper for callbacks."""
    kwargs = {}
    if id:
        kwargs["id"] = id
    return dcc.Loading(
        type="default",
        color=theme.ACCENT,
        children=children,
        **kwargs,
    )
