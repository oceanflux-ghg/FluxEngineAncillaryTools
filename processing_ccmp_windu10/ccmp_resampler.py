#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 10:25:02 2018

Resample reynolds data to monthly temporal resolution and custom lon and lat resolution.

@author: Tom Holding
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


def resample_ccmpv2(stopYear, stopMonth, startYear=1981, startMonth=9, lonResolution=1.0, latResolution=1.0, sourceTemplate=Template("downloaded_files/avhrr-only-v2.${YYYY}${MM}${DD}.nc"), destinationRootDirectory=""):
    #check resolutions are exact multiples of 180 (lat) and 360 (lon).
    if ((360.0 / lonResolution) % 1.0 != 0) or ((180.0 / latResolution) % 1.0 != 0):
        raise ValueError("Longitude or latitude resolution must be an exact multiple of longitude or latitude (respectively).");
    if lonResolution < 0.25 or latResolution < 0.25:
        raise ValueError("Longitude or latitude resolution cannot be smaller than 0.25 (downloaded data resolution).");
        
    #Check start year is not before the start of the data series.
    if startYear < 1987:
        print("Setting start year to 1987 because there is no data before this.");
        startYear = 1987
    if (startYear == 1987) and (startMonth < 9):
        print("Setting start month to August (8) which is the first full month of data in 1987");
        startMonth = 9;
    
    scriptDirectory = path.dirname(__file__); #Get path from working directory to the directory that the script is in. This will contain the reference file.
    referenceFilename = path.join(scriptDirectory, "REFERENCE_FILE_FOR_METADATA-CCMPv2.0.nc"); #Path to netCDF reference file.
    referenceNc = Dataset(referenceFilename, 'r');
    
    yearMonthsToRun = get_year_month_pairs(startYear, startMonth, stopYear, stopMonth); #inclusive
    
    filesSkipped = [];
    filesResampled = [];
    for (year, month) in yearMonthsToRun:
        currentOutputDir = path.join(destinationRootDirectory, "ccmp_v2.0_monthly_resampled_"+str(lonResolution)+"x"+str(latResolution), str(year));
        
        if path.exists(currentOutputDir) == False:
            makedirs(currentOutputDir);
        
        monthStr = format(month, "02d");
        curOutputpath = path.join(currentOutputDir, "CCMP_Wind_Analysis_"+str(year)+monthStr+"_V02.0_L3.5_RSS_"+str(lonResolution)+"x"+str(latResolution)+".nc");
        
        if path.exists(curOutputpath) == True: #Don't overwrite existing files.
            #print("Skipping year/month", year, monthStr)
            filesSkipped.append(curOutputpath);
            continue;
        
        #Start processing this month's data.
        print("Processing year/month:", year, month)
        monthlyInputNc = Dataset(sourceTemplate.safe_substitute(YYYY=str(year), MM=monthStr), 'r'); #Open nc file
        
        #input file spans all longitude values but an incomplete range of latitudes.
        latRange = (monthlyInputNc.variables["latitude"][0], monthlyInputNc.variables["latitude"][-1]);
        firstLatIndex = int(((latRange[0]-0.125) / 0.25) + 90.0*4);
        lastLatIndex = int(((latRange[1]-0.125) / 0.25) + 90.0*4);
        
        #Copy and process windspeed
        windu10 = np.ma.empty((int(180/0.25), int(360/0.25))); #Create arrays to fit the original data
        windu10[:] = np.nan;
        windu10[firstLatIndex:lastLatIndex+1, :] = monthlyInputNc.variables["wspd"][0,:,:];
        windu10 = np.roll(windu10, int(180/0.25), axis=1); #Original data from 0 to 360 longitude, but we're using -180 to 180
        windu10Rebinned = rebin(windu10, (int(180/latResolution), int(360/lonResolution)));
        
        #copy and process wind component East and North vectors
        wndu = np.ma.empty((int(180/0.25), int(360/0.25))); #Create arrays to fit the original data
        wndu[:] = np.nan;
        wndu[firstLatIndex:lastLatIndex+1, :] = monthlyInputNc.variables["uwnd"][0,:,:];
        wndu = np.roll(wndu, int(180/0.25), axis=1); #Original data from 0 to 360 longitude, but we're using -180 to 180
        wnduRebinned = rebin(wndu, (int(180/latResolution), int(360/lonResolution)));
        
        wndv = np.ma.empty((int(180/0.25), int(360/0.25))); #Create arrays to fit the original data
        wndv[:] = np.nan;
        wndv[firstLatIndex:lastLatIndex+1, :] = monthlyInputNc.variables["vwnd"][0,:,:];
        wndv = np.roll(wndv, int(180/0.25), axis=1); #Original data from 0 to 360 longitude, but we're using -180 to 180
        wndvRebinned = rebin(wndu, (int(180/latResolution), int(360/lonResolution)));
        
        
        #Write to netCDF
        newnc = Dataset(curOutputpath, 'w');
        newnc.createDimension(u'time', 1); #create dimensions
        newnc.createDimension(u'lat', int(180/latResolution));
        newnc.createDimension(u'lon', int(360/lonResolution));
    
        #refTime = datetime(1981, 1, 1, 0, 0, 0);
        #curTime = datetime(year, month, 1, 0, 0, 0);
        #td = curTime-refTime;
        timeVar = newnc.createVariable("time", "float64", (u"time",));
        timeVar.setncatts({k: referenceNc.variables["time"].getncattr(k) for k in referenceNc.variables["time"].ncattrs()}); # Copy variable attributes
        timeVar[:] = referenceNc.variables["time"][:];
        #timeVar[:] = [td.total_seconds()];
    
        lon = np.arange(-180.0+(0.5*lonResolution), 180, lonResolution); #-179.5 to 179.5 in steps of 1
        lonVar = newnc.createVariable("lon", "float64", (u"lon",));
        lonVar.setncatts({k: referenceNc.variables["longitude"].getncattr(k) for k in referenceNc.variables["longitude"].ncattrs()}); # Copy variable attributes
        lonVar.valid_min = -180.0;
        lonVar.valid_max = 180.0;
        lonVar[:] = lon;
        
        lat = np.arange(-90.0+(0.5*latResolution), 90, latResolution); #-89.5 to 89.5 in steps of 1
        latVar = newnc.createVariable("lat", "float64", (u"lat",));
        latVar.setncatts({k: referenceNc.variables["latitude"].getncattr(k) for k in referenceNc.variables["latitude"].ncattrs()}); # Copy variable attributes
        latVar.valid_min = -90.0;
        latVar.valid_max = 90.0;
        latVar[:] = lat;
        
        #windspeed
        var = newnc.createVariable("windu10", "float32", (u"time", u"lat", u"lon"));
        var.setncatts({k: referenceNc.variables["wspd"].getncattr(k) for k in referenceNc.variables["wspd"].ncattrs()}); # Copy variable attributes
        var[:] = np.ma.expand_dims(windu10Rebinned, axis=0);
        
        #Eastward wind component
        var = newnc.createVariable("wndu", "float32", (u"time", u"lat", u"lon"));
        var.setncatts({k: referenceNc.variables["uwnd"].getncattr(k) for k in referenceNc.variables["uwnd"].ncattrs()}); # Copy variable attributes
        var[:] = np.ma.expand_dims(wnduRebinned, axis=0);
        
        #Northward wind conponent
        var = newnc.createVariable("wndv", "float32", (u"time", u"lat", u"lon"));
        var.setncatts({k: referenceNc.variables["vwnd"].getncattr(k) for k in referenceNc.variables["vwnd"].ncattrs()}); # Copy variable attributes
        var[:] = np.ma.expand_dims(wndvRebinned, axis=0);
        
        newnc.close();
        filesResampled.append(curOutputpath);
    
    print("Completed with:\n\t", len(filesResampled), "file(s) resampled\n\t", len(filesSkipped), "file(s) skipped to prevent overwriting existing files.");

if __name__ == "__main__":
        #parse arguments
    description = unicode("""Resamples Reynolds AVHRR daily SST data into monthly averages with user-specified spatial resolution.
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("stopYear", type=int,
                        help="Stop year, e.g. 1999");
    parser.add_argument("stopMonth", type=int,
                        help="Stop month (numeric), e.g. 1 for January, 12 for December.");
    parser.add_argument("startYear", type=int, default=1981,
                        help="Start year, e.g. 1999. Defaults to 1981.");
    parser.add_argument("startMonth", type=int, default=9,
                        help="Start month (numeric), e.g. 1 for January, 12 for December. Defaults to 9 (Septembbe).");
    parser.add_argument("--lonResolution", type=float, default=1.0,
                        help="Resolution (in degrees) for longitude. Must be an exact multiple of 360. Defaults to 1.0");
    parser.add_argument("--latResolution", type=float, default=1.0,
                        help="Resolution (in degrees) for latitude. Must be an exact multiple of 180. Defaults to 1.0");
    parser.add_argument("--sourceTemplate", type=str, default="downloaded_files/CCMP_Wind_Analysis_${YYYY}${MM}_V02.0_L3.5_RSS.nc",
                        help="String 'template' for the online download location. The file should be specified using ${YYYY}, ${MM} and ${DD} for year, month and day, respectively.");
    parser.add_argument("--destinationRootDirectory", type=str, default="",
                        help="Path to the root directory where processed output files will be stored. Defaults to the current working directory.");
    clArgs = parser.parse_args();

    #Do the resample
    print("* Resampling Reynolds data from", clArgs.startMonth, clArgs.startYear, "to", clArgs.stopMonth, clArgs.stopYear, "to a lon/lat resolution of", clArgs.lonResolution, "x", clArgs.latResolution);
    resample_ccmpv2(clArgs.stopYear, clArgs.stopMonth, clArgs.startYear, clArgs.startMonth, clArgs.lonResolution, clArgs.latResolution, sourceTemplate=Template(clArgs.sourceTemplate), destinationRootDirectory=clArgs.destinationRootDirectory);










