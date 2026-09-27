from dash import dcc, html

def StyledLoading(children, id=None):
    if id:
        return dcc.Loading(
            id=id,
            type="default",
            color="var(--accent)",
            children=children
        )
    return dcc.Loading(
        type="default",
        color="var(--accent)",
        children=children
    )
