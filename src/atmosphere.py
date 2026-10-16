


UNITS = {
    'shear': r'm s$^{-1}$', 
    'tbdiff': r'K', 
    'cr': r'mm hr$^{-1}$',
    'pr': r'mm hr$^{-1}$',
    'ua': r'm s$^{-1}$', 
    'va': r'm s$^{-1}$',
    'condensation_rate': r'kg m$^{-2}$ s$^{-1}$', 
    'surface_precip': r'kg m$^{-2}$ s$^{-1}$', 
}



### constants

Rd, g = 287.04, 9.80665



def pressure_from_height(height): 
    pressure = 1013.25 * (1 - 2.25577e-5 * height)**5.25588

    return pressure