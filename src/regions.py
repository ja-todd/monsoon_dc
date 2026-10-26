

REGIONS = {
    'wam': {
        'display':     'WAM',
        'lon_min':     340, 'lon_max': 20,    # wraps: 340–360° + 0–20°
        'lat_min':     2,   'lat_max': 15,
        'buf_lon_min': -25, 'buf_lon_max': 25,
        'buf_lat_min': -3,  'buf_lat_max': 20,
        },

    'sahel': {
        'display':     'SAHEL',
        'lon_min':     340, 'lon_max': 20,    # wraps: 340–360° + 0–20°
        'lat_min':     3,   'lat_max': 15,
        'buf_lon_min': -20, 'buf_lon_max': 25,
        'buf_lat_min': 3,  'buf_lat_max': 15,
        },
    'tropics_wide': {
        'display': 'TROPICS', 
        'lon_min': 320, 'lon_max': 100, 
        'lat_min': 0, 'lat_max': 45, 
        'buf_lon_min': -25, 'buf_lon_max': 105,
        'buf_lat_min': -3,  'buf_lat_max': 25,
        },
    'india': { 
        'display': 'INDIA', 
        'lon_min': 55, 'lon_max': 105, 
        'lat_min': 5, 'lat_max': 35, 
        'buf_lon_min': 50, 'buf_lon_max': 110,
        'buf_lat_min': 0,  'buf_lat_max': 40,
            }, 
        
    'wAfr': {
            'display':     'West_Africa',
            'lon_min':     330, 'lon_max': 20,    # wraps: 340–360° + 0–20°
            'lat_min':     0,   'lat_max': 35,
            'buf_lon_min': -35, 'buf_lon_max': 25,
            'buf_lat_min': -5,  'buf_lat_max': 40,
            },

    'nAfr': {
                'display':     'North_Africa',
                'lon_min':     320, 'lon_max': 50,    # wraps: 340–360° + 0–20°
                'lat_min':     -5,   'lat_max': 40,
                'buf_lon_min': -45, 'buf_lon_max': 55,
                'buf_lat_min': -10,  'buf_lat_max': 45,
                },

    

}


INDIA_REGIONS = {
        'NI':{ 
            'lon_min': 75, 'lon_max': 84, 
            'lat_min': 26, 'lat_max': 33,
            'color': '#E91EC8'
        }, 
        'CI':{ 
           'lon_min': 75, 'lon_max': 83.5, 
           'lat_min': 18, 'lat_max': 25.5,
           'color': '#E8212B'
                },
         'ENE':{ 
            'lon_min': 84.5, 'lon_max': 95, 
            'lat_min': 22, 'lat_max': 29,
             'color': '#2DD4D9'           },
         'WI':{ 
                'lon_min': 68, 'lon_max': 74, 
                'lat_min': 22, 'lat_max': 28,
             'color': '#1F3FD6'                   },
         'SI':{ 
            'lon_min': 74, 'lon_max': 80, 
            'lat_min': 8, 'lat_max': 16,
             'color': '#E8A33D'   } 


        
}

mumbai_lats = [18.5, 19.5]
mangalore_lats = [12.5, 13.5]
goa_lats = [14.5, 15.5]
kochi_lats = [9.5, 10.5]

location_dict = {
    'Mumbai': {'latitudes': mumbai_lats}, 
    'Goa': {'latitudes': goa_lats}, 
    'Mangalore': {'latitudes': mangalore_lats}, 
    'Kochi': {'latitudes': kochi_lats}
}