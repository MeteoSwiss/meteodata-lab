&RunSpecification
 strict_nl_parsing=.true.
 verbosity="moderate"
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
/

&ModelSpecification
 model_name="cosmo-1e"
 earth_axis_large=6371229.
 earth_axis_small=6371229.
/

&Process
in_file="{{ file.inputi }}"
tstart=0, tstop=12, tincr=1, tlag=-1
out_file="{{ file.output }}"
out_type="NETCDF"
/
&Process in_field = "ASWDIFD_S", toper = "tdelta,1,hour" /
&Process in_field = "ASWDIR_S", toper = "tdelta,1,hour" /
&Process out_field = "GLOB", set_trange_type="average" /
