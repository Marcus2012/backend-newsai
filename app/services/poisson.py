"""Poisson estimator retirado (dependía de API-SPORTS)."""


class PoissonError(Exception):
    """Custom error for Poisson estimator"""


def _raise_retired() -> None:
    raise PoissonError("Poisson estimator fue retirado de este servicio")


async def estimate_scoreline_from_match(*_args, **_kwargs):
    _raise_retired()
