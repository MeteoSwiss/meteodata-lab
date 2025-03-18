&RunSpecification
 strict_nl_parsing=.true.
 verbosity="moderate"
/

&GlobalResource
 dictionary="{{ resources }}/dictionary_icon.txt"
 grib_definition_path="{{ resources }}/eccodes_definitions_cosmo",
                      "{{ resources }}/eccodes_definitions_vendor"
 grib2_sample="{{ resources }}/eccodes_samples/COSMO_GRIB2_default.tmpl"
 rttov_coefs_path="{{ resources }}/rttov_coefficients"
 icon_grid_description="{{ icon_grid_description }}"
/

&GlobalSettings
 default_model_name="{{ model_name }}"
/

&ModelSpecification
 model_name="{{ model_name }}"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
/

&Process
  in_file  = "{{ file.inputi }}"
  out_file = "{{ file.output }}"
  out_type = "NETCDF"
  tstart   = 0
  tstop    = 0
  tincr    = 1
/
&Process in_field = "U_10M" /
&Process in_field = "V_10M" /
&Process out_field = "FF_10M"  /
&Process out_field = "DD_10M" /
