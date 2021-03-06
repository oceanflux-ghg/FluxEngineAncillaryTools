#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 16:07:08 2018

Download CCMP v2.0 monthly meaned data

@author: Tom Holding
"""

from __future__ import print_function;
import os;
from os import path;
import urllib;
from string import Template
import argparse;

#http://data.remss.com/ccmp/v02.0/Y1987/M07/
#CCMP_Wind_Analysis_19870710_V02.0_L3.0_RSS.nc
def download_ccmp2_windu10(stopYear, stopMonth, startYear=1981, startMonth=6, destinationDir="downloaded_files", sourceTemplate=Template("http://data.remss.com/ccmp/v02.0/Y${YYYY}/M${MM}/CCMP_Wind_Analysis_${YYYY}${MM}_V02.0_L3.5_RSS.nc")):
    if startYear < 1987:
        print("Setting start year to 1987 because there is no data before this.");
        startYear = 1987
    if (startYear == 1987) and (startMonth < 8):
        print("Setting start month to August (8) which is the first full month of data in 1987");
        startMonth = 8;
    
    notDownloadedError = [];
    notDownloadedSkipped = [];
    downloadedFiles = [];
    
    #Create destination directory
    if path.exists(destinationDir) == False:
        os.makedirs(destinationDir);
    
    #sslContext = ssl._create_unverified_context(); #Ignore SSL verification (shttp)
    urlOpener = urllib.URLopener(); #http
    for year in range(startYear, stopYear+1):
        for month in range(1, 13):
            #Ignore months before start month and after end month for first and last year, respectively.
            if year == startYear and month < startMonth:
                continue;
            if year == stopYear and month > stopMonth:
                continue;
            
            monthStr = format(month, "02d");
            url = sourceTemplate.safe_substitute(YYYY=str(year), MM=monthStr);            
            
            curDestination = path.join(destinationDir, path.basename(url)); #Append filename to the destination dir to create the download path
            if path.exists(curDestination) == False:
                print("Downloading:", path.basename(url));
                try: #Try to download file
                    urlOpener.retrieve(url, filename=curDestination);
                    #urllib.urlretrieve(url, filename=curDestination, context=sslContext);
                    downloadedFiles.append(url);
                    
                except Exception as e: #Tried to download file and it failed
                    print("Could not download", year, monthStr+".", "Reason:", e.args);
                    notDownloadedError.append((url, e));
            else: #Skip file, because it already seems to be there...
                notDownloadedSkipped.append(url);
    
    print("Completed with:\n\t", len(downloadedFiles), "file(s) downloaded\n\t", len(notDownloadedError), "file(s) skipped due to error downloading.\n\t", len(notDownloadedSkipped), "file(s) skipped to prevent overwriting existing files.");


if __name__ == "__main__":
    #parse arguments
    description = unicode("""Downloads CCMPv2 wind speed data between two dates.
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
    parser.add_argument("--sourceTemplate", type=str, default="http://data.remss.com/ccmp/v02.0/Y${YYYY}/M${MM}/CCMP_Wind_Analysis_${YYYY}${MM}_V02.0_L3.5_RSS.nc",
                        help="String 'template' for the online download location. The file should be specified using ${YYYY}, ${MM} and ${DD} for year, month and day, respectively.");
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Downloading CCMPv2 data from", clArgs.startMonth, clArgs.startYear, "to", clArgs.stopMonth, clArgs.stopYear);
    download_ccmp2_windu10(stopYear=clArgs.stopYear, stopMonth=clArgs.stopMonth, startYear=clArgs.startYear, startMonth=clArgs.startMonth, destinationDir=clArgs.destinationDir, sourceTemplate=Template(clArgs.sourceTemplate));
