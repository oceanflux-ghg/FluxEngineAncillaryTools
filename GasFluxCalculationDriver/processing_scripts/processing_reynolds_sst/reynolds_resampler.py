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
import calendar;
from netCDF4 import Dataset;
from os import path, makedirs;
from datetime import datetime;


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

def rebin_sum(m, shape):
    sh = (shape[0], m.shape[0]//shape[0], shape[1], m.shape[1]//shape[1]);
    return m.reshape(sh).sum(-1).sum(1);

def resample_reynolds(stopYear, stopMonth, startYear=1981, startMonth=9, lonResolution=1.0, latResolution=1.0, sourceTemplate=Template("downloaded_files/avhrr-only-v2.${YYYY}${MM}${DD}.nc"), destinationRootDirectory=""):
    if ((360.0 / lonResolution) % 1.0 != 0) or ((180.0 / latResolution) % 1.0 != 0):
        raise ValueError("Longitude or latitude resolution must be an exact multiple of longitude or latitude (respectively).");
    if lonResolution < 0.25 or latResolution < 0.25:
        raise ValueError("Longitude or latitude resolution cannot be smaller than 0.25 (downloaded data resolution).");
    
    scriptDirectory = path.dirname(__file__); #Get path from working directory to the directory that the script is in. This will contain the reference file.
    referenceFilename = path.join(scriptDirectory, "REFERENCE_FILE_FOR_METADATA-REYNOLDS.nc"); #Path to netCDF reference file.
    referenceNc = Dataset(referenceFilename, 'r');
    
    yearMonthsToRun = get_year_month_pairs(startYear, startMonth, stopYear, stopMonth); #inclusive
    
    filesSkipped = [];
    filesResampled = [];
    for (year, month) in yearMonthsToRun:
        currentOutputDir = path.join(destinationRootDirectory, "reynolds_avhrr_only_monthly_resampled_"+str(lonResolution)+"x"+str(latResolution), str(year));
        
        if path.exists(currentOutputDir) == False:
            makedirs(currentOutputDir);
        
        monthStr = format(month, "02d");
        
        curOutputpath = path.join(currentOutputDir, str(year)+monthStr+"01_OCF-SST-GLO-1M-100-REYNOLDS_"+str(lonResolution)+"x"+str(latResolution)+".nc");
        if path.exists(curOutputpath) == True: #Don't overwrite existing files.
            #print("Skipping year/month", year, monthStr)
            filesSkipped.append(curOutputpath);
            continue;
        
        print("Processing year/month:", year, month)
        sstVals = np.ma.empty((calendar.monthrange(year, month)[1], int(180/latResolution), int(360/lonResolution)));
        sstCountVals = np.ma.empty((calendar.monthrange(year, month)[1], int(180/latResolution), int(360/lonResolution)));
        sstErrVals = np.ma.empty((calendar.monthrange(year, month)[1], int(180/latResolution), int(360/lonResolution)));
        iceVals = np.ma.empty((calendar.monthrange(year, month)[1], int(180/latResolution), int(360/lonResolution)));

        for day in range(1, calendar.monthrange(year, month)[1]+1):
            dayStr = format(day, "02d");
            #try each supplied sourceTemplate until we find one that matches a file
            dailyInputNc = None;
            for filePathTemplate in sourceTemplate:
                if path.exists(filePathTemplate.safe_substitute(YYYY=str(year), MM=monthStr, DD=dayStr)):
                    dailyInputNc = Dataset(filePathTemplate.safe_substitute(YYYY=str(year), MM=monthStr, DD=dayStr), 'r');
                    break;
            if dailyInputNc is None: #No matching template was found
                print(" *** WARNING: No sourceTemplate matched for ", year, monthStr, dayStr);
            
            sst = dailyInputNc.variables["sst"][0,0,:,:];
            sstRebinned = rebin(sst, (int(180/latResolution), int(360/lonResolution)));
            sstVals[day-1,:,:] = sstRebinned;

            sstCounts = sst.mask==False;
            sstCounts = rebin_sum(sstCounts, (int(180/latResolution), int(360/lonResolution)));
            hasData = np.where(sstCounts > 0);
            sstCountVals[day-1,:,:] = sstCounts;

            sstErrSquared = dailyInputNc.variables["err"][0,0,:,:]**2;
            sstErrRebinned = np.sqrt(rebin_sum(sstErrSquared, (int(180/latResolution), int(360/lonResolution))));
            sstErrRebinned[hasData] /= sstCounts[hasData];
            sstErrVals[day-1,:,:] = sstErrRebinned;
            #allErrs[hasData] += errs[hasData]**2; #sum errors as variance
            
            ice = dailyInputNc.variables["ice"][0,0,:,:];
            iceRebinned = rebin(ice, (int(180/latResolution), int(360/lonResolution)));
            iceVals[day-1,:,:] = iceRebinned;
    
    
        #Calculate data for monthly output file
        #SST
        means = sstVals.mean(0);
        counts = sstCountVals.sum(0);
        errs = np.sqrt(np.sum(sstErrVals**2, axis=0) / sstVals.count(0));
        #counts = sstVals.count(0);
        #stddevs = sstVals.std(0);
        #variances = sstVals.var(0);
        #medians = np.ma.median(sstVals, axis=0);
        
        means = np.roll(means, -int(180/latResolution), axis=1);
        counts = np.roll(counts, -int(180/latResolution), axis=1);
        errs = np.roll(errs, -int(180/latResolution), axis=1);
        #stddevs = np.roll(stddevs, -int(180/latResolution), axis=1);
        #variances = np.roll(variances, -int(180/latResolution), axis=1);
        #medians = np.roll(medians, -int(180/latResolution), axis=1);
        
        #ICE
        meansIce = iceVals.mean(0);
        meansIce = np.roll(meansIce, -int(180/latResolution), axis=1);
    
        
        #Write to netCDF
        newnc = Dataset(curOutputpath, 'w');
        newnc.createDimension(u'time', 1); #create dimensions
        newnc.createDimension(u'lat', int(180/latResolution));
        newnc.createDimension(u'lon', int(360/lonResolution));
    
        refTime = datetime(1981, 1, 1, 0, 0, 0);
        curTime = datetime(year, month, 1, 0, 0, 0);
        td = curTime-refTime;
        timeVar = newnc.createVariable("time", "float64", (u"time",));
        timeVar.setncatts({k: referenceNc.variables["time"].getncattr(k) for k in referenceNc.variables["time"].ncattrs()}); # Copy variable attributes
        timeVar[:] = [td.total_seconds()];
    
        lon = np.arange(-180.0+(0.5*lonResolution), 180, lonResolution); #-179.5 to 179.5 in steps of 1
        lonVar = newnc.createVariable("lon", "float64", (u"lon",));
        lonVar.setncatts({k: referenceNc.variables["lon"].getncattr(k) for k in referenceNc.variables["lon"].ncattrs()}); # Copy variable attributes
        lonVar[:] = lon;
        
        lat = np.arange(-90.0+(0.5*latResolution), 90, latResolution); #-89.5 to 89.5 in steps of 1
        latVar = newnc.createVariable("lat", "float64", (u"lat",));
        latVar.setncatts({k: referenceNc.variables["lat"].getncattr(k) for k in referenceNc.variables["lat"].ncattrs()}); # Copy variable attributes
        latVar[:] = lat;
        
        #SST
        meanVar = newnc.createVariable("sst_mean", "float32", (u"time", u"lat", u"lon"));
        meanVar.setncatts({k: referenceNc.variables["sst_mean"].getncattr(k) for k in referenceNc.variables["sst_mean"].ncattrs()}); # Copy variable attributes
        meanVar[:] = np.ma.expand_dims(means, axis=0);
        
        countVar = newnc.createVariable("sst_count", "uint32", (u"time", u"lat", u"lon"));
        countVar.setncatts({k: referenceNc.variables["sst_count"].getncattr(k) for k in referenceNc.variables["sst_count"].ncattrs()}); # Copy variable attributes
        countVar[:] = np.ma.expand_dims(counts, axis=0);
        
        stddevVar = newnc.createVariable("sst_stddev", "float32", (u"time", u"lat", u"lon"));
        stddevVar.setncatts({k: referenceNc.variables["sst_stddev"].getncattr(k) for k in referenceNc.variables["sst_stddev"].ncattrs()}); # Copy variable attributes
        stddevVar[:] = np.ma.expand_dims(errs, axis=0);
        
        #ICE
        meanIce = newnc.createVariable("ice", "float32", (u"time", u"lat", u"lon"));
        meanIce.valid_min = 0.0;
        meanIce.valid_max = 100.0;
        meanIce.units = "percentage";
        meanIce.long_name = "Sea ice concentration";
        meanIce.fill_value = -999.0;
        meanIce[:] = np.ma.expand_dims(meansIce, axis=0);
        
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
    parser.add_argument("--sourceTemplate", type=str, nargs="+", default="downloaded_files/avhrr-only-v2.${YYYY}${MM}${DD}.nc",
                        help="String 'template' for the online download location. The file should be specified using ${YYYY}, ${MM} and ${DD} for year, month and day, respectively.");
    parser.add_argument("--destinationRootDirectory", type=str, default="",
                        help="Path to the root directory where processed output files will be stored. Defaults to the current working directory.");
    clArgs = parser.parse_args();

    #Do the resample
    print("* Resampling Reynolds data from", clArgs.startMonth, clArgs.startYear, "to", clArgs.stopMonth, clArgs.stopYear, "to a lon/lat resolution of", clArgs.lonResolution, "x", clArgs.latResolution);
    resample_reynolds(clArgs.stopYear, clArgs.stopMonth, clArgs.startYear, clArgs.startMonth, clArgs.lonResolution, clArgs.latResolution, sourceTemplate=[Template(template) for template in clArgs.sourceTemplate], destinationRootDirectory=clArgs.destinationRootDirectory);










