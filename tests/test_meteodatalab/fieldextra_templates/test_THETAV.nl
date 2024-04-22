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
 dictionary="{{ resources }}/dictionary_cosmo.txt"
 grib_definition_path="{{ resources }}/eccodes_definitions_cosmo",
                        "{{ resources }}/eccodes_definitions_vendor"
 grib2_sample="{{ resources }}/eccodes_samples/COSMO_GRIB2_default.tmpl"
 rttov_coefs_path="{{ resources }}/rttov_coefficients"
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

&Process
  in_file="{{ file.inputc }}"
  out_type="INCORE" /
&Process in_field="FR_LAND" /
&Process in_field="FR_LAKE" /
&Process in_field="SOILTYP" /
&Process in_field="HSURF", tag='GRID' /
&Process in_field="FIS" /
&Process in_field="HEIGHT", tag="hhl_c1e", levmin=1, levmax=81, level_class="k_half" /

&Process
  in_type="INCORE"
  tstart=0, tstop=0, tincr=1
  out_file="{{ file.output }}"
  out_type="NETCDF"
  in_size_field=570
/
&Process in_field="HSURF", use_tag="GRID", tag="hsurf" /
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HHL", level_class="k_half", levmin=1, levmax=81 /
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HFL", level_class="k_full", levmin=1, levmax=80 /
&Process in_field="SOILTYP" /

&Process
  in_file="{{ file.inputi }}"
  out_file="{{ file.output }}", out_type="NETCDF"
  in_size_field=570
  tstart=0, tstop=0, tincr=1
/
&Process in_field="P", levmin=1, levmax=80 /
&Process in_field="T", levmin=1, levmax=80 /
&Process in_field="QV", levmin=1, levmax=80 /
&Process out_field="THETA_V", levmin=1, levmax=80 /

