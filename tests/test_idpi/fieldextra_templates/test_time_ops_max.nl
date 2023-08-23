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
tstart=0, tstop=33, tincr=1, tlag=-24,0,1, out_tstart=0, out_tincr=3
out_file="{{ file.output }}"
out_type="NETCDF"
/
&Process in_field = "VMAX_10M", toper='mask_all', toper_mask='lead_time=0' /

&Process out_field = "VMAX_10M", tag='vmax_10m_24h', toper='max,-23,0,1,hour', set_trange_type="maximum" /
