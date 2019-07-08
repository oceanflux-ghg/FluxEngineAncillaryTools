#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 16:51:12 2018

@author: rr
"""

from __future__ import print_function;
from scipy.io import loadmat;
from netCDF4 import Dataset;
import numpy as np;
import argparse;
from os import path;
from os import makedirs;
from string import Template;

def create_monthly_netCDF(fCO2DataPeter, fCO2DataUta, outputFilePath, timeStep):
    if path.exists(path.dirname(outputFilePath)) == False:
        makedirs(path.dirname(outputFilePath));
    
    ncout = Dataset(outputFilePath, 'w');
    ncout.createDimension('time', 1);
    ncout.createDimension('lat', 180);
    ncout.createDimension('lon', 360);
    
    timeVar = ncout.createVariable("time", np.dtype(float), ("time",) );
    timeVar[:] = timeStep;
    timeVar.units = "days";
    timeVar.long_name = "Days since 1st Jan 0AD";
    timeVar.valid_min = 0;
    timeVar.valid_max = 999999999;
    
    latVar = ncout.createVariable("lat", np.dtype(float), ("lat",) );
    latVar[:] = lat;
    latVar.units = "degrees North";
    latVar.long_name = "Latitude";
    latVar.valid_min = -90;
    latVar.valid_max = 90;
    
    lonVar = ncout.createVariable("lon", np.dtype(float), ("lon",) );
    lonVar[:] = lon;
    lonVar.units = "degrees East";
    lonVar.long_name = "Longitude";
    lonVar.valid_min = -180;
    lonVar.valid_max = 180;
    
    pData = ncout.createVariable("fCO2_NNA", np.dtype(float), ("time", "lat", "lon") );
    pData[:] = fCO2DataPeter;
    pData.units = "umol/mol ???";
    pData.long_name = "subskin fCO2 produced by the neural network method";
    pData.valid_min = 0.0;
    pData.valid_max = 10000.0;
    
    uData = ncout.createVariable("fCO2_MLR", np.dtype(float), ("time", "lat", "lon") );
    uData[:] = fCO2DataUta;
    uData.units = "umol/mol ???";
    uData.long_name = "subskin fCO2 produced by the multiple linear regression method";
    uData.valid_min = 0.0;
    uData.valid_max = 10000.0;
    
    ncout.close();
    


#Parse commandline arguments
description = unicode("Converts Uta and Peter's data (provided by Andy Watson in .mat format) to a FluxEngine compatible netCDF file.", 'utf-8');
parser = argparse.ArgumentParser(description=description);
parser.add_argument("inputFilepath", type=str, default="Jamie_Oct_18_2018.mat",
                    help="input .mat data file");
parser.add_argument("outputFileTemplate", type=str, default="netCDF/${YYYY}${MM}_watson_fco2.nc",
                    help="output .nc file string 'template'. Use ${YYYY} and ${MM} to specify year and month, respectively");
parser.add_argument("--startYear", type=int, default=1970,
                    help="First year covered in the .mat data file's 'time' field.");
clArgs = parser.parse_args();

inputFilepath = clArgs.inputFilepath;
outputFileTemplate = Template(clArgs.outputFileTemplate);
startYear = clArgs.startYear;
#inputFilepath = "Jamie_Oct_18_2018.mat";
#outputFileTemplate = Template("netCDF/${YYYY}${MM}_watson_fco2.nc");
#startYear = 1970;
print("* Converting fCO2 matlab file format: ", inputFilepath, "to netCDF format.");

#load input data
mat = loadmat(inputFilepath);

lon = mat["lon"]; #1 deg res
lat = mat["lat"]; #1 deg res
time = mat["time"]; #1970 to 2015 (inclusive). Time is days since 0AD
peter = mat["p_data"]; #1993-2016
uta = mat["u_data"]; #1994-2017

#Append some blank arrays to the start if they are not the same length as time
if len(peter) != len(time):
    newPeter = np.empty((len(time), peter.shape[1], peter.shape[2]));
    newPeter[:] = np.nan;
    newPeter[(len(time)-len(peter)):, :, :] = peter;
    peter = newPeter;
    del newPeter;
if len(uta) != len(time):
    newUta = np.empty((len(time), uta.shape[1], uta.shape[2]));
    newUta[:] = np.nan;
    newUta[(len(time)-len(uta)):, :, :] = uta;
    uta = newUta;
    del newUta;

#plot to check
#plt.imshow(peter[200, :, :]);
#plt.colorbar(); plt.clim(0, 500);

def incr_month(year, month):
    month += 1;
    if month > 12:
        month = 1;
        year += 1;
    return year, month;

#Create and write netCDF file.
writtenFiles = [];
skippedFiles = [];
noDataMonths = [];

curYear = startYear;
curMonth = 1;
for i in range(0, len(time)):
    monthStr = format(curMonth, "02d");
    outputFilePath = outputFileTemplate.safe_substitute(YYYY=str(curYear), MM=monthStr);
    
    #Make the directory if it doesn't already exist
    if path.exists(path.dirname(outputFilePath)) == False:
        makedirs(path.dirname(outputFilePath));
    
    if path.exists(outputFilePath):
        skippedFiles.append(outputFilePath);
        curYear, curMonth = incr_month(curYear, curMonth);
        continue;
    
    peterSlice = peter[i,:,:];
    utaSlice = uta[i,:,:];
    if np.any(np.isnan(peterSlice)==False) or np.any(np.isnan(utaSlice)==False):
        print("Writing netCDF file:", path.basename(outputFilePath));
        create_monthly_netCDF(peterSlice, utaSlice, outputFilePath, time[i])
        writtenFiles.append(outputFilePath);
    else: #There's no data so don't bother making a file
        #print("No data found for year/month:", curYear, curMonth);
        noDataMonths.append((curYear, curMonth));
    
    curYear, curMonth = incr_month(curYear, curMonth);

print("Completed with:\n\t", len(writtenFiles), "file(s) converted\n\t", len(skippedFiles), "file(s) skipped to prevent overwriting existing files.\n\t", len(noDataMonths), "file(s) were not created because data did not exist for these months.");
#    ncout = Dataset(outputFilepath, 'w');
#    ncout.createDimension('time', len(time));
#    ncout.createDimension('lat', 180);
#    ncout.createDimension('lon', 360);
#    
#    timeVar = ncout.createVariable("time", np.dtype(float), ("time",) );
#    timeVar[:] = time;
#    timeVar.units = "days";
#    timeVar.long_name = "Days since 1st Jan 0AD";
#    timeVar.valid_min = 0;
#    timeVar.valid_max = 999999999;
#    
#    latVar = ncout.createVariable("lat", np.dtype(float), ("lat",) );
#    latVar[:] = lat;
#    latVar.units = "degrees North";
#    latVar.long_name = "Latitude";
#    latVar.valid_min = -90;
#    latVar.valid_max = 90;
#    
#    lonVar = ncout.createVariable("lon", np.dtype(float), ("lon",) );
#    lonVar[:] = lon;
#    lonVar.units = "degrees East";
#    lonVar.long_name = "Longitude";
#    lonVar.valid_min = -180;
#    lonVar.valid_max = 180;
#    
#    pData = ncout.createVariable("fCO2_peter", np.dtype(float), ("time", "lat", "lon") );
#    pData[(552-444):552,:,:] = peter;
#    pData.units = "umol/mol ???";
#    pData.long_name = "subskin fCO2";
#    pData.valid_min = 0.0;
#    pData.valid_max = 10000.0;
#    
#    uData = ncout.createVariable("fCO2_uta", np.dtype(float), ("time", "lat", "lon") );
#    uData[:] = uta;
#    uData.units = "umol/mol ???";
#    uData.long_name = "subskin fCO2";
#    uData.valid_min = 0.0;
#    uData.valid_max = 10000.0;
#    
#    ncout.close();
#    print("Successfully written", outputFilepath);





