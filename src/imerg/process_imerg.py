"""
Code written by Steve Woolnough, with a couple of tweaks from JT
"""

import numpy as np
import h5py 
import xarray as xr
import datetime as dt
import pandas as pd
import cf
import pickle
import datetime

def read_imerg_v7(time,lon_range=None,lat_range=None):
# Subroutine to read precipitation from single imerg file and
# convert to xarray data array
# Can pass time as datetime.datetime object or list [YYYY,MM,DD,HH,min] 
# If you wish to restrict data across the Dateline then you can specify
# lon_range in [[0,180],(180,360]]
# lat_range should be [South,North]

    if not isinstance(time,dt.datetime) :
        time=dt.datetime(time[0],time[1],time[2],time[3],time[4],0)
        print("I'm here")
 
    filename='/badc/gpm/data/GPM-IMERG-v7/'
    filename=filename+time.strftime('%Y/%j/')
    filename=filename+'3B-HHR.MS.MRG.3IMERG.'
    filename=filename+time.strftime('%Y%m%d')
    filename=filename+time.strftime('-S%H%M%S')
    filename=filename+\
        (time+dt.timedelta(minutes=29,seconds=59)).strftime('-E%H%M%S')
    filename=filename+\
        '.{:04d}.V07B.HDF5'.format(int((\
        time-dt.datetime(time.year,time.month,time.day,0,0,0)).seconds/60))


#    print(filename)

    df=h5py.File(filename)
#    list(df.keys())


    ppt=np.transpose(df['Grid']['precipitation'][()],(0,2,1))
    units=df['Grid']['precipitation'].attrs['units'].decode('utf-8')
    lon=df['Grid']['lon'][()]
    lat=df['Grid']['lat'][()]

    da=xr.DataArray(data=ppt,name='precipitation',\
                dims=['time','latitude','longitude'],\
                coords={'longitude' : lon,\
                'latitude' : lat,\
                'time' : [time]})
    da=da.where(da !=-9999.9)
    da.attrs['units']=units
    da.attrs['Description']='IMERG_v7.0 30min precipitation flux '+\
        'at 0.1 x 0.1 degree resolution - converted to netcdf.'+\
        ' Obtained from /badc/GPM/GPM-IMERG-V7'


    
    slices={}
    if lon_range :
        slices=dict(slices,\
                    **{'longitude' : slice(lon_range[0],lon_range[1])})
        if lon_range[1] > 180.0 :
           da.coords['longitude']=(da.coords['longitude'] +360) %360 
           da=da.sortby(da.longitude)
    if lat_range :
        if lat_range[1] < lat_range[0] :
            lat_range=np.flip(lat_range)
        slices=dict(slices,\
                    **{ 'latitude' : slice(lat_range[0],lat_range[1])})
    da['longitude'].attrs['units']='degrees_east'
    da['latitude'].attrs['units']='degrees_north'
        
    if slices :
        da=da.sel(slices)
    

    return (da)

def read_mfimerg_v7(first_time,last_time,\
                    time_method=None,lon_range=None,lat_range=None) :
# Wrapper to read multiple imerg files and perform some basic operations \
# and output xarray data array
# First_time and last_time must be of the format datetime.datetime\
# or integer values of [YYYY,MM,DD,HH,MM]
# Valid time_methods :
#                'daily' : produce daily averages of precipitation rate
    
    if not isinstance(first_time,dt.datetime) :
        first_time=dt.datetime(first_time[0],first_time[1],first_time[2],\
                               first_time[3],first_time[4],0)
    if not isinstance(last_time,dt.datetime) :
        last_time=dt.datetime(last_time[0],last_time[1],last_time[2],\
                              last_time[3],last_time[4],0)

    times=pd.date_range(first_time,last_time,freq='30min')

    data_arrays=[]
    for time in times :
        da1=read_imerg_v7(time,lon_range=lon_range,lat_range=lat_range)
        data_arrays.append(da1)
    da=xr.concat(data_arrays,dim='time')
    print,da

    if time_method == 'daily' :
        da=da.resample(time='1D').mean()
        da.attrs['Time processing']='Converted to daily mean'

    return(da)

def regrid_imerg (da_in,dx_new=0.5,dy_new=0.5,\
                  lat_out=[-30,30],lon_out=[0,360], \
                  regrid_file=None) :

# rountine to regrid 0.1x0.1deg IMERG data to new grid default=0.5x0.5

    
    
    da=da_in.copy()

    p=cf.Field()
    if (da.dims[0] == 'time') | (da.dims [0]=='t') :
        l_time=True
        domain_axisT=cf.DomainAxis(da[da.dims[0]].size)
        dimT=cf.DimensionCoordinate(data=cf.Data(da[da.dims[0]].data),\
                                    properties={'standard_name' : 'time'})
        axisT = p.set_construct(domain_axisT)
    else :
        l_time=False


    if (len(da.dims) == 4) | ((l_time==False) & (len(da.dims) == 4)) :
        l_zed=True
        domain_axisZ=cf.DomainAxis(da[da.dims[-3]].size)
        dimZ=cf.DimensionCoordinate(data=da[da.dims[-3]].data)
        axisZ = p.set_construct(domain_axisZ)
    else :
        l_zed=False

    domain_axisY=cf.DomainAxis(da[da.dims[-2]].size)
    lats=da[da.dims[-2]].data.astype(np.float32)
    dimY=cf.DimensionCoordinate(data=cf.Data(lats),\
        properties={'standard_name' : 'latitude', 'units' : 'degrees_north'})
    axisY = p.set_construct(domain_axisY)
    dy=float(lats[1]-lats[0])
    lat_bounds=np.empty((da[da.dims[-2]].size,2))
    lat_mids=np.append(np.append(lats[0]-dy/2,(lats[0:-1]+lats[1:])/2),\
                       lats[-1]+dy/2)
    lat_bounds[:,0]=lat_mids[0:-1]
    lat_bounds[:,1]=lat_mids[1:]
    lat_bounds=cf.Bounds(data=cf.Data(lat_bounds))
    dimY.set_bounds(lat_bounds)

    domain_axisX=cf.DomainAxis(da[da.dims[-1]].size)
    lons=da[da.dims[-1]].data.astype(np.float32)
    dimX=cf.DimensionCoordinate(data=cf.Data(lons),\
        properties={'standard_name' : 'longitude', 'units' : 'degrees_east'})
    axisX = p.set_construct(domain_axisX)
    dx=float(lons[1]-lons[0])
    lon_bounds=np.empty((da[da.dims[-1]].size,2))
    lon_mids=np.append(np.append(lons[0]-dx/2,(lons[0:-1]+lons[1:])/2),\
                       lons[-1]+dx/2)
    lon_bounds[:,0]=lon_mids[0:-1]
    lon_bounds[:,1]=lon_mids[1:]
    lon_bounds=cf.Bounds(data=cf.Data(lon_bounds))
    dimX.set_bounds(lon_bounds)

    p.set_data(da.data)

    if l_time :
        p.set_construct(dimT)
    if l_zed :
        p.set_construct(dimZ)
    p.set_construct(dimY)
    p.set_construct(dimX)

    # if regrid_file :
    #     rfile=open(regrid_file,'rb')
    #     regridder=pickle.load(rfile)
    if regrid_file: 
        with open(regrid_file, 'rb') as rfile: 
            regridder = pickle.load(rfile)
    
    else:

        domain=cf.Domain.create_regular((lon_out[0],lon_out[1],dx_new),\
                                    (lat_out[0],lat_out[1],dy_new))
        regridder = p.regrids(domain,method='conservative',return_operator=True)


    c=p.regrids(regridder)

    da_out=xr.DataArray(data=c.array,name='precipitation',\
                    dims=['time','latitude','longitude'],\
                    coords={\
                    'longitude' : c.dimension_coordinate('longitude').array,\
                    'latitude' : c.dimension_coordinate('latitude').array,\
                    'time' : da.time.values})

    da_out.attrs=da.attrs
    da_out.attrs['space_processing']=\
        'Regridded using cfpython conservative method'
    da_out.longitude.attrs=da.longitude.attrs
    da_out.latitude.attrs=da.latitude.attrs

    return da_out
