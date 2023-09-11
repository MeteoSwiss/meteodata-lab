&RunSpecification
 strict_nl_parsing=.true.
 verbosity="moderate"
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
/

&ModelSpecification
 model_name="cosmo-1e"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
/

&Process
  in_file  = "{{ file.inputi }}"
  out_file = "{{ file.output }}"
  out_type = "NETCDF", out_type_noundef = .false.
  tstart   = 0
  tstop    = 33
  tincr    = 1
/
&Process in_field = "ATHB_S", toper="tdelta,1,hour" /
&Process in_field = "T_G" /
&Process out_field = "ATHD_S_TG", set_trange_type="average" /
