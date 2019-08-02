_CONST_AREA = 'area'
_CONST_CYCLE = 'cycle'
_CONST_POWER = 'power'
_CONST_P1 = 'P1'
_CONST_P2 = 'P2'
_CONST_P3 = 'P3'
_CONST_P4 = 'P4'
_CONST_P5 = 'P5'

_CONST_TARGET_CHOICES_SIMULATOR = [_CONST_CYCLE, _CONST_POWER, _CONST_AREA]
_CONST_TARGET_CHOICES_TESTS = [_CONST_P1, _CONST_P2, _CONST_P3, _CONST_P4, _CONST_P5]
_CONST_TARGET_CHOICES = _CONST_TARGET_CHOICES_SIMULATOR + \
    _CONST_TARGET_CHOICES_TESTS

_CONST_C1 = 'C1'
_CONST_C2 = 'C2'

_TARGET_FUNC_COEF = {
    _CONST_P1: {_CONST_C1: 0.50, _CONST_C2: 0.50},
    _CONST_P2: {_CONST_C1: 0.25, _CONST_C2: 0.75},
    _CONST_P3: {_CONST_C1: 0.75, _CONST_C2: 0.25},
    _CONST_P4: {_CONST_C1: 0.99, _CONST_C2: 0.01},
    _CONST_P5: {_CONST_C1: 0.01, _CONST_C2: 0.99}}

### fft_transpose 1000 random search results
# _CONST_MAX_AREA = float(2515230.0)
# _CONST_MAX_CYCLE = float(62966.0)
# _CONST_MAX_POWER = float(225.118)

### eas_eas 1000 random search results (Study 14)
_CONST_MAX_AREA = float(1155350)
_CONST_MAX_CYCLE = float(23282)
_CONST_MAX_POWER = float(69.5747)

		