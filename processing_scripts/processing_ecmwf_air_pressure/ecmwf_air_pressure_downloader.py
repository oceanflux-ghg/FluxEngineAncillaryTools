#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Downloads ECMWF ERA Interim air pressure at mean sea level.
Uses the ECMWF API for python.
Note that:
    Current API key info. This is stored in ~/.ecmwfapirc and will need updating each year.
    {
        "url"   : "https://api.ecmwf.int/v1",
        "key"   : "62d805a84c81dafa0b3f7864448796c8", #Valid until 6 Nov 2019.
        "email" : "t.m.holding@exeter.ac.uk"
    }
and you will need to update this / use your own file if you're running it from another location/computer.

@author: Tom Holding
"""

from __future__ import print_function;
from ecmwfapi import ECMWFDataServer
import os;
from os import path;
from string import Template
import argparse;
import sys

#Current API key info. This is stored in ~/.ecmwfapirc and will need updating each year.
#{
#    "url"   : "https://api.ecmwf.int/v1",
#    "key"   : "62d805a84c81dafa0b3f7864448796c8", #Valid until 6 Nov 2019.
#    "email" : "t.m.holding@exeter.ac.uk"
#}
#API keys can be aquired for free from: https://api.ecmwf.int/v1/key/
def ecmwf_api_call(dateStr, outputFilePath):
    server = ECMWFDataServer()
    server.retrieve({
        "class": "ei",
        "dataset": "interim",
        "date": dateStr, #e.g. "19800101",
        "expver": "1",
        "grid": "1.0/1.0",
        "levtype": "sfc",
        "param": "151.128",
        "stream": "moda",
        "type": "an",
        "format": "netcdf",
        "target": outputFilePath, #e.g. "output_2010_01.nc",
    });



def download_ecmwf_air_pressure(stopYear, stopMonth, startYear=1981, startMonth=6, destinationDir="downloaded_files"):
    notDownloadedError = [];
    notDownloadedSkipped = [];
    downloadedFiles = [];
    outputFilenameTemplate = Template("${YYYY}${MM}01_ECMWF_ERA_Interim_monthly_mean_air_pressure_msl_1.0x1.0.nc");
    
    #Create destination directory
    if path.exists(destinationDir) == False:
        os.mkdirs(destinationDir);
    
    for year in range(startYear, stopYear+1):
        for month in range(1, 13):
            #Ignore months before start month and after end month for first and last year, respectively.
            if year == startYear and month < startMonth:
                continue;
            if year == stopYear and month > stopMonth:
                continue;
            
            monthStr = format(month, "02d");
            outputFilename = outputFilenameTemplate.safe_substitute(YYYY=str(year), MM=monthStr);
            curDestination = path.join(destinationDir, outputFilename);
            
            if path.exists(curDestination) == False:
                print("Downloading:", outputFilename);
                try: #Try to download file
                    ecmwf_api_call(str(year)+monthStr+"01", curDestination);
                    downloadedFiles.append(curDestination);
                    
                except Exception as e: #Tried to download file and it failed
                    print(type(e), e.args);
                    notDownloadedError.append((curDestination, e));
            else: #Skip file, because it already seems to be there...
                notDownloadedSkipped.append(curDestination);
    
    print("Completed with:\n\t", len(downloadedFiles), "file(s) downloaded\n\t", len(notDownloadedError), "file(s) skipped due to error downloading.\n\t", len(notDownloadedSkipped), "file(s) skipped to prevent overwriting existing files.");


if __name__ == "__main__":
    #parse arguments
    description = unicode("""Downloads ECMWF ERA Interim air pressure at mean sea level.
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("stopYear", type=int,
                        help="Stop year, e.g. 1999");
    parser.add_argument("stopMonth", type=int,
                        help="Stop month (numeric), e.g. 1 for January, 12 for December.");
    parser.add_argument("startYear", type=int, default=1981,
                        help="Start year, e.g. 1999. Defaults to 1981.");
    parser.add_argument("startMonth", type=int, default=6,
                        help="Start month (numeric), e.g. 1 for January, 12 for December. Defaults to 6 (June).");
    parser.add_argument("--destinationDir", default="downloaded_files", type=str,
                        help="Destination directory for downloaded files.");
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Downloading ECMWF ERA-Interim data from", clArgs.startMonth, clArgs.startYear, "to", clArgs.stopMonth, clArgs.stopYear);
    download_ecmwf_air_pressure(stopYear=clArgs.stopYear, stopMonth=clArgs.stopMonth, startYear=clArgs.startYear, startMonth=clArgs.startMonth, destinationDir=clArgs.destinationDir);
