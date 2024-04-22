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
  in_file="{{ file.inputc }}"
  out_type="INCORE"
/
&Process in_field="FIS" /
&Process in_field="HSURF", tag='GRID' /
&Process in_field="HEIGHT", tag="hhl_c1e", levmin=1, levmax=81, level_class="k_half" /

&Process
  in_type="INCORE"
  in_regrid_target="GRID"
  out_file="{{ file.output }}", out_type="NETCDF"
  tstart=0, tstop=0, tincr=1
/
&Process in_field="HEIGHT", use_tag="hhl_c1e", tag="HHL", level_class="k_half", levmin=1, levmax=81 /

&Process
  in_file="{{ file.inputi }}"
  in_regrid_target="GRID"
  out_file="{{ file.output }}", out_type="NETCDF"
  tstart=0, tstop=0, tincr=1
/

&Process in_field="U", levmin=1, levmax=80 /
&Process in_field="V", levmin=1, levmax=80 /
&Process in_field="W", levmin=1, levmax=81 /
&Process in_field="P", levmin=1, levmax=80 /
&Process in_field="T", levmin=1, levmax=80 /
&Process in_field="QV", levmin=1, levmax=80 /
&Process in_field="QC", levmin=1, levmax=80 /
&Process in_field="QI", levmin=1, levmax=80 /

&Process tmp1_field="POT_VORTIC", levmin=1, levmax=80 /

&Process out_field="POT_VORTIC" /
