fluxEngineRoot=$HOME"/Software/FluxEngine/" #Path to the FluxEngine root directory
inputDataPath="input_data/" #Where to find input data
outputDirectory="output/" #Where to store reanalysed and merged output files.

#Specify the directory and file name structure of the Reynolds SST dataset. This is used as the depth-consistent temperature field.
reynoldsSSTRoot="../GasFluxCalculationDriver/data/reynolds_sst/reynolds_avhrr_only_monthly_resampled_1.0x1.0/"
reynoldsSSTTail="01_OCF-SST-GLO-1M-100-REYNOLDS_1.0x1.0.nc" #Tail is the filename without the yyyymm prefix


###################
# Download and process SST Reynolds data - this provides a consistent depth temperature field for the reanalysis calculation
# ***Uncomment section to download and process the Reynolds SST data set***
# sstReynoldsPath="../data/reynolds_sst/" #Path to put downloaded / processed SST data. This should be consistent with those specified above.
# #Download
# python ../processing_scripts/processing_reynolds_sst/reynolds_downloader.py "2019" "12" "1981" "9" --destinationDir $sstReynoldsPath"downloaded_files"
# #Resample
# python ../processing_scripts/processing_reynolds_sst/reynolds_resampler.py "2019" "12" "1981" "9" --lonResolution "1.0" --latResolution "1.0" --sourceTemplate $sstReynoldsPath"downloaded_files/avhrr-only-v2.\${YYYY}\${MM}\${DD}.nc" --destinationRootDirectory $sstReynoldsPath


###################
#Global SOCATv2019 ascii
datasetName="SOCATv2019" #Input data should be in a sub-directory which matched this name.
python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv2019_ascii" -socatversion 6 -usereynolds -startyr 1957 -endyr 2019 -keepduplicates -keeptempfiles -asciioutput
#Merge reanalysed data into original text file.
python combine_ascii.py --socatAsciiPath $inputDataPath$datasetName"/"$datasetName".tsv" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv2019_ascii/output/reanalysed_data/" --outputPath "output/merged/"$datasetName".tsv" --startYear "1981" --stopYear "2019" --suffix="v6"
python add_header_rename_columns.py --reanalysedInputFile "output/merged/"$datasetName".tsv" --reanalysedOutputFile "output/merged/"$datasetName"_with_header.tsv" --socatAsciiFile "input_data/"$datasetName"/"$datasetName".tsv"

#Global SOCATc2019 netCDF
datasetName="SOCATv2019" #Input data should be in a sub-directory which matched this name.
python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv2019_netCDF" -socatversion 6 -usereynolds -startyr 1957 -endyr 2019 -keepduplicates -keeptempfiles
##Merge reanalysed data into original nc file.1
python combine_netcdf.py --socatGridPath $inputDataPath$datasetName"/"$datasetName"_tracks_gridded_monthly.nc" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv2019_netCDF/output/reanalysed_global/" --outputPath "output/merged/"$datasetName".nc" --startYear "1957" --stopYear "2019"



####################################
# Uncomment to run SOCATv6 example
# #Global SOCATv6 ascii
# datasetName="SOCATv6" #Input data should be in a sub-directory which matched this name.
# python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv6_ascii" -socatversion 6 -usereynolds -startyr 1957 -endyr 2018 -keepduplicates -keeptempfiles -asciioutput
#Merge reanalysed data into original text file.
# python combine_ascii.py --socatAsciiPath $inputDataPath$datasetName"/"$datasetName".tsv" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv6_ascii/output/reanalysed_data/" --outputPath "output/merged/"$datasetName".tsv" --startYear "1981" --stopYear "2018"  --suffix="v6"
# python add_header_rename_columns.py --reanalysedInputFile "output/merged/"$datasetName".tsv" --reanalysedOutputFile "output/merged/"$datasetName"_with_header.tsv" --socatAsciiFile "input_data/"$datasetName"/"$datasetName".tsv"

# #Global SOCATv6 netCDF
# datasetName="SOCATv6" #Input data should be in a sub-directory which matched this name.
# python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv6_netCDF" -socatversion 6 -usereynolds -startyr 1957 -endyr 2018 -keepduplicates -keeptempfiles
# #Merge reanalysed data into original nc file.
# python combine_netcdf.py --socatGridPath $inputDataPath$datasetName"/"$datasetName"_tracks_gridded_monthly.nc" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv6_netCDF/output/reanalysed_global/" --outputPath "output/merged/"$datasetName".nc" --startYear "1957" --stopYear "2018"


####################################
# Uncomment to run SOCATv5 example
#Global SOCATv5 ascii
# datasetName="SOCATv5" #Input data should be in a sub-directory which matched this name.
# python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv5_ascii" -socatversion 5 -usereynolds -startyr 1957 -endyr 2018 -keepduplicates -keeptempfiles -asciioutput
#Merge reanalysed data into original text file.
# python combine_ascii.py --socatAsciiPath $inputDataPath$datasetName"/"$datasetName".tsv" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv5_ascii/output/reanalysed_data/" --outputPath "output/merged/"$datasetName".tsv" --startYear "1981" --stopYear "2018"  --suffix="v5"
# python add_header_rename_columns.py --reanalysedInputFile "output/merged/"$datasetName".tsv" --reanalysedOutputFile "output/merged/"$datasetName"_with_header.tsv" --socatAsciiFile "input_data/"$datasetName"/"$datasetName".tsv"

## datasetName="SOCATv5" #Input data should be in a sub-directory which matched this name.
## python $fluxEngineRoot"fluxengine_src/tools/reanalyse_socat_driver.py" -socat_dir $inputDataPath$datasetName"/" -socat_files $datasetName".tsv" -sst_dir $reynoldsSSTRoot -sst_tail $reynoldsSSTTail -output_dir $outputDirectory$datasetName"/output_SOCATv5_netCDF" -socatversion 5 -usereynolds -startyr 1957 -endyr 2018 -keepduplicates -keeptempfiles
## #Merge reanalysed data into original nc file.
## python combine_netcdf.py --socatGridPath $inputDataPath$datasetName"/"$datasetName"_tracks_gridded_monthly.nc" --reanalysisDataDirectory $outputDirectory$datasetName"/output_SOCATv5_netCDF/output/reanalysed_global/" --outputPath "output/merged/"$datasetName".nc" --startYear "1957" --stopYear "2018"
#