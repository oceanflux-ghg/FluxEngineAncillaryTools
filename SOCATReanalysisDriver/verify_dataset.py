#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:37:36 2019

@author: Tom Holding
Compares different versions of the reanalysed SOCAT data for consistency.
Compares SOCAT reanalysis with consistency to original SOCAT.
"""

import numpy as np;
import matplotlib.pyplot as plt;
import pandas as pd;

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

readDatasets = True; #Switch for debugging

#SOCATv6
originalv6Path = "input_data/SOCATv6/SOCATv6.tsv";
reanalysedv6Path = "output/merged/SOCATv6.tsv";

#SOCATv2019
originalv2019Path = "input_data/SOCATv2019/SOCATv2019.tsv";
reanalysedv2019Path = "output/merged/SOCATv2019.tsv";

print "reading v6 original dataset...";
socatTop = get_socat_header(originalv6Path);
or6 = pd.read_csv(originalv6Path, sep='\t', skiprows=len(socatTop)-1);

print "reading v6 reanalysed dataset...";
re6 = pd.read_csv(reanalysedv6Path, sep='\t');

print "reading v2019 dataset...";
socatTop = get_socat_header(originalv2019Path);
or2019 = pd.read_csv(originalv2019Path, sep='\t', skiprows=len(socatTop)-1);

print "reading v2019 dataset...";
re2019 = pd.read_csv(reanalysedv2019Path, sep='\t');


# for i, key in enumerate(re6.keys()):
#     print i, key, "\n";
# for i, key in enumerate(re2019.keys()):
#     print i, key, "\n";


#Subset to years that aren't overlapping.
print "Difference in number of rows in the reanalysed and original SOCATv6:", len(or6) - len(re6);
print "Difference in number of rows in the reanalysed and original SOCATv2019:", len(or2019) - len(re2019);
#difference between reanalysed old and new datasets
print "Difference in number of rows in SOCATv6 and SOCATv2019:", len(re2019) - len(re6);

#mean fugacities:
print "Mean fugacities:";
print "\tSOCATv6 original:", np.nanmean(or6["fCO2rec [uatm]"]);
print "\tSOCATv6 reanalysed (original):", np.nanmean(re6["fCO2_SST"]);
print "\tSOCATv6 reanalysed (reanalysed):", np.nanmean(re6["fCO2_Tym"]);
print "\tSOCATv2019 original:", np.nanmean(or2019["fCO2rec [uatm]"])
print "\tSOCATv2019 reanalysed (original):", np.nanmean(re2019["fCO2_SST"])
print "\tSOCATv2019 reanalysed (reanalysed):", np.nanmean(re2019["fCO2_Tym"])

print "\nfCO2 difference due to reanalysis (v6):", np.nanmean(re6["fCO2_Tym"])-np.nanmean(or6["fCO2rec [uatm]"]);
print "\nfCO2 difference due to reanalysis (v2019):", np.nanmean(re2019["fCO2_Tym"])-np.nanmean(or2019["fCO2rec [uatm]"]);

#mean temperatures
print "\n\nMean temperatures:";
print "\tSOCATv6 original:", np.nanmean(or6["SST [deg.C]"]);
print "\tSOCATv6 reanalysed (original):", np.nanmean(re6["SST_C"]);
print "\tSOCATv6 reanalysed (reanalysed):", np.nanmean(re6["Tcl_C"]);
print "\tSOCATv2019 original:", np.nanmean(or2019["SST [deg.C]"])
print "\tSOCATv2019 reanalysed (original):", np.nanmean(re2019["SST_C"])
print "\tSOCATv2019 reanalysed (reanalysed):", np.nanmean(re2019["Tcl_C"])

print "\nfCO2 difference due to reanalysis (v6):", np.nanmean(re6["Tcl_C"])-np.nanmean(or6["SST [deg.C]"]);
print "\nfCO2 difference due to reanalysis (v2019):", np.nanmean(re2019["Tcl_C"])-np.nanmean(or2019["SST [deg.C]"]);



# sumDiffTemperature = np.nansum(np.abs(np.array(re1DF["Tsubskin [deg.C]"]) - np.array(re2DF["Tcl_C"])));
# sumDiffFugacity = np.nansum(np.abs(np.array(re1DF["fCO2_reanalysed [uatm]"]) - np.array(re2DF["fCO2_Tym"])));

# diffs = np.abs(np.array(re1DF["fCO2_reanalysed [uatm]"]) - np.array(re2DF["fCO2_Tym"]));
# print len(np.where(diffs != 0.0)[0])
# wfug = np.where((diffs != 0.0) & (np.isfinite(diffs)));
# fugDiffs = pd.DataFrame();
# fugDiffs["yr1"] = re1DF["yr"].iloc[wfug];
# fugDiffs["yr2"] = re2DF["yr"].iloc[wfug];
# fugDiffs["re1Fug"] = re1DF["fCO2_reanalysed [uatm]"].iloc[wfug];
# fugDiffs["re2Fug"] = re2DF["fCO2_Tym"].iloc[wfug];
# fugDiffs["re1OrigT"] = re1DF["SST [deg.C]"].iloc[wfug];
# fugDiffs["re2OrigT"] = re2DF["SST [deg.C]"].iloc[wfug];
# fugDiffs["re1OrigFug"] = re1DF["fCO2rec [uatm]"].iloc[wfug];
# fugDiffs["diff"] = diffs[wfug];





