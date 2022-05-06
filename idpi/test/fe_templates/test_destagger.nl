&RunSpecification
 additional_profiling=.true.
 strict_nl_parsing=.true.
 print_product_list=.true.
 product_list_keep_epsm=0,1,10
 product_list_keep_leadtime_hh=0,1,2,3,6,9,12,18,24,33,45
 verbosity="moderate"
 diagnostic_length=110
 soft_memory_limit=350.0 
 wait_time=10
 mx_wait_time=14400
 enable_repeat_mode='all'
 ready_flag_dir="{{ready_flags}}"
   ready_flag_prefix_pure="FXTRF_PURE_"
   ready_flag_prefix_other="FXTRF_OTHER_"
 out_noready_postfix=".incomplete"
 out_snapshot_postfix=".snapshot_"
 stop_flag="/opr/osm/rh7.9/tmp/21101512_407/.ppStopTasks_c"
 n_ompthread_total=1
 n_ompthread_collect=1
 n_ompthread_generate=1,1
 out_cost_expensive=1000
/
&GlobalResource
 dictionary="/project/s83c/fieldextra/tsa/resources/dictionary_cosmo.txt"
 grib_definition_path="/project/s83c/fieldextra/tsa/resources/eccodes_definitions_cosmo", 
                        "/project/s83c/fieldextra/tsa/resources/eccodes_definitions_vendor"
 grib2_sample="/project/s83c/fieldextra/tsa/resources/eccodes_samples/COSMO_GRIB2_default.tmpl"
 location_list="/project/s83c/fieldextra/tsa/resources/location_list.txt" 
 slice_list="/project/s83c/fieldextra/tsa/resources/slice_list.txt"
 location_list_additional="/opr/osm/rh7.9/wd/21101512_407/coeff_2021101512_cosmo-1e_kal_T_2M",
                            "/opr/osm/rh7.9/wd/21101512_407/coeff_2021101512_cosmo-1e_kal_TD_2M",
                            "/opr/osm/rh7.9/wd/21101512_407/coeff_2021101512_cosmo-1e_kal_FF_10M"
 region_list="/project/s83c/fieldextra/tsa/resources/region_list.txt"
 rttov_coefs_path="/project/s83c/fieldextra/tsa/resources/rttov_coefficients"
/
&GlobalSettings
 default_model_name="cosmo-1e"
 location_to_gridpoint="sn" 
 slice_to_gridpoint="nn" 
 slice_resolution_factor=0.5
 slice_upscaling_factor=10
 auxiliary_metainfo="localNumberOfExperiment=407",
/
&ModelSpecification
 model_name="cosmo-1e"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
 hydrometeor="QR", "QG", "QS"
 precip_all="RAIN_GSP", "SNOW_GSP", "GRAU_GSP"
 precip_snow="SNOW_GSP", "GRAU_GSP"
 precip_rain="RAIN_GSP"
 precip_convective=
 precip_gridscale="RAIN_GSP", "SNOW_GSP", "GRAU_GSP"
 vertical_coordinate_coef=
   104.00000,       80.000000,       100000.00,       288.14990,       42.000000,    
   11357.000,       22000.000,       21187.520,       20396.250,       19625.891,    
   18876.129,       18146.680,       17437.219,       16747.449,       16077.078,    
   15425.797,       14793.297,       14179.289,       13583.469,       13005.527,    
   12445.188,       11902.129,       11376.059,       10866.688,       10373.707,    
   9896.8398,       9435.7695,       8990.2070,       8559.8672,       8144.4492,    
   7743.6602,       7357.2070,       6984.7969,       6626.1484,       6280.9688,    
   5948.9570,       5629.8281,       5323.3086,       5029.0898,       4746.9102,    
   4476.4570,       4217.4570,       3969.6399,       3732.7000,       3506.3701,    
   3290.3601,       3084.3999,       2888.2000,       2701.4800,       2523.9600,    
   2355.3799,       2195.4500,       2043.8999,       1900.4500,       1764.8398,    
   1636.7800,       1516.0200,       1402.2700,       1295.2800,       1194.7700,    
   1100.4800,       1012.1399,       929.48999,       852.28003,       780.22998,    
   713.08984,       650.60986,       592.52002,       538.56982,       488.51978,    
   442.10986,       399.08984,       359.20996,       322.23999,       287.92993,    
   256.03979,       226.33000,       198.57001,       172.53999,       148.00000,    
   124.73000,       102.50999,       81.129990,       60.389999,       40.069992,    
   20.000000,       0.0000000,       10000.000,       3300.0000,       100.00000,    
   75.000000,       10000.000
/
&ModelSpecification
 model_name="inca-1"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
/
&ModelSpecification
 model_name="inca-1e"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
/

&Process
  in_file="{{ file.inputc }}"
  out_type="INCORE" /
&Process in_field="HSURF", tag='GRID' /
&Process in_field="HEIGHT", tag="hhl_c1e", levmin=1, levmax=81, level_class="k_half" /

&Process
  in_type="INCORE"
  in_regrid_target="GRID"
  in_regrid_method="average,square,0.9",
  tstart=0, tstop=0, tincr=1
  out_file="{{ file.output }}"
  out_cost=5
  out_type="NETCDF"
  out_mode_ignore_wloading=.false.
  out_mode_h0cl_extrapolate=.true.
  in_duplicate_field=.true.
  in_size_field=1072
/
&Process in_field="HSURF", use_tag="GRID", tag="hsurf" /
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HHL", level_class="k_half", levmin=1, levmax=81 /
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HFL", level_class="k_full", levmin=1, levmax=80 /

&Process
  in_file="{{ file.inputi }}"
  in_regrid_target="GRID"
  in_regrid_method="average,square,0.9",
  out_file="{{ file.output }}", out_type="NETCDF"
  out_cost=5
  out_mode_ignore_wloading=.false.
  out_mode_h0cl_extrapolate=.true.
  in_duplicate_field=.true.
  in_size_field=1072
  tstart=0, tstop=0, tincr=1
/
&Process in_field="U", regrid=.t., levmin=1, levmax=80 /
&Process in_field="V", regrid=.t., levmin=1, levmax=80 /
&Process tmp1_field="U", levmin=1,levmax=80 /
&Process tmp1_field="V", levmin=1, levmax=80 /
&Process tmp1_field="HFL", levmin=1, levmax=80 /
&Process out_field="U", levmin=1, levmax=80 /
&Process out_field="V", levmin=1, levmax=80 /
&Process out_field="HFL", levmin=1, levmax=80 /

