#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 10:53:22 2019

@author: verwirrt
"""

import pandas as pd;
import numpy as np;
from os import path, makedirs
from netCDF4 import Dataset;
from string import Template;
import argparse;
#import matplotlib.pyplot as plt; #debugging
#from datetime import datetime, timedelta; #debugging


def calc_time_index(year, month, startYear):
    return (year - startYear)*12 + (month-1);

def year_month_from_time_index(index, startYear):
    year = int(index/12) + startYear;
    month = index%12;
    return year, month+1;
    

#Processes marine boundary layer reference vCO2 data (downloaded from https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php ) to a format which is
#compatible with FluxEngine. Interpolates across latitudes and takes a weighted mean of their 7.6 day time steps to produce monthly means values.
def process_esrl_mbl_vco2(stopYear, startYear, inputPath, destinationDir="noaa_esrl_mbl_reflayer_vCO2_1.0x1.0"):
    #sums a row of mbl data into the correct slice of an array and gives it a weighting corresponding to the number of days entry represents.
    #modified in place
    def accumulate_data(dataVals, dataUncertainties, totalDays, year, month, row, weighting=1.0, startYear=1979):
        tIndex = calc_time_index(year, month, startYear);
        if tIndex < len(dataVals): #Sometimes the last row spills over onto another year (past the stop date)
            totalDays[tIndex] += weighting;
            
            dataVals[tIndex, :] += row[valueIndices]*weighting;
            dataUncertainties[tIndex, :] += row[uncertaintyIndices]*weighting;
    
        #    #debugging.    
        #    rowYear = int(row["decimal_date"]);
        #    mblDate = datetime(rowYear, 1, 1) + (timedelta(days=(row["decimal_date"]-rowYear)*365.0));
        #    mblDate2 = mblDate + timedelta(days=(365.0/48.0));
        #    
        #    #MBL dataset doesn't have a concept of leap years, but all the python functions do. If we cross the end of 28th Feb on a leap year we need to add one day to the timestep increment.
        #    if calendar.isleap(mblDate.year) and (mblDate.month==2 and mblDate2 <= datetime(mblDate2.year, mblDate.month, 29)):
        #        mblDate2 += timedelta(days=1);
        #    #If we've already passed 29th Feb on a leap year add one to all the dates
        #    elif calendar.isleap(mblDate.year) and mblDate <= datetime(mblDate2.year, mblDate.month, 29):
        #        mblDate += timedelta(days=1);
        #        mblDate2 += timedelta(days=1);
        #    
        #    if ((mblDate.year == year) or (mblDate2.year == year)) and ((mblDate.month == month) or (mblDate2.month == month)):
        #        print "|", mblDate.year, mblDate.month, mblDate.day, "|", year, month, "|", mblDate2.year, mblDate2.month, mblDate2.day, "|";
        #    else:
        #        print "|", mblDate.year, mblDate.month, mblDate.day, "|", year, month, "|", mblDate2.year, mblDate2.month, mblDate2.day, "|";
        #        raise Exception("Oh nooooo!");
        #    #start = datetime(1980, 1, 1) + timedelta(0.979167*365.0 + 1); end = start + timedelta(days=365.0/48.0)
        #
    
    outputNetCDFTemplate = Template(path.join(destinationDir, "${YYYY}${MM}_marine_boundary_layer_reference_vCO2.nc"));
    daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]; #The marine boundary reference data ignore leap years
    decimalMonthStarts = [0.0] + [days / 365.0 for days in np.cumsum(daysInMonths)]; #Time in decimal years that months start and end (ignoring leap years)
    mblDecimalTimeInterval = 365.0/48.0; #in days, mbl dataset timepoints are this long (approx 7.6 days)
    sinLats = [-1.0, -0.95, -0.9, -0.85, -0.8, -0.75, -0.7, -0.65, -0.6, -0.55, -0.5, -0.45, -0.4, -0.35, -0.3, -0.25, -0.2, -0.15, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0];
    latsUsedByMBL = [np.rad2deg(np.arcsin(sinLat)) for sinLat in sinLats]; #Converting sin(lat) back to plain lat.
    roundedLats = [np.round(lat) for lat in latsUsedByMBL]; #1x1 degree grid, so round/'bin' to nearest latitude.
    inputColNames = ["decimal_date"];
    for roundedLat in roundedLats:
        inputColNames = inputColNames + ["value_"+str(int(roundedLat)), "uncertainty_"+str(int(roundedLat))];
    
    valueIndices = [1+(i*2) for i in range(len(latsUsedByMBL))]; #Indices in data file which refer to vCO2 values
    uncertaintyIndices = [i+1 for i in valueIndices]; #Indices in data file which refer to uncertainties
    
    #import data
    inputData = np.genfromtxt(inputPath, dtype=float, names=inputColNames);
    inputData = pd.DataFrame(inputData);
    
    #Make sure destination directory exists
    if path.exists(destinationDir) == False:
        makedirs(destinationDir);
    
    ####################
    # Main calculation #
    ####################
    dataVals = np.zeros((calc_time_index(stopYear, 12, startYear)+1, len(valueIndices)));
    dataUncertainties = np.zeros((calc_time_index(stopYear, 12, startYear)+1, len(valueIndices)));
    totalDays = np.zeros((480), dtype=float);
    
    curYear = startYear;
    curMonthIndex = 0; #0=jan, 11=dec
    skippedInputData = [];
    for r in range(len(inputData)): #loop through each row of the input data assigning row a month/year and a weighting then calculate weighted mean
        #print r, "of", len(inputData);
        row = inputData.iloc[r];
        
        #Check year matches
        curRowsYear = int(row["decimal_date"]);
        if (curRowsYear != curYear) or (curRowsYear > stopYear):
            print "Skipping row", r, "(year", str(curRowsYear)+") because it is not year", curYear;
            skippedInputData.append(row["decimal_date"]);
            continue;
        
        #Calculate how much of this data point belong to this month, and how much to the next month.
        startPointThroughYear = row["decimal_date"]-curYear;
        endPointThroughYear = startPointThroughYear + (365.0/48.0)/365.0;
    
        if endPointThroughYear <= decimalMonthStarts[curMonthIndex+1]: #+1 for start of next month
            #It all belongs to this month, so add values to the current months/year with a weighting of the full time period
            accumulate_data(dataVals, dataUncertainties, totalDays, curYear, curMonthIndex+1, row, weighting=mblDecimalTimeInterval, startYear=startYear);
            
            #Special case where the datapoint ends exactly where the next year starts
            if endPointThroughYear == 1.0:
                curYear += 1;
                curMonthIndex = 0;
        
        else: #Some of this data point belongs to the next month
            #How much in the next month?
            nextMonthWeighting = (endPointThroughYear - decimalMonthStarts[curMonthIndex+1]) * 365.0;
            
            #Remaining belongs to this month.
            curMonthWeighting = (365.0/48.0) - nextMonthWeighting;
            
            #Add to correct years and increment month
            accumulate_data(dataVals, dataUncertainties, totalDays, curYear, curMonthIndex+1, row, weighting=curMonthWeighting, startYear=startYear);
            curMonthIndex += 1;
            if curMonthIndex > 11:
                curYear += 1;
                curMonthIndex = 0;
            accumulate_data(dataVals, dataUncertainties, totalDays, curYear, curMonthIndex+1, row, weighting=nextMonthWeighting, startYear=startYear);
    
    
    #Divide by the total weighting (total number of days) used for each monthly sum
    for i in range(dataVals.shape[0]):
        if (totalDays[i] != 0 and np.isfinite(totalDays[i])):
            dataVals[i, :] = dataVals[i, :] / totalDays[i];
            dataUncertainties[i, :] = dataUncertainties[i, :] / totalDays[i];
    
    
    
    #########################################################################################
    # Now interpolate to a standard lon/lat grid. Also write output files while we're at it #
    #########################################################################################
    filesProcessed = []
    filesSkipped = [];
    #For each month linearly interpolate to 1 degree latitude transect, stretch to a 2D 1x1 degree grid and write to netCDF
    gridLats = np.arange(-89.5, 90.0, 1.0);
    for i in range(len(dataVals)):
        yearMonth = year_month_from_time_index(i, startYear);
        #linear interpolation for latitude
        values = dataVals[i];
        interpolatedValues = np.interp(gridLats, latsUsedByMBL, values);
        
    #    #Debug plot
    #    if yearMonths[i][0] == 2013 and yearMonths[i][1] == 10:
    #        plt.figure();
    #        plt.plot(latsUsedByMBL, values, 'b');
    #        plt.plot(gridLats, interpolatedValues, 'r');
        
        #stretch around longitude (360 1 degree steps)
        interpolatedValues.shape = (len(interpolatedValues), 1);
        interpolatedValues = np.repeat(interpolatedValues, 360, axis=1);
        
        #write to netCDF
        outputNetCDFPath = outputNetCDFTemplate.safe_substitute(YYYY=str(yearMonth[0]), MM=format(yearMonth[1], "02d"));
        if path.exists(outputNetCDFPath) == True:
            filesSkipped.append(outputNetCDFPath);
            continue;

        #Create new netCDF file
        print "Writing output file for", yearMonth[0], str(yearMonth[1])+":", path.basename(outputNetCDFPath);
        ncout = Dataset(outputNetCDFPath, 'w');
        latRes = 1.0; lonRes = 1.0;
        ncout.createDimension('lat', 180.0/latRes);
        ncout.createDimension('lon', 360.0/lonRes);
        
        latVar = ncout.createVariable("lat", np.dtype(float), ("lat",) );
        latVar[:] = np.arange(-90+(latRes/2.0), 90+(latRes/2.0), latRes);
        latVar.units = "degrees North";
        latVar.long_name = "Latitude";
        latVar.valid_min = -90;
        latVar.valid_max = 90;
        
        lonVar = ncout.createVariable("lon", np.dtype(float), ("lon",) );
        lonVar[:] = np.arange(-180+(lonRes/2.0), 180+(lonRes/2.0), lonRes);
        lonVar.units = "degrees East";
        lonVar.long_name = "Longitude";
        lonVar.valid_min = -180;
        lonVar.valid_max = 180;
       
        var = ncout.createVariable("VCO2", np.dtype(float), ("lat", "lon") );
        #var[:] = np.flip(interpolatedValues, axis=0);
        var[:] = interpolatedValues;
        var.units = "umol mol^-1";
        var.long_name = "NOAA Greenhouse Gas Marine Boundary Layer Reference. Atmospheric VCO2 ";
        var.valid_min = -1000.0;
        var.valid_max = 1000.0;
        ncout.close();
        filesProcessed.append(outputNetCDFPath);

    print "Completed with:\n\t", len(filesProcessed), "monthly file(s) created\n\t", len(filesSkipped), "file(s) skipped to prevent overwriting existing files.\n\tSkipped", len(skippedInputData), "rows in input file which did not match specified temporal period.";



if __name__ == "__main__":
        #parse arguments
    description = unicode("""Processes NOAA ESRL greenhouse gas marine boundary layer reference vCO2 data into monthly averages with a 1.0 by 1.0 degree spatial resolution.
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("stopYear", type=int,
                        help="Stop year (inclusive)), e.g. 1999");
    parser.add_argument("startYear", type=int, default=1981,
                        help="Start year, e.g. 1999. Defaults to 1981.");
    parser.add_argument("inputPath", type=str,
                        help="Path to the input data in text format. This should be the 'surface' data downloaded from https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php for the years of interest.");
    parser.add_argument("--destinationRootDirectory", type=str, default="",
                        help="Path to the root directory where processed output files will be stored. Defaults to the current working directory.");
    clArgs = parser.parse_args();

    #Do the resample
    print "* Processing NOA ESRL marine boundary layer reference vCO2 data.";
    process_esrl_mbl_vco2(clArgs.stopYear, clArgs.startYear, clArgs.inputPath, destinationDir=clArgs.destinationRootDirectory);


