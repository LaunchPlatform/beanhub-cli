import typing


MakeSession = typing.Callable[[], str]
MakeSessionCookies = typing.Callable[[], typing.Dict[str, typing.Any]]
