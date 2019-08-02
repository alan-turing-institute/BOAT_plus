import gem5_constants

def get_target_value(results, target_type):
    """ Returns the value of a target function depending on the target_type

    Args:
        results: obtained results from the simulator
        target_type: a key value for the target function

    Returns:
        value: the value of the target function
    """
 
    if target_type in gem5_constants._CONST_TARGET_CHOICES_SIMULATOR:
        value = results[target_type]

    elif target_type in gem5_constants._CONST_TARGET_CHOICES_TESTS:
        
        area = results[gem5_constants._CONST_AREA]
        cycle = results[gem5_constants._CONST_CYCLE]
        power = results[gem5_constants._CONST_POWER]

        area_norm = area / gem5_constants._CONST_MAX_AREA
        cycle_norm = cycle / gem5_constants._CONST_MAX_CYCLE
        power_norm = power / gem5_constants._CONST_MAX_POWER

        c1 = gem5_constants._TARGET_FUNC_COEF[target_type][gem5_constants._CONST_C1]
        c2 = gem5_constants._TARGET_FUNC_COEF[target_type][gem5_constants._CONST_C2]

        value = c1 * (cycle_norm / area_norm) + c2 * (power_norm / area_norm)
        
    else:
        value = 0.0
        raise ValueError('Unrecognised target_type')

    return value 