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
in_file="{{ file.inputi }}"
tstart=0, tstop=15, tincr=3, tlag=-3,0,3
out_file="{{ file.output }}"
out_type="NETCDF"
/
!The point operator replaces negative values by zero as those are due to numerical inaccuracies.
&Process in_field = "TOT_PREC", tag='tot_prec_03h', toper='delta,3,hour', poper="replace_cond,<0.,0." /

&Process out_field = "tot_prec_03h", set_trange_type="accumulation" /
