#-------------------------------------------------------------------------------------------------------------
# Run specification and global blocks (compulsory!)
#-------------------------------------------------------------------------------------------------------------
&RunSpecification
 strict_nl_parsing  = .true.
 verbosity          = "moderate"
 diagnostic_length  = 110
 additional_diagnostic = .false.
 n_ompthread_total    = 1
 n_ompthread_collect  = 1
 n_ompthread_generate = 1
 soft_memory_limit   = 20.0
 strict_usage = .false.
/

&GlobalResource
 dictionary           = "/project/s83c/fieldextra/tsa/resources/dictionary_ifs.txt",
 grib_definition_path = "/project/s83c/fieldextra/tsa/resources/eccodes_definitions_cosmo",
                        "/project/s83c/fieldextra/tsa/resources/eccodes_definitions_vendor"
 grib2_sample         = "/project/s83c/fieldextra/tsa/resources/eccodes_samples/COSMO_GRIB2_default.tmpl"
/
&GlobalSettings
 default_model_name ="ifs"
 location_to_gridpoint = "sn"
 auxiliary_metainfo = "localNumberOfExperiment=1"
/

&ModelSpecification
 earth_axis_large   = 6371229.
 earth_axis_small   = 6371229.
 model_name = "ifs"
 precip_rain        = "TOT_PREC", "-1:TOT_SNOW"
/

&Process
  in_file = "{{ file.inputc }}"
  out_type = "INCORE" /
&Process in_field = "FIS" /
&Process in_field = "FR_LAND" /
&Process in_field = "SDOR" /

#-------------------------------------------------------------------------------------------------------------
# In core data
#-------------------------------------------------------------------------------------------------------------
&Process
 in_type = "INCORE"
 out_file = "{{ file.output }}"
 out_type = "NETCDF"
 tstart = 0, tstop = 9, tincr = 3
/
&Process in_field = "FIS" /
&Process in_field = "FR_LAND" /
&Process in_field = "SDOR" /

&Process
 in_file = "{{ file.inputi }}"
 out_file = "{{ file.output }}"
 out_type = "NETCDF"
 tstart = 0, tstop = 9, tincr = 3, out_tstart=3, out_tincr=3, tlag=-3
/
&Process in_field = "U",levmin=40,levmax=137  /
&Process in_field = "V",levmin=40,levmax=137  /
&Process in_field = "ETADOT",levmin=1,levmax=137 /
&Process in_field = "T", levmin=40,levmax=137  /
&Process in_field = "QV",levmin=40,levmax=137  /
&Process in_field = "PS"/
&Process in_field = "U_10M" /
&Process in_field = "V_10M" /
&Process in_field = "T_2M" /
&Process in_field = "TD_2M" /
&Process in_field = "CLCT" /
! FLEXPART expects precipitation rates in mm/h. It, however, checks for the GRIB coding
! of precipitation in the import. Therefore, the parameter IDs are not changed here.
! Time ranges are neither checked, so they are neither re-set.
&Process in_field = "TOT_GSP", toper="delta", scale=0.333333 /
&Process in_field = "TOT_CON", toper="delta", scale=0.333333 /
&Process in_field = "W_SNOW" /
&Process in_field = "SSR", toper="delta" /
&Process in_field = "SSHF", toper="delta" /
&Process in_field = "EWSS", toper="delta" /
&Process in_field = "NSSS", toper="delta" /

&Process out_field = "FIS" /
&Process out_field = "FR_LAND" /
&Process out_field = "SDOR" /
&Process out_field = "U" /
&Process out_field = "V" /
! TODO recover
&Process out_field = "OMEGA_SLOPE", new_field_id="ETADOT", levmin=40,levmax=137 /
!&Process out_field = "OMEGA_SLOPE", new_field_id="ETADOT" /
&Process out_field = "T" /
&Process out_field = "QV" /
&Process out_field = "PS"/
&Process out_field = "U_10M" /
&Process out_field = "V_10M" /
&Process out_field = "T_2M" /
&Process out_field = "TD_2M" /
&Process out_field = "CLCT" /
&Process out_field = "TOT_GSP", scale=1000. /
&Process out_field = "TOT_CON", scale=1000. /
&Process out_field = "W_SNOW" /
&Process out_field = "SSR", poper="rate", new_field_id="SSR" /
&Process out_field = "SSHF", poper="rate", new_field_id="SSHF" /
&Process out_field = "EWSS", poper="rate", new_field_id="EWSS" /
&Process out_field = "NSSS", poper="rate", new_field_id="NSSS" /
