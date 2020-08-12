def cmH2O_to_hPa(pressure):
    return pressure*98.0665

def hPa_to_cmH2O(pressure):
    return pressure / 98.0665


def rounded_string(value, decimals=0):
    """
    create a rounded string of a number that doesnt have trailing .0 when decimals = 0
    """
    if decimals == 0:
        return str(round(value)).split('.')[0]

    else:
        return str(round(value, decimals))