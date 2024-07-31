&RunSpecification
  strict_nl_parsing=.true.
  verbosity="moderate"
  diagnostic_length=110
  soft_memory_limit=300.0
/

&GlobalResource
  dictionary="{{ resources }}/dictionary_icon.txt"
  grib_definition_path="{{ resources }}/eccodes_definitions_cosmo"
                       "{{ resources }}/eccodes_definitions_vendor"
  grib2_sample="{{ resources }}/eccodes_samples/COSMO_GRIB2_default.tmpl"
  icon_grid_description="/oprusers/osm/opr.emme/data/ICON_INPUT/ICON-CH1-EPS/icon_grid_0001_R19B08_mch.nc"
  rttov_coefs_path="{{ resources }}/rttov_coefficients"
/

&GlobalSettings
  default_model_name="icon-ch1-eps"
  default_out_type_stdlongitude=.true.
  location_to_gridpoint="sn"
/

&ModelSpecification
  model_name="icon-ch1-eps"
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
  in_file  = "{{ file.inputi }}"
  tstart = 0, tstop = 0, tincr = 1
  out_regrid_target = "rotlatlon,353140000,-4460000,4830000,3390000,10000,10000,190000000,43000000"
  out_regrid_method = "icontools,rbf"
  out_file = "{{ file.output }}"
  out_type = "NETCDF"
/
&Process in_field="T", levmin=1, levmax=80 /
&Process out_field="T" /

