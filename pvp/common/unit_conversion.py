def cmH2O_to_hPa(pressure: float) -> float:
    """
    Convert cmH2O to hPa

    Args:
        pressure (float): Pressure in cmH2O

    Returns:
        float: Pressure in hPa (pressure / 1.0197162129779)
    """
    return pressure / 1.0197162129779

def hPa_to_cmH2O(pressure: float) -> float:
    """
    Convert hPa to cmH2O

    Args:
        pressure (float): Pressure in hPa

    Returns:
        float: Pressure in cmH2O (pressure * 1.0197162129779)
    """
    return pressure * 1.0197162129779


def rounded_string(value: float, decimals: int = 0) -> str:
    """
    Create a rounded string of a number that doesnt have trailing .0 when decimals = 0

    Args:
        value (float): Value to stringify
        decimals (int): Number of decimal places to round to

    Returns:
        str: Clean rounded string version of number
    """
    if decimals == 0:
        return str(round(value)).split('.')[0]

    else:
        return str(round(value, decimals))