#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 09:16:40 2018

Combines individual data files into a single global netCDF containing original SOCAT data and reanalysed data.

@author: rr
"""

from os import path;
import os;
import numpy as np;
from netCDF4 import Dataset;
from datetime import datetime;
import argparse;


def copy_netcdf(inNC, outNC):
    # copy global attributes all at once via dictionary
    outNC.setncatts({"SOCAT_"+k:inNC.__dict__[k] for k in inNC.__dict__});
    #copy dimensions
    for name, dimension in inNC.dimensions.items():
        print("Copying SOCAT dimension", name);
        outNC.createDimension(name, (len(dimension) if not dimension.isunlimited() else None));
    
    #copy all file data except for the excluded
    for name, variable in inNC.variables.items():
        print("Copying SOCAT variable", name);
        outNC.createVariable(name, variable.datatype, variable.dimensions);
        #Copy variable attributes
        outNC[name].setncatts(inNC[name].__dict__);
        outNC[name][:] = inNC[name][:];


#Calculates the time index from month and year.
def calc_time_index(year, month):
    return (year-1970)*12 + month - 1;


def do_combine_netcdf(socatGridPath, reanalysisDataDirectory, outputPath, startYr, stopYr):
#socatGridPath = path.expanduser("~/data/SOCAT_gridded/SOCATv5/SOCATv5_tracks_gridded_monthly.nc");
#reanalysedGridPath = path.expanduser("output_SOCATv5_netCDF/output/reanalysed_global");
#yearStart = 1970;
#yearEnd = 2017; #inclusive

    #Create a new netCDF file.
    #timeDimensionLength = calc_time_index(yearEnd, 12);
    if path.exists(path.dirname(outputPath)) == False:
        os.makedirs(path.dirname(outputPath));
    combinedNC = Dataset(outputPath, 'w');
    
    #Copy the original SOCAT data into the new file.
    socatNC = Dataset(socatGridPath, 'r');
    copy_netcdf(socatNC, combinedNC);
    
    
    ##dictionary mapping old (reanalyse_socat output) variable names to new variable (in keeping with socat naming scheme) names
    oldToNewMap = {};
    oldToNewMap["count_ncruise"] = "count_ncruise_reanalysed";
    oldToNewMap["count_nobs"] = "count_nobs_reanalysed";
    #oldToNewMap["max_fCO2_SST"] = "fco2_max"; #SOCAT uses 'fco2_max_unwtd' and has no unweighted version. It is the same for weighted and unweighted, so this has been renamed
    oldToNewMap["max_fCO2_Tym"] = "fco2_reanalysed_max";
    #oldToNewMap["max_pCO2_SST"] = "pco2_max";
    oldToNewMap["max_pCO2_Tym"] = "pco2_reanalysed_max";
    #oldToNewMap["min_fCO2_SST"] = "fco2_min";
    oldToNewMap["min_fCO2_Tym"] = "fco2_reanalysed_min";
    #oldToNewMap["min_pCO2_SST"] = "pco2_min";
    oldToNewMap["min_pCO2_Tym"] = "pco2_reanalysed_min";
    #oldToNewMap["stdev_fCO2_SST"] = "fco2_std_weighted";
    oldToNewMap["stdev_fCO2_Tym"] = "fco2_reanalysed_std_weighted";
    #oldToNewMap["stdev_pCO2_SST"] = "pco2_std_weighted";
    oldToNewMap["stdev_pCO2_Tym"] = "pco2_reanalysed_std_weighted";
    #oldToNewMap["unweighted_fCO2_SST"] = "fco2_ave_unwtd";
    oldToNewMap["unweighted_fCO2_Tym"] = "fco2_reanalysed_ave_unwtd";
    #oldToNewMap["unweighted_pCO2_SST"] = "pco2_ave_unwtd";
    oldToNewMap["unweighted_pCO2_Tym"] = "pco2_reanalysed_ave_unwtd";
    #oldToNewMap["unweighted_std_fCO2_SST"] = "fco2_std_unwtd";
    oldToNewMap["unweighted_std_fCO2_Tym"] = "fco2_reanalysed_std_unwtd";
    #oldToNewMap["unweighted_std_pCO2_SST"] = "pco2_std_unwtd";
    oldToNewMap["unweighted_std_pCO2_Tym"] = "pco2_reanalysed_std_unwtd";
    #oldToNewMap["weighted_fCO2_SST"] = "fco2_ave_weighted";
    oldToNewMap["weighted_fCO2_Tym"] = "fco2_reanalysed_ave_weighted";
    #oldToNewMap["weighted_pCO2_SST"] = "pco2_ave_weighted";
    oldToNewMap["weighted_pCO2_Tym"] = "pco2_reanalysed_ave_weighted";
    oldToNewMap["weighted_dfCO2"] = "weighted_dfco2";
    oldToNewMap["weighted_dpCO2"] = "weighted_dpco2";
    oldToNewMap["weighted_dT"] = "weighted_dT";
    
    #Iterate through each reanslyse_socat output file appending them to the combinedNC.
    first = True; #Used to prompt copy of additional variables.
    for year in range(startYr, stopYr):
        for month in range(1, 13):
            #Read NC file for this month
            monthStr = format(month, "02d");
            monthYearFilename = str(year)+monthStr+"01-OCF-CO2-GLO-1M-100-SOCAT-CONV.nc";
            monthYearPath = path.join(reanalysisDataDirectory, monthStr, monthYearFilename);
            
            #Try to open the file
            try:
                monthlyNC = Dataset(monthYearPath, 'r');
                if first == True: #Create the required variables when we first encounter a monthly dataset.
                    for oldVarname in oldToNewMap.keys():
                        oldVar = monthlyNC.variables[oldVarname];
                        try:
                            newVar = combinedNC.createVariable(oldToNewMap[oldVarname], oldVar.dtype, (u"tmnth", u"ylat", u"xlon"));
                            print("Appending variable metadata:", oldVarname, newVar.name);
                            newVar.setncatts({k: oldVar.getncattr(k) for k in oldVar.ncattrs()}); # Copy variable attributes
                        except RuntimeError as e:
                            print(e, "\nOld name:", oldVarname, "\nNew name: "+oldToNewMap[oldVarname]);
                            raise SystemExit();
                            
                    first = False;
                
                #Append data to the correct point in time
                newNCTimeIndex = calc_time_index(year, month);# - timeOffset;
                print("Adding reanalysed slice:", newNCTimeIndex, year, month);
                for monthlyNCVar in oldToNewMap.keys():
                    newNCVar = oldToNewMap[monthlyNCVar];
                    combinedNC.variables[newNCVar][newNCTimeIndex,:,:] = np.flipud(monthlyNC.variables[monthlyNCVar][0,:,:]);
                
            except IOError as e:
                print("Skipping netCDF month "+monthStr+" for year "+str(year)+" because it doesn't exist:", monthYearPath);
    
    
    #(Re)Calculate and add reynolds SST to the netCDF file
    if ("sst_ave_weighted" in combinedNC.variables.keys()): #Early versions of the SOCAT dataset don't include the temperature data in the NC files.
        combinedNC.createVariable("sst_reynolds", np.float32, ("tmnth", "ylat", "xlon"));
        #combinedNC["sst_reynolds"].setncatts(combinedNC["weighted_dT"].__dict__);
        combinedNC["sst_reynolds"].standard_name = "sst_reynolds";
        combinedNC["sst_reynolds"].long_name = "Mean sea surface temperature at a consistent-depth from the Reynolds OISST field.";
        combinedNC["sst_reynolds"][:] = combinedNC["weighted_dT"][:] + combinedNC["sst_ave_weighted"][:];

    
    
    #Copy over important attributes
    currentAtts = combinedNC.__dict__;
    
    currentAtts["Reanalysed_history"] = "Reanalysed " + datetime.now().strftime("%B %d, %Y");
    currentAtts["title"] = currentAtts["SOCAT_title"] + ". Additional variables added for reanalysed data (to consistent temperature and depth).";
    combinedNC.setncatts(currentAtts);
    combinedNC.close();


########################################
# Append nc files to a single nc file. #
########################################

#Copy some metadata from the official SOCATv6 netCDF.
#varsToCopy = [u"tmnth", u"tmnth_bnds", u"xlon", u"ylat"];
#socatNC = Dataset(socatGridPath, 'r');
#for curVar in varsToCopy:
#    originalVar = socatNC.variables[curVar];
#    newVar = newNC.createVariable(curVar, originalVar.datatype, originalVar.dimensions);
#    newVar.setncatts({k: originalVar.getncattr(k) for k in originalVar.ncattrs()}) # Copy variable attributes
#    
#    if u"tmnth" not in originalVar.dimensions:
#        newVar[:] = originalVar[:]; #copy data
#    else:
#        newVar[:] = originalVar[-timeDimensionLength:]; #We're working with a reduced timeseries (limited be EO data).



if __name__ == "__main__":
    #parse arguments
    description = """Downloads CCMPv2 wind speed data between two dates.
    """;
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("--socatGridPath", type=str, default="defaultPath",
                        help="Path to the socat netCDF file.");
    parser.add_argument("--reanalysisDataDirectory", type=str, default="defaultPath",
                        help="Path to the data directory containing the reanalysed SOCAT data, e.g. 'output/reanalysed_global/'");
    parser.add_argument("--outputPath", type=str, default="defaultPath",
                        help="Path (and filename) where the merged datasets will be written to.");
    
    parser.add_argument("--startYear", type=int, default=1981,
                        help="Start year, e.g. 1999. Defaults to 1981.");
    parser.add_argument("--stopYear", type=int, default=2000,
                        help="Stop year (inclusive)), e.g. 2000");
    
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Merging SOCAT and reanalysed SOCAT data from", clArgs.startYear, "to", clArgs.stopYear);
    do_combine_netcdf(socatGridPath=clArgs.socatGridPath, reanalysisDataDirectory=clArgs.reanalysisDataDirectory, outputPath=clArgs.outputPath, startYr=clArgs.startYear, stopYr=clArgs.stopYear);


















