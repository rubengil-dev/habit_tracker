"""
Number helpers.
"""


def drop_float_noise(value: float) -> float:
    """
    Float noise remover, rounding to 12 significant figures:
        Example: 0.1 + 0.7 = 0.7999999999999999 → 0.8
    """
    return float(f"{value:.12g}")
