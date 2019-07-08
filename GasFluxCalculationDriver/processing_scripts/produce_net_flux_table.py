#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 14:18:51 2019

@author: rr
"""

import pandas as pd;
import argparse;

#inputDataPathUta: multiple linear regression version
#inputDataPathPeter: neural network approach version
def produce_net_flux_table(inputDataPathUta, inputDataPathPeter, outputPath):
    utaInDf = pd.read_table(inputDataPathUta, sep=',');
    annualRowsUta = utaInDf[utaInDf["MONTH"]=="ALL"];
    
    peterInDf = pd.read_table(inputDataPathPeter, sep=',');
    annualRowsPeter = peterInDf[peterInDf["MONTH"]=="ALL"];
    
    outDF = pd.DataFrame();
    outDF["YEAR"] = annualRowsUta["YEAR"];
    outDF["MLR NET FLUX (TgC)"] = annualRowsUta["NET FLUX TgC"];
    outDF["NNA NET FLUX (TgC)"] = annualRowsPeter["NET FLUX TgC"];
    outDF.to_csv(outputPath, sep=',');


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracts annual net flux data from oceanghg-flux-budgets tool for Peter's and Uta's interpolated fCO2 FluxEngine runs.");
    parser.add_argument("inputDataPathUta", default="fe_output/uta_fco2_runs_global.txt", type=str,
                        help="Path to the global oceanghg-flux-budgets tool output for the multiple linear regression approach fCO2 data.");
    parser.add_argument("inputDataPathPeter", type=str, default="fe_output/peter_fco2_runs_global.txt",
                        help="Path to the global oceanghg-flux-budgets tool output for the neural network approach fCO2 data.");
    parser.add_argument("outputPath", type=str, default="fe_output/annual_net_flux.csv",
                        help="Filepath to for the output file (csv to be written).");
    clArgs = parser.parse_args();
    
    print "* Grouping net flux data from MLR and NNA runs...";
    produce_net_flux_table(clArgs.inputDataPathUta, clArgs.inputDataPathPeter, clArgs.outputPath);
    print "\tWritten output file:", clArgs.outputPath;