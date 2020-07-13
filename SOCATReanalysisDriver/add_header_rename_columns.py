#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 09:31:46 2018

@author: rr
"""

import pandas as pd;
import datetime;
import argparse;

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



def do_add_header_rename(reanalysedInputFile, reanalysedOutputFile, socatAsciiFile, additionalHeaderTextFile):
    print("Extracting original SOCAT header");
    header = get_socat_header(socatAsciiFile);
    header = header[0:-1]; #remove column names, because these are no longer accurate for the reanalysed data.
    
    print("Constructing new header");
    with open(additionalHeaderTextFile) as additionalHeader:
        extraHeader = [];
        for line in additionalHeader:
            extraHeader.append(line);
    
    
    
    print("reading input data");
    socatDF = pd.read_table(reanalysedInputFile, sep="\t");
    
    #remove duplicate columns
    print("removing duplicate columns");
    cols = list(socatDF.keys());
    cols.remove("SST_C");
    cols.remove("fCO2_SST");
    socatDF = socatDF[cols];
    
    #rename columns
    print("renaming columns");
    cols[-4] = "T_reynolds [C]";
    cols[-3] = "fCO2_reanalysed [uatm]";
    cols[-2] = "pCO2_SST [uatm]";
    cols[-1] = "pCO2_reanalysed [uatm]";
    socatDF.columns = cols;
    
    #write header
    print("writing header");
    out = open(reanalysedOutputFile, 'w');
    for line in header:
        out.write(line);
    
    out.writelines("Reanalysis conducted: "+str(datetime.datetime.now().date())+"\n\r");
    for line in extraHeader:
        out.write(line);
    
    #write data
    print("writing data");
    socatDF.to_csv(out, sep="\t", index=False, float_format='%.3f', na_rep='NaN');
    out.close();

if __name__ == "__main__":
    #parse arguments
    description = """Adds the original SOCAT header to the top of merged reanalysed SOCAT data. Also adds additional reanalysis-specific section to the header.
    """;
    
    parser = argparse.ArgumentParser(description=description);
    parser.add_argument("--reanalysedInputFile", type=str, default="defaultPath",
                        help="Path to the file containing the merged reanalysed SOCAT dataset.");
    parser.add_argument("--reanalysedOutputFile", type=str, default="defaultPath",
                        help="Path and filename to store the dataset after the header has been added.");
    parser.add_argument("--socatAsciiFile", type=str, default="defaultPath",
                        help="Path to the original SOCAT ASCII data file (used to extract original header).");
    parser.add_argument("--additionalHeaderTextFile", type=str, default="reanalysed_addition_to_header.txt",
                        help="Path to the file containing additional section to add to the header.");

    clArgs = parser.parse_args();   
    print(" * Appending header to copy of data and saving at:", clArgs.reanalysedOutputFile);
    do_add_header_rename(clArgs.reanalysedInputFile, clArgs.reanalysedOutputFile, clArgs.socatAsciiFile, clArgs.additionalHeaderTextFile);

