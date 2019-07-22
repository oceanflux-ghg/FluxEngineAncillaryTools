#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 09:16:40 2018

Combines individual data files into a single global ascii file.

@author: rr
"""

from os import path;
import os;
import pandas as pd;
import numpy as np;
import argparse;
#from datetime import datetime, timedelta;


#Returns the header portion of a socat ascii file. This included everything before the individual data points:
#   The preamble/description.
#   The expedition table.
#   Post expedition table description.
#   Also includes the header of the individual data points table.
#Returns as a list of strings corresponding to each line.
def get_socat_header(filepath):
    header = [];
    with open(filepath) as SOCAT:
      for preline in SOCAT:
         if 'Expocode' not in preline or 'yr' not in preline:
            header.append(preline);
         else:
            header.append(preline);
            break;
    return header;

#Returns true is both rows match
def is_match(socatRow, reanalysedRow):
    socatLonToUse = socatRow["longitude [dec.deg.E]"];
    if socatLonToUse == 360: #Both 0 and 360 are used in the socat database.
        socatLonToUse = 0;
    if (socatRow["day"] == reanalysedRow["day"]
       and socatRow["hh"] == reanalysedRow["hh"]
       and socatRow["mm"] == reanalysedRow["mm"]
       and socatRow["ss"] == reanalysedRow["ss"]
       #and socatRow["Expocode"] == reanalysedRow["expocode"]
       and np.isclose(socatRow["latitude [dec.deg.N]"], reanalysedRow["lat"], rtol=0, atol=1e-04)
       and np.isclose(socatLonToUse, reanalysedRow["lon"], rtol=0, atol=1e-04)
       and np.isclose(socatRow["fCO2rec [uatm]"], reanalysedRow["fCO2_SST"], rtol=0, atol=1e-04)):
           return True;
    else:
        return False;

##Returns the row in socatMonthSlice (dataframe) which corresponds to the time/date and lon/lat and exposocde of toMatchRow.
##   toMatchRow should be a row from a reanalysed_socat output file
##   socatMonthSlice should be the year-month subset of the original socat data
#def match_row(toMatchRow, socatMonthSlice):
#    lonToMatch = toMatchRow["lon"]; #Differences between the way longitude is stored between the two datasets.
#    
#    matches = socatMonthSlice[#(socatMonthSlice["yr"] == toMatchRow["yr"]) &
#                               #(socatMonthSlice["mon"] == toMatchRow["mon"]) &
#                               (socatMonthSlice["day"] == toMatchRow["day"]) &
#                               (socatMonthSlice["hh"] == toMatchRow["hh"]) &
#                               (socatMonthSlice["mm"] == toMatchRow["mm"]) &
#                               (socatMonthSlice["ss"] == toMatchRow["ss"]) &
#                               #(socatMonthSlice["Expocode"] == toMatchRow["expocode"]) &
#                               (np.isclose(socatMonthSlice["latitude [dec.deg.N]"], toMatchRow["lat"], rtol=0, atol=1e-04)) &
#                               (np.isclose(socatMonthSlice["longitude [dec.deg.E]"], lonToMatch, rtol=0, atol=1e-04)) &
#                               (np.isclose(socatMonthDF["fCO2rec [uatm]"], curMonthDF["fCO2_SST"], rtol=0, atol=1e-04))
#                               ];
#    
#    #print "Matches:", len(matches);
#                              
#    if len(matches) != 1:
#        raise ValueError("There were %d matches for the given row in match_row!"%len(matches));
#    
#    
#    return matches#.iloc[0]; #Return the row which matches 'toMatchRow'

def what_no_match(socatRow, reanalysedRow):
    socatLonToUse = socatRow["longitude [dec.deg.E]"];
    if socatLonToUse == 360:
        socatLonToUse = 0;
    
    if socatRow["day"] != reanalysedRow["day"]:
        return False, "day", "day";
    elif socatRow["hh"] != reanalysedRow["hh"]:
        return False, "hh", "hh";
    elif socatRow["mm"] != reanalysedRow["mm"]:
        return False, "mm", "mm";
    elif socatRow["ss"] != reanalysedRow["ss"]:
        return False, "ss", "ss";
    #elif socatRow["Expocode"] != reanalysedRow["expocode"]:
    #    return False, "Expocode", "expocode";
    elif np.isclose(socatRow["latitude [dec.deg.N]"], reanalysedRow["lat"], rtol=0, atol=1e-04) == False:
        return False, "latitude [dec.deg.N]", "lat";
    elif np.isclose(socatLonToUse, reanalysedRow["lon"], rtol=0, atol=1e-04) == False:
        return False, "longitude [dec.deg.E]", "lon";
    elif np.isclose(socatRow["fCO2rec [uatm]"], reanalysedRow["fCO2_SST"], rtol=0, atol=1e-04) == False:
        return False, "fCO2rec [uatm]", "fCO2_SST";
    else:
        return True, None, None;



##socat6AsciiPath = path.expanduser("~/data/SOCAT_ascii/SOCATv6/SOCATv6.tsv");
##reanalysedAsciiPath = path.expanduser("output_SOCATv6_ascii/output/reanalysed_data");
#socat6AsciiPath = path.expanduser("/home/verwirrt/Desktop/PostDoc/Backup/data/SOCAT_ascii/SOCATv5/SOCATv5.tsv");
#reanalysedAsciiPath = path.expanduser("output_SOCATv5_ascii/output/reanalysed_data");

#newAsciiOutputPath = "socatv5_reanalysed_ascii_from1981_raw.tsv";

#startYr = 1957#1981;
#stopYr = 2018#2018;

#Perform the combination step.
def do_combine_ascii(socatAsciiPath, reanalysisDataDirectory, outputPath, startYr, stopYr):
#socatAsciiPath = "input_data/SOCATv5/SOCATv5_NorthPacific.tsv"
#reanalysisDataDirectory = "output/SOCATv5/output_SOCATv5_ascii_mini/output/reanalysed_data/"
#outputPath = "output/merged/SOCATv5_mini.tsv"
#startYr = 1981
#stopYr = 2017

    #Append ascii files to a single ascii file #
    socatTop = get_socat_header(socatAsciiPath);
    socatDF = pd.read_table(socatAsciiPath, sep='\t', skiprows=len(socatTop)-1);
    socatDF = socatDF[(socatDF["yr"] >= startYr) & (socatDF["yr"] <= stopYr)]; #Only keep relvant years
    socatDF.sort_values(["yr", "mon", "day", "hh", "mm", "ss", "latitude [dec.deg.N]", "longitude [dec.deg.E]", "fCO2rec [uatm]", "SST [deg.C]"], inplace=True);
    print "sorted", socatDF.iloc[0:3].index;
    print socatDF.iloc[0:3][["yr", "mon"]];
    socatDF.reset_index(drop=True); #Recalculates index column to begin with 0 (this is important as index is used later to match rows)
    print "reset", socatDF.iloc[0:3].index;
    
    #define lists containing the new columns
    SST_C = np.empty(len(socatDF)); SST_C[:] = np.nan; #Uncorrected temperature
    Tcl_C = np.empty(len(socatDF)); Tcl_C[:] = np.nan; #Corrected temperature
    fCO2_SST = np.empty(len(socatDF)); fCO2_SST[:] = np.nan; #Uncorrected fCO2
    fCO2_Tym = np.empty(len(socatDF)); fCO2_Tym[:] = np.nan; #Corrected fCO2
    pCO2_SST = np.empty(len(socatDF)); pCO2_SST[:] = np.nan; #Uncorrected pCO2
    pCO2_Tym = np.empty(len(socatDF)); pCO2_Tym[:] = np.nan; #Corrected pCO2
    
    
    
    #totalGenRow = -1;
    numMissingRows = 0;
    #missingRows = [];
    
    numSkipped = 0;
    expectedSkips = [];
    #socatIndex=0;
    
    debugLengths = [];
    debugTotals = [];
    
    monthYearSocatOffset = 0;
    socatIndex = 0;
    for year in range(startYr, stopYr+1):
    #for year in range(1997, 1998):
        for month in range(1, 13):
        #for month in range(1, 13):
            print year, month;
            monthStr = format(month, "02d");
            monthYearFilename = "GL_from_"+str(year)+"_to_"+str(year)+"_"+monthStr+"_v5.txt";
            
            socatMonthDF = socatDF[(socatDF["yr"] == year) & (socatDF["mon"] == month)];
            
            try:
                monthYearPath = path.join(reanalysisDataDirectory, monthStr, monthYearFilename);
                curMonthDF = pd.read_table(monthYearPath, sep=',');
                curMonthDF.loc[curMonthDF["lon"] < 0, "lon"] += 360;
                curMonthDF.sort_values(["yr", "mon", "day", "hh", "mm", "ss", "lat", "lon", "fCO2_SST", "SST_C"], inplace=True);
                
                expectedNumSkips = len(socatMonthDF) - len(curMonthDF);
                numCurMonthSkipped = 0;
                
                #monthYearSocatOffset += socatIndex;
                socatIndex=-1;
                for r in range(0, len(curMonthDF)):
                    socatIndex += 1;
                    while is_match(socatMonthDF.iloc[socatIndex], curMonthDF.iloc[r]) == False:
                        #print "Mismatch at:", r, socatIndex, what_no_match(socatMonthDF.iloc[socatIndex], curMonthDF.iloc[r]);
                        #raise SystemExit();
                        numSkipped += 1;
                        numCurMonthSkipped += 1;
                        socatIndex += 1;
                        if numCurMonthSkipped > expectedNumSkips:
                            raise SystemExit();
                    
                    #print r, socatIndex, socatMonthDF.iloc[socatIndex]["fCO2rec [uatm]"], curMonthDF.iloc[r]["fCO2_SST"];
                    #Populate new columns
                    SST_C[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["SST_C"];
                    Tcl_C[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["Tcl_C"];
                    fCO2_SST[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["fCO2_SST"];
                    fCO2_Tym[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["fCO2_Tym"];
                    pCO2_SST[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["pCO2_SST"];
                    pCO2_Tym[socatIndex+monthYearSocatOffset] = curMonthDF.iloc[r]["pCO2_Tym"];
                
                expectedSkips.append( (expectedNumSkips, numCurMonthSkipped));
                if numCurMonthSkipped != 0:
                    print numCurMonthSkipped, "rows skipped. Expected", expectedNumSkips, "rows to be skipped.";
                monthYearSocatOffset += len(socatMonthDF);
            
            except IOError:
                monthYearSocatOffset += len(socatMonthDF);
                print "Skipping ASCII month "+monthStr+" for year "+str(year)+" because it doesn't exist.";
            print year, month, "length:", len(socatMonthDF), "monthYearSocatOffset =", monthYearSocatOffset;
            debugLengths.append(len(socatMonthDF));
            debugTotals.append(monthYearSocatOffset);
    
    
    newTotal = 0;
    ll = [];
    for i in range(0, len(debugLengths)):
        newTotal += debugLengths[i];
        ll.append( (debugLengths[i], debugTotals[i], newTotal) );
        if newTotal != debugTotals[i]:
            print i, newTotal - debugTotals[i];
    
    
    #curMonthDF.loc[curMonthDF["lon"] <= 0, "lon"] += 360;
    #
    #curMonthDF.iloc[r]["lon"]
    #
    #print curMonthDF.iloc[r];
    #print socatMonthDF.iloc[r];
    #print what_no_match(socatMonthDF.iloc[r], curMonthDF.iloc[r]);
    
    
    
    
    
    #Append columns
    print "Adding columns...";
    socatDF["SST_C"] = SST_C;
    socatDF["Tcl_C"] = Tcl_C;
    socatDF["fCO2_SST"] = fCO2_SST;
    socatDF["fCO2_Tym"] = fCO2_Tym;
    socatDF["pCO2_SST"] = pCO2_SST;
    socatDF["pCO2_Tym"] = pCO2_Tym;
    
    #len(socatDF)
    #Write to file
    if path.exists(path.dirname(outputPath)) == False:
        os.makedirs(path.dirname(outputPath));
    f = open(outputPath, mode='w');
    socatDF.to_csv(f, header=True, index=False, sep="\t", float_format='%.3f');
    f.close();
    
    print "Completed with", numMissingRows, "row(s) missing from the reanalysed data. This is usually due to missing Earth observation data during the reanalysis calculation.";
    
    
    #socatDF = pd.read_table("/home/verwirrt/Desktop/PostDoc/Backup/Files/Tasks/Reanalyse_SOCAT_PANGAEA/Reanalyse_SOCATv5_PANGAEA/socatv5_reanalysed_ascii_from1981_fixed.tsv", sep='\t');
    socatDF = pd.read_table(outputPath, sep='\t');
    
    
    print "Sanity checking...";
    count1=0; count2=0;
    for vi in range(0, len(socatDF)):
        if vi%5000 == 0:
            print vi, "of", len(socatDF);
        if socatDF.iloc[vi]["fCO2rec [uatm]"] != socatDF.iloc[vi]["fCO2_SST"] and np.isnan(socatDF.iloc[vi]["fCO2_SST"]) == False:
            print "fCO2:", vi, socatDF.iloc[vi]["fCO2rec [uatm]"], socatDF.iloc[vi]["fCO2_SST"];
            count1+=1;
        if socatDF.iloc[vi]["SST [deg.C]"] != socatDF.iloc[vi]["SST_C"] and np.isnan(socatDF.iloc[vi]["SST_C"]) == False:
            print "Temp:", vi, socatDF.iloc[vi]["SST [deg.C]"], socatDF.iloc[vi]["SST_C"];
            count2+=1;
    print count1, "fCO2 missmatches and", count2, "Temperature mismatches";
    
    #origDF = pd.read_table("/home/verwirrt/Desktop/PostDoc/Backup/data/SOCAT_ascii/SOCATv5/SOCATv5.tsv", sep='\t', skiprows=len(socatTop));
    origDF = pd.read_table(socatAsciiPath, sep='\t', skiprows=len(socatTop)-1);
    if len(socatDF) == len(origDF):
        print "original and merged dataframes are the same length.";
    else:
        print "original and merged dataframes are NOT the same length.";
        print len(socatDF), "vs", len(origDF);



#print socatDF.iloc[10000000]
#for i in range(0, len(SST_C)):
#    if np.isnan(SST_C[i]) == False:
#        print i,SST_C[i]
    
    
if __name__ == "__main__":
    #parse arguments
    description = unicode("""Combines reanalysed ascii data with SOCAT text ascii data into one file..
    """, 'utf-8');
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("--socatAsciiPath", type=str, default="defaultPath",
                        help="Path to the socat ascii file.");
    parser.add_argument("--reanalysisDataDirectory", type=str, default="defaultPath",
                        help="Path to the data directory containing the reanalysed SOCAT data, e.g. 'output/reanalysed_data/'");
    parser.add_argument("--outputPath", type=str, default="defaultPath",
                        help="Path (and filename) where the merged datasets will be written to.");
    
    parser.add_argument("--startYear", type=int, default=1981,
                        help="Start year, e.g. 1999. Defaults to 1981.");
    parser.add_argument("--stopYear", type=int, default=2000,
                        help="Stop year (inclusive)), e.g. 2000");
    
    clArgs = parser.parse_args();   
    
    #Download files.
    print("* Merging SOCAT and reanalysed SOCAT data from", clArgs.startYear, "to", clArgs.stopYear);
    do_combine_ascii(socatAsciiPath=clArgs.socatAsciiPath, reanalysisDataDirectory=clArgs.reanalysisDataDirectory, outputPath=clArgs.outputPath, startYr=clArgs.startYear, stopYr=clArgs.stopYear);




#--socatAsciiPath input_data/SOCATv5/SOCATv5_NorthPacific.tsv --reanalysisDataDirectory output/SOCATv5/output_SOCATv5_ascii_mini/output/reanalysed_data/ --outputPath output/merged/SOCATv5_mini.tsv --startYear 1981 --stopYear 2017































