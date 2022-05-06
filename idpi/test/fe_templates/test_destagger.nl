&RunSpecification
 additional_profiling=.true.
 strict_nl_parsing=.true.
 verbosity="moderate"
 diagnostic_length=110
 soft_memory_limit=350.0 
 wait_time=10
 mx_wait_time=14400
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
  out_type="NETCDF"
  in_size_field=240
/
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HFL", level_class="k_full", levmin=1, levmax=80 /

&Process
  in_file="{{ file.inputi }}"
  in_regrid_target="GRID"
  in_regrid_method="average,square,0.9",
  out_file="{{ file.output }}", out_type="NETCDF"
  in_size_field=240
  tstart=0, tstop=0, tincr=1
/
&Process in_field="U", regrid=.t., levmin=1, levmax=80 /
&Process in_field="V", regrid=.t., levmin=1, levmax=80 /
&Process out_field="U", levmin=1, levmax=80 /
&Process out_field="V", levmin=1, levmax=80 /
&Process out_field="HFL", levmin=1, levmax=80 /

