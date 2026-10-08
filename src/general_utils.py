import pandas as pd 
import numpy as np 



def get_days_from_date(date:str, n_days:int): 
    """
    get the n_days either side (and including) a date
    """
    date = pd.Timestamp(date).normalize()
    
    date_range = pd.date_range(date - pd.Timedelta(days=n_days), 
                               date + pd.Timedelta(days=n_days))
    
    return date_range


def format_date_list(dates:list, n_days:int): 
    """
    generate a set of dates that can be used to filter an 
    xarray dataarray, from an array of dates

    generates an n_days either side (and including) each date 
    in a list of dates

    """
    dates_list = [(get_days_from_date(date, n_days)) for date in dates]
    dates_list_formatted = [i.date for i in dates_list]

    return np.concatenate(dates_list_formatted)


