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
  in_file="{{ file.inputc }}"
  out_type="INCORE"
/
&Process in_field="HSURF", tag='GRID' /
&Process in_field="HEIGHT", levmin=1, levmax=81, level_class="k_half" /

&Process
in_type="INCORE"
out_file="{{ file.output }}", out_type="NETCDF"
out_mode_ignore_wloading=.true.
in_regrid_target="GRID"
tstart=0, tstop=0, tincr=1
/
&Process in_field = "HEIGHT", levmin = 1, levmax = 81, level_class="k_half", tag="hhl" /
&Process in_field = "HEIGHT", levmin = 1, levmax = 80, level_class="k_full", tag="hfl" /
&Process in_field = "HSURF" /

&Process
in_file="{{ file.inputi }}"
out_file="{{ file.output }}", out_type="NETCDF"
out_mode_ignore_wloading=.true.
in_regrid_target="GRID"
tstart=0, tstop=0, tincr=1
/
&Process in_field = "U", levmin = 1, levmax = 80 /
&Process in_field = "V", levmin = 1, levmax = 80 /
&Process in_field = "W", levmin = 1, levmax = 81 /
&Process in_field = "P", levmin=1, levmax=80 /
&Process in_field = "T", levmin=1, levmax=80 /
&Process in_field = "QC", levmin=1, levmax=80 /
&Process in_field = "QV", levmin=1, levmax=80 /
&Process in_field = "QI", levmin=1, levmax=80 /

&Process tmp1_field = "hhl" /
&Process tmp1_field = "hfl", tag = "height_700hPa", voper = "intpl_k2p,lnp", voper_lev = 700 /
&Process tmp1_field = "hfl", tag = "height_900hPa", voper = "intpl_k2p,lnp", voper_lev = 900 /
&Process tmp1_field = "THETA" /
&Process tmp1_field = "POT_VORTIC" /
&Process tmp1_field = "P" /
&Process tmp1_field = "U", hoper="destagger" /
&Process tmp1_field = "V", hoper="destagger" /

&Process tmp2_field = "hhl" /
&Process tmp2_field = "height_700hPa" /
&Process tmp2_field = "height_900hPa" /
&Process tmp2_field = "THETA", tag="theta" /
&Process tmp2_field = "POT_VORTIC", tag = "POT_VORTIC_MEAN", voper="norm_integ_z2z,height_900hPa,height_700hPa", voper_use_tag="hhl,height_900hPa,height_700hPa" /
&Process tmp2_field = "POT_VORTIC", tag = "POT_VORTIC_AT_THETA", voper="intpl_k2theta,low_fold", voper_lev = 310,315,320,325,330,335, voper_lev_units="K", voper_use_tag="hhl,theta" /
&Process tmp2_field = "P", voper="intpl_k2theta,low_fold", voper_lev = 310,315,320,325,330,335, voper_lev_units="K", voper_use_tag="hhl,theta" /
&Process tmp2_field = "U", voper="intpl_k2theta,low_fold", voper_lev = 310,315,320,325,330,335, voper_lev_units="K", voper_use_tag="hhl,theta" /
&Process tmp2_field = "V", voper="intpl_k2theta,low_fold", voper_lev = 310,315,320,325,330,335, voper_lev_units="K", voper_use_tag="hhl,theta" /

&Process out_field = "POT_VORTIC" /
&Process out_field = "P" /
&Process out_field = "U" /
&Process out_field = "V" /
