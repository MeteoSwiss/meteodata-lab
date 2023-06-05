"""Physical constants."""

pc_omega = 7.2921e-5
earth_radius = 6371229.0  # value from COSMO GRIB2 key

p0 = 1.0e5

pc_r_d = 287.05
pc_r_v = 461.51  # Gas constant for water vapour[J kg-1 K-1]
pc_cp_d = 1005.0
pc_rvd = pc_r_v / pc_r_d
pc_rdocp = pc_r_d / pc_cp_d
pc_rvd_o = pc_rvd - 1.0
