#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 16:07:08 2018

Download NOAA World Ocean Atland salinity data 'decav' (climate normal) data at 1x1 degree resolution for each month.
Data description: https://data.nodc.noaa.gov/woa/WOA18/DOC/woa18documentation.pdf

@author: Tom Holding
"""

from __future__ import print_function;
import os;
from os import path;
import urllib;
import ssl;
from string import Template
import argparse;

#https://data.nodc.noaa.gov/woa/WOA18/DATA/salinity/netcdf/decav/1.00/
#woa18_decav_s${MM}_01.nc   s00=Annual, S01=Jan, S12=Dec, S13="Winter", S16="Autumn": https://www.nodc.noaa.gov/cgi-bin/OC5/woa18/woa18.pl
def download_woa_salinity(destinationDir="downloaded_files", sourceTemplate=Template("https://data.nodc.noaa.gov/woa/WOA18/DATA/salinity/netcdf/decav/1.00/woa18_decav_s${MM}_01.nc"), months=range(1,13)):
    notDownloadedError = [];
    notDownloadedSkipped = [];
    downloadedFiles = [];
    
    #Create destination directory
    if path.exists(destinationDir) == False:
        os.makedirs(destinationDir);
    
    sslContext = ssl._create_unverified_context(); #Ignore SSL verification (shttp)
    #urlOpener = urllib.URLopener(); #http
    for month in months:
        monthStr = format(month, "02d");
        url = sourceTemplate.safe_substitute(MM=monthStr);            
        
        curDestination = path.join(destinationDir, path.basename(url)); #Append filename to the destination dir to create the download path
        if path.exists(curDestination) == False:
            print("Downloading:", path.basename(url));
            try: #Try to download file
                #urlOpener.retrieve(url, filename=curDestination);
                urllib.urlretrieve(url, filename=curDestination, context=sslContext);
                downloadedFiles.append(url);
                
            except Exception as e: #Tried to download file and it failed
                print("Could not download data for month", monthStr+".", "Reason:", e.args);
                notDownloadedError.append((url, e));
        else: #Skip file, because it already seems to be there...
            notDownloadedSkipped.append(url);
    
    print("Completed with:\n\t", len(downloadedFiles), "file(s) downloaded\n\t", len(notDownloadedError), "file(s) skipped due to error downloading.\n\t", len(notDownloadedSkipped), "file(s) skipped to prevent overwriting existing files.");


if __name__ == "__main__":
    #parse arguments
    description = unicode("""Downloads WOA salinity data.
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("--months", nargs="+", default=range(1,13), type=list,
                        help="List of months to be downloaded (1=Jan, 12=Dec). Defaults to all months");
    parser.add_argument("--destinationDir", default="downloaded_files", type=str,
                        help="Destination directory for downloaded files.");
    parser.add_argument("--sourceTemplate", type=str, default="https://data.nodc.noaa.gov/woa/WOA18/DATA/salinity/netcdf/decav/1.00/woa18_decav_s${MM}_01.nc",
                        help="String 'template' for the online download location. The file should be specified using ${YYYY}, ${MM} and ${DD} for year, month and day, respectively.");
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Downloading WOA salinity data from", clArgs.sourceTemplate);
    download_woa_salinity(destinationDir=clArgs.destinationDir, sourceTemplate=Template(clArgs.sourceTemplate), months=clArgs.months);
