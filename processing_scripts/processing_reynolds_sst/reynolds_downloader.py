#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 16:07:08 2018

@author: Tom Holding
"""

from __future__ import print_function;
import os;
from os import path;
import urllib;
import calendar;
import ssl;
from string import Template
import argparse;

#https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/201701/
#avhrr-only/201504/avhrr-only-v2.20150401.nc
#wget -r -A.nc https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/201601/


def download_reynolds_avhrr_sst(stopYear, stopMonth, startYear=1981, startMonth=6, destinationDir="downloaded_files", sourceTemplate=Template("https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/${YYYY}${MM}/avhrr-only-v2.${YYYY}${MM}${DD}.nc")):
    notDownloadedError = [];
    notDownloadedSkipped = [];
    downloadedFiles = [];
    
    #Create destination directory
    if path.exists(destinationDir) == False:
        os.makedirs(destinationDir);
    
    sslContext = ssl._create_unverified_context(); #Ignore SSL verification
    for year in range(startYear, stopYear+1):
        for month in range(1, 13):
            #Ignore months before start month and after end month for first and last year, respectively.
            if year == startYear and month < startMonth:
                continue;
            if year == stopYear and month > stopMonth:
                continue;
            
            monthStr = format(month, "02d");
            for day in range(1, calendar.monthrange(year, month)[1]+1):
                dayStr = format(day, "02d");
                url = sourceTemplate.safe_substitute(YYYY=str(year), MM=monthStr, DD=dayStr);
                
                curDestination = path.join(destinationDir, path.basename(url));
                if path.exists(curDestination) == False:
                    print("Downloading:", path.basename(url));
                    try: #Try to download file
                        urllib.urlretrieve(url, filename=curDestination, context=sslContext);
                        downloadedFiles.append(url);
                        
                    except Exception as e: #Tried to download file and it failed
                        pass;
                        print(type(e), e.args);
                        notDownloadedError.append((url, e));
                else: #Skip file, because it already seems to be there...
                    notDownloadedSkipped.append(url);
    
    print("Completed with:\n\t", len(downloadedFiles), "file(s) downloaded\n\t", len(notDownloadedError), "file(s) skipped due to error downloading.\n\t", len(notDownloadedSkipped), "file(s) skipped to prevent overwriting existing files.");


if __name__ == "__main__":
    #parse arguments
    description = unicode("""Downloads Reynolds AVHRR daily SST data between two dates.
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
    parser.add_argument("--sourceTemplate", type=str, default="https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/${YYYY}${MM}/avhrr-only-v2.${YYYY}${MM}${DD}.nc",
                        help="String 'template' for the online download location. The file should be specified using ${YYYY}, ${MM} and ${DD} for year, month and day, respectively.");
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Downloading Reynolds data from", clArgs.startMonth, clArgs.startYear, "to", clArgs.stopMonth, clArgs.stopYear);
    download_reynolds_avhrr_sst(stopYear=clArgs.stopYear, stopMonth=clArgs.stopMonth, startYear=clArgs.startYear, startMonth=clArgs.startMonth, destinationDir=clArgs.destinationDir, sourceTemplate=Template(clArgs.sourceTemplate));
