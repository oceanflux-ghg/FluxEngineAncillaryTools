#Start and stop dates (inclusive) that control the temporal range that input data will be downloaded for
startYearData="1981"
startMonthData="9" #1=Jan, 12=Dec
stopYearData="2017"
stopMonthData="12" #1=Jan, 12=Dec

#Input data will be resampled to this spatial grid resolution. Not all data sets support other lon/lat resolutions, so change at your own risk!
lonResampleResolution="1.0" #In degrees
latResampleResolution="1.0" #In degrees

#NOAA ESRL marine boundary layer reference vCO2 data path:
#	This should be downloaded for the required time span.
#	Download the 'surface' dataset in .txt format from: https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php
mblInputDataPath="processing_mbl_reference_vco2/data/co2_GHGreference.275669481_surface.txt";
mblStartYear="1979" #Start year of the NOAA marine boundary layer reference data file (this must match the input data file)
mblStopYear="2018" #Stop year (inclusive) of the NOAA marine boundary layer reference data file (this must match the input data file)

#FluxEngine run parameters
#Uta's fCO2 interpolation (multiple linear regression)
feRunStartMLR="1991" #1991
feRunEndMLR="2015" #2015
configPathMLR="configs/mlr_run.conf"
#Peter's fCO2 interpolation (neural network approach)
feRunStartNNA="1991" #1991
feRunEndNNA="2015" #2015
configPathNNA="configs/nna_run.conf"



##########################################
#Download and resample Reynolds SST data #
##########################################
#Download
python processing_reynolds_sst/reynolds_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir "processing_reynolds_sst/downloaded_files"
#Resample
python processing_reynolds_sst/reynolds_resampler.py $stopYearData $stopMonthData $startYearData $startMonthData --lonResolution $lonResampleResolution --latResolution $latResampleResolution  --sourceTemplate "processing_reynolds_sst/downloaded_files/avhrr-only-v2.\${YYYY}\${MM}\${DD}.nc" --destinationRootDirectory "processing_reynolds_sst"


#############################################
#Download and resample CCMP wind speed data #
#############################################
#Download
python processing_ccmp_windu10/ccmp_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir "processing_ccmp_windu10/downloaded_files"
#Resample
python processing_ccmp_windu10/ccmp_resampler.py $stopYearData $stopMonthData $startYearData $startMonthData --lonResolution $lonResampleResolution --latResolution $latResampleResolution  --sourceTemplate "processing_ccmp_windu10/downloaded_files/CCMP_Wind_Analysis_\${YYYY}\${MM}_V02.0_L3.5_RSS.nc" --destinationRootDirectory "processing_ccmp_windu10"

################################################
#Download and resample ECMWF air pressure data #
################################################
#Download. Note that there is no need to further process this data because the ECMWF API is used to download the data in the correct format / resolution.
python processing_ecmwf_air_pressure/ecmwf_air_pressure_downloader.py $stopYearData $stopMonthData $startYearData $startMonthData --destinationDir "processing_ecmwf_air_pressure/ecmwf_era_interim_monthly_1.0x1.0_downloaded"


#################################################
#Download and resample SMOS/MIRAS salinity data #
#################################################
#Download
python processing_woa_salinity/woa_salinity_downloader.py --destinationDir "processing_woa_salinity/downloaded_files"
#Process (to extract just the top depth)
python processing_woa_salinity/process_woa_salinity.py --sourceTemplate "processing_woa_salinity/downloaded_files/woa18_decav_s\${MM}_01.nc" --destinationRootDirectory "processing_woa_salinity"


###################################
# Process NOAA ESRL MBL vCO2 data #
###################################
# Process vCO2 data from the NOAA ESRL marine boundary layer reference to a FluxEngine compatible format.
# This must be downloaded manually from https://www.esrl.noaa.gov/gmd/ccgg/mbl/data.php
# and the 'mblInputDataPath' set accordingly (at the top of this script)
python processing_mbl_reference_vco2/process_mbl_reference_vco2.py $mblStopYear $mblStartYear $mblInputDataPath --destinationRootDirectory "processing_mbl_reference_vco2/noaa_esrl_mbl_reflayer_vCO2_1.0x1.0"



# ##################################################################################
# #Convert CO2 data from matlab .mat format to FluxEngine compatible netCDF format #
# ##################################################################################
watsonMatPath="watson_fCO2_data/Jamie_Oct_18_2018.mat" #path to the .mat data file provides by Andy/Peter/Uta containing Peter and Uta's fCO2 (sw) data.
watsonNetcdfPathTemplate="watson_fCO2_data/netCDF/\${YYYY}\${MM}_watson_fco2.nc" #path template to store netCDF version of the above .mat file. Use /${YYYY} and /${MM} to specify year and month
watsonDataStartYear="1970" #Year corresponding to the first entry of the 'time' attribute in the .mat file. Month is assumed to be January.
python watson_fCO2_data/watson_to_netCDF.py $watsonMatPath $watsonNetcdfPathTemplate --startYear $watsonDataStartYear



# ##################################
# # Run FluxEngine with Uta's data # Multiple linear regression approach
# ##################################
# #Uta's data time span: 1994, 2017
echo "Running FluxEngine for Uta's MLR fCO2"
python ~/Software/FluxEngine/ofluxghg_run.py $configPathUta -s $feRunStartMLR -e $feRunEndMLR -l


####################################
# Run FluxEngine with Peter's data # Neural network approach
####################################
echo "Running FluxEngine for Peter's NNA fCO2"
python ~/Software/FluxEngine/ofluxghg_run.py $configPathNNA -s $feRunStartNNA -e $feRunEndNNA -l


###########################
# Calculate global fluxes #
###########################
#Note that the '~' (tilda) 'home' token is not parsed correctly by ofluxghg_flux_budgets and cannot be used.
echo "Calculating net flux/budgets for Uta's MLR fCO2 runs"
python ~/Software/FluxEngine/fluxengine_src/tools/ofluxghg_flux_budgets.py --dir "fe_output/mlr_fco2_runs" --outroot "fe_output/mlr_fco2_runs" --maskfile "/home/tmh214/Software/FluxEngine/data/World_Seas-final-complete_IGA.nc" --landfile "onedeg_land.nc"


echo "Calculating net flux/budgets for Peter's NNA fCO2 runs"
python ~/Software/FluxEngine/fluxengine_src/tools/ofluxghg_flux_budgets.py --dir "fe_output/nna_fco2_runs" --outroot "fe_output/nna_fco2_runs" --maskfile "/home/tmh214/Software/FluxEngine/data/World_Seas-final-complete_IGA.nc" --landfile "onedeg_land.nc"

#Group annual net flux data for each run
python processing_output/produce_net_flux_table.py "fe_output/mlr_fco2_runs_global.txt" "nna_fco2_runs_global.txt" "fe_output/annual_net_flux.csv"


echo ""
echo "Finished! FluxEngine output files have been stored in "$(pwd)"/fe_output"
