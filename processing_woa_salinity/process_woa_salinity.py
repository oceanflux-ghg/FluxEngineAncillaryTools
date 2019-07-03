#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 15:04:02 2019

Extracts the top (surface) depth from NOAA WOA salinity data and stores in it in a new netCDF file.

@author: rr
"""


from __future__ import print_function;
import argparse;
from string import Template;
import numpy as np;
from netCDF4 import Dataset;
from os import path, makedirs;


def get_year_month_pairs(startYear, startMonth, endYear, endMonth):
    pairs = [];
    for year in range(startYear, endYear+1):
        for month in range(1, 13):
            if year == startYear and month < startMonth:
                continue;
            if year == endYear and month > endMonth:
                continue;
            
            pairs.append( (year, month) );
    return pairs;

#Rebin 2D data to a specified shape.
#Converts to a 4D array, then takes the mean in first and last dimension to give newly binned array.
def rebin(m, shape):
    sh = (shape[0], m.shape[0]//shape[0], shape[1], m.shape[1]//shape[1]);
    return m.reshape(sh).mean(-1).mean(1);


def process_woa_salinity(sourceTemplate=Template("downloaded_files/woa18_decav_s${MM}_01.nc"), destinationRootDirectory="", months=range(1,13)):
    filesSkipped = [];
    filesResampled = [];
    for month in months:
        monthStr = format(month, "02d");
        currentOutputDir = path.join(destinationRootDirectory, "NOAA_WOA_decav_monthly_surface_salinity_1.0x1.0");
        if path.exists(currentOutputDir) == False:
            makedirs(currentOutputDir);
        
        curOutputpath = path.join(currentOutputDir, "NOAA_WOA_decav_surface_salinity_month"+monthStr+"_1.0x1.0.nc");
        if path.exists(curOutputpath) == True: #Don't overwrite existing files.
            #print("Skipping year/month", year, monthStr)
            filesSkipped.append(curOutputpath);
            continue;
        
        #Start processing this month's data.
        print("Processing WOA salinity month:", month);
        monthlyInputNc = Dataset(sourceTemplate.safe_substitute(MM=monthStr), 'r'); #Open nc file
        
        #Copy and process windspeed
        salinity = np.ma.empty((180, 360)); #Create arrays to fit the original data
        salinity[:] = monthlyInputNc.variables["s_an"][0,0,:,:]; #time=0, depth=0, all lat and lon
        
        #Write to netCDF
        newnc = Dataset(curOutputpath, 'w');
        newnc.createDimension(u'time', 1); #create dimensions
        newnc.createDimension(u'lat', int(180));
        newnc.createDimension(u'lon', int(360));
    
        timeVar = newnc.createVariable("time", "float64", (u"time",));
        timeVar.setncatts({k: monthlyInputNc.variables["time"].getncattr(k) for k in monthlyInputNc.variables["time"].ncattrs()}); # Copy variable attributes
        timeVar[:] = monthlyInputNc.variables["time"][:];
    
        lonVar = newnc.createVariable("lon", "float64", (u"lon",));
        lonVar.setncatts({k: monthlyInputNc.variables["lon"].getncattr(k) for k in monthlyInputNc.variables["lon"].ncattrs()}); # Copy variable attributes
        lonVar.valid_min = -180.0;
        lonVar.valid_max = 180.0;
        lonVar[:] = monthlyInputNc.variables["lon"][:];
        
        latVar = newnc.createVariable("lat", "float64", (u"lat",));
        latVar.setncatts({k: monthlyInputNc.variables["lat"].getncattr(k) for k in monthlyInputNc.variables["lat"].ncattrs()}); # Copy variable attributes
        latVar.valid_min = -90.0;
        latVar.valid_max = 90.0;
        latVar[:] = monthlyInputNc.variables["lat"][:];
        
        #windspeed
        sal = newnc.createVariable("sal_mean", "float32", (u"time", u"lat", u"lon"));
        sal.setncatts({k: monthlyInputNc.variables["s_an"].getncattr(k) for k in monthlyInputNc.variables["s_an"].ncattrs()}); # Copy variable attributes
        sal[:] = np.ma.expand_dims(salinity, axis=0);
        
        newnc.close();
        filesResampled.append(curOutputpath);
    
    print("Completed with:\n\t", len(filesResampled), "file(s) resampled\n\t", len(filesSkipped), "file(s) skipped to prevent overwriting existing files.");


if __name__ == "__main__":
        #parse arguments
    description = unicode("""Extracts the top (surface) layer from NOAA WOA salinity data and stores as a new file.
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("--months", nargs="+", default=range(1,13), type=list,
                        help="List of months to be downloaded (1=Jan, 12=Dec). Defaults to all months");
    parser.add_argument("--sourceTemplate", type=str, default="downloaded_files/woa18_decav_s${MM}_01.nc",
                        help="String 'template' for the online download location. The file should be specified using ${MM} for month.");
    parser.add_argument("--destinationRootDirectory", type=str, default="",
                        help="Path to the root directory where processed output files will be stored. Defaults to the current working directory.");
    clArgs = parser.parse_args();

    #Do the resample
    print("* Processing NOAA WOA Salinity data from for months...");
    process_woa_salinity(sourceTemplate=Template(clArgs.sourceTemplate), destinationRootDirectory=clArgs.destinationRootDirectory, months=clArgs.months);










