#Start and stop dates (inclusive) that control the temporal range that input data will be downloaded for
startYearData="1981"
startMonthData="9" #1=Jan, 12=Dec
stopYearData="2017"
stopMonthData="12" #1=Jan, 12=Dec

#Input data will be resampled to this spatial grid resolution. Not all data sets support other lon/lat resolutions, so change at your own risk!
lonResampleResolution="1.0" #In degrees
latResampleResolution="1.0" #In degrees

#NOAA ESRL marine boundary layer reference vCO2 data must be downloaded manually:
#	This should be downloaded for the required time span.
#	Download the 'surface' dataset in .txt format from: https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php
#	Set first and last (inclusive) years for the temporal range of the data to match, below.
mblInputDataPath="data/mbl_reference_vco2/data/co2_GHGreference.275669481_surface.txt"; #Location of the downloaded data
mblStartYear="1979" #Start year of the NOAA marine boundary layer reference data file (this must match the input data file)
mblStopYear="2018" #Stop year (inclusive) of the NOAA marine boundary layer reference data file (this must match the input data file)


#Interpolated surface ocean fCO2 data
fco2InputMatPath="data/interpolated_aqueous_fco2/fco2_aq_Oct_18_2018.mat" #path to the .mat (matlab) data file containing fCO2(sw) field.
fCO2StartYear="1970" #Year corresponding to the first entry of the 'time' attribute in the .mat file. Month is assumed to be January.


#Path for output data
outputDataPath="output"

#Paths for each input data sources. This determines the location of the downloaded and processed files.
sstReynoldsPath="data/reynolds_sst/"
windu10CCMPPath="data/ccmp_windu10/"
airPressureECMWFPath="data/ecmwf_air_pressure/"
aqueousfCO2Path="data/interpolated_aqueous_fco2/"
salinityWOAPath="data/woa_salinity/"
vco2MBLReferencePath="data/mbl_reference_vco2/"



#FluxEngine paths, arguments and configuration files
fluxEnginePath=$HOME"/Software/FluxEngine/" #Path to the FluxEngine toolbox's root directory
fluxEngineRunStartYear="1991" #First year to run FluxEngine for data
fluxEngineRunEndYear="2015" #Last year to run FluxEngine for (inclusive)
configPathMLR="configs/mlr_run.conf" #configuration file for the multiple linear regression approach run
configPathNNA="configs/nna_run.conf" #configuration file for the neural network approach run


##########################################
#Download and resample Reynolds SST data #
##########################################
#Download
python processing_scripts/processing_reynolds_sst/reynolds_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir $sstReynoldsPath"downloaded_files"
#Resample
python processing_scripts/processing_reynolds_sst/reynolds_resampler.py $stopYearData $stopMonthData $startYearData $startMonthData --lonResolution $lonResampleResolution --latResolution $latResampleResolution --sourceTemplate $sstReynoldsPath"downloaded_files/oisst-avhrr-v02r01.\${YYYY}\${MM}\${DD}.nc" $sstReynoldsPath"downloaded_files/avhrr-only-v2.\${YYYY}\${MM}\${DD}.nc" --destinationRootDirectory $sstReynoldsPath


#############################################
#Download and resample CCMP wind speed data #
#############################################
#Download
python processing_scripts/processing_ccmp_windu10/ccmp_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir $windu10CCMPPath"downloaded_files"
#Resample
python processing_scripts/processing_ccmp_windu10/ccmp_resampler.py $stopYearData $stopMonthData $startYearData $startMonthData --lonResolution $lonResampleResolution --latResolution $latResampleResolution  --sourceTemplate $windu10CCMPPath"downloaded_files/CCMP_Wind_Analysis_\${YYYY}\${MM}_V02.0_L3.5_RSS.nc" --destinationRootDirectory $windu10CCMPPath

################################################
#Download and resample ECMWF air pressure data #
################################################
#Download. Note that there is no need to further process this data because the ECMWF API is used to download the data in the correct format / resolution.
python processing_scripts/processing_ecmwf_air_pressure/ecmwf_air_pressure_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir $airPressureECMWFPath"downloaded_files"


#################################################
#Download and resample SMOS/MIRAS salinity data #
#################################################
#Download
python processing_scripts/processing_woa_salinity/woa_salinity_downloader.py --destinationDir $salinityWOAPath"downloaded_files"
#Process (to extract just the top depth)
python processing_scripts/processing_woa_salinity/process_woa_salinity.py --sourceTemplate $salinityWOAPath"downloaded_files/woa18_decav_s\${MM}_01.nc" --destinationRootDirectory $salinityWOAPath


###################################
# Process NOAA ESRL MBL vCO2 data #
###################################
# Process vCO2 data from the NOAA ESRL marine boundary layer reference to a FluxEngine compatible format.
# This must be downloaded manually from https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php
# and the 'mblInputDataPath' set accordingly (at the top of this script)
python processing_scripts/processing_mbl_reference_vco2/process_mbl_reference_vco2.py $mblStopYear $mblStartYear $mblInputDataPath --destinationRootDirectory $vco2MBLReferencePath"noaa_esrl_mbl_reflayer_vCO2"



###################################################################################
# Convert CO2 data from matlab .mat format to FluxEngine compatible netCDF format #
###################################################################################
python processing_scripts/processing_aqueous_fco2/matfile_to_netCDF.py $fco2InputMatPath $aqueousfCO2Path"netCDF/\${YYYY}\${MM}_watson_fco2.nc" --startYear $fCO2StartYear



#################################################################################
# Run FluxEngine with data derived from the multiple linear regression approach #
#################################################################################
#Multiple linear regression data time span: 1994, 2017
echo "Running FluxEngine with fCO2 data derived from the multiple linear regression approach"
python $fluxEnginePath"ofluxghg_run.py" $configPathMLR -s $fluxEngineRunStartYear -e $fluxEngineRunEndYear -l


#####################################################################
# Run FluxEngine with data derived from the neural network approach #
#####################################################################
echo "Running FluxEngine with fCO2 data derived from the neural network approach"
python $fluxEnginePath"ofluxghg_run.py" $configPathNNA -s $fluxEngineRunStartYear -e $fluxEngineRunEndYear -l


###########################
# Calculate global fluxes #
###########################
#Note that the '~' (tilda) 'home' token is not parsed correctly by ofluxghg_flux_budgets and cannot be used.
echo "Calculating net flux/budgets for the multiple linear regression fCO2 run"
python ~/Software/FluxEngine/fluxengine_src/tools/ofluxghg_flux_budgets.py --dir "output/mlr_fco2_runs" --outroot "output/mlr_fco2_runs" --maskfile $fluxEnginePath"data/World_Seas-final-complete_IGA.nc" --landfile $fluxEnginePath"data/onedeg_land.nc"


echo "Calculating net flux/budgets for the neural network approach fCO2 run"
python ~/Software/FluxEngine/fluxengine_src/tools/ofluxghg_flux_budgets.py --dir "output/nna_fco2_runs" --outroot "output/nna_fco2_runs" --maskfile $fluxEnginePath"data/World_Seas-final-complete_IGA.nc" --landfile $fluxEnginePath"data/onedeg_land.nc"

#Group annual net flux data for each run
python processing_scripts/produce_net_flux_table.py "output/mlr_fco2_runs_global.txt" "output/nna_fco2_runs_global.txt" "output/annual_net_flux.csv"


echo ""
echo "Finished! FluxEngine output files net CO2 flux budget calculations have been stored in "$(pwd)"/output"
