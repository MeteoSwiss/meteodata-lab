"""Physical constants."""

pc_omega = 7.2921e-5
earth_radius = 6371229.0  # value from COSMO GRIB2 key

p0 = 1.0e5

pc_r_d = 287.05
pc_r_v = 461.51  # Gas constant for water vapour[J kg-1 K-1]
pc_rdv = pc_r_d / pc_r_v
pc_o_rdv = 1.0 - pc_rdv
pc_cp_d = 1005.0
pc_rvd = pc_r_v / pc_r_d
pc_rdocp = pc_r_d / pc_cp_d
pc_rvd_o = pc_rvd - 1.0

# saturation vapour pressure (Tetens's formula, see
# http://www.ecmwf.int/sites/default/files/elibrary/2015/9208-part-i-observation-processing.pdf)
pc_b1 = 611.21  # Pressure at triple point of water [Pa]
pc_b2w = 17.502
pc_b3 = 273.16  # Temperature at triple point of water [K]
pc_b4w = 32.19  # [K]
#
