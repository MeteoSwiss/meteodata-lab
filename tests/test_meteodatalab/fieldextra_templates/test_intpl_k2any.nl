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
  out_type = "INCORE"
/
&Process in_field = "HEIGHT", level_class="k_half", levmin=1, levmax=81 /

&Process
  in_type="INCORE"
  out_file="{{ file.output }}"
  out_type="NETCDF"
  tstart=0, tstop=0, tincr=1
/
&Process in_field = "HEIGHT", level_class="k_full", levmin=1, levmax=80 /

&Process
  in_file = "{{ file.inputi }}"
  out_file = "{{ file.output }}",
  out_type = "NETCDF"
  tstart = 0, tstop = 0, tincr = 1
/
&Process in_field="DBZ", levmin=1, levmax=80, ignore_vcoord=.true. /

&Process tmp1_field="HEIGHT", tag="htop", levlist=1 /
&Process tmp1_field="HEIGHT", tag="height", voper="find_value,dbz=15.,htop,down" /
&Process tmp1_field="HEIGHT", tag="height2", voper="find_value,dbz=10.,htop,down" /
&Process tmp1_field="DBZ", tag="dbz" /

&Process out_field = "height", tag="ECHOTOPinM", new_field_id="ECHOTOPinM", set_level_property="echo_top[dBZ],15" /
&Process out_field = "height2", tag="ECHOTOP10inM", new_field_id="ECHOTOPinM", set_level_property="echo_top[dBZ],10" /
