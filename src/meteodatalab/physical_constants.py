"""Physical constants."""

g = 9.80665  # [m s-2]
omega = 7.2921e-5
earth_radius = 6371229.0  # value from COSMO GRIB2 key

r_d = 287.05  # Specific gas constant for dry air [J kg-1 K-1]
r_v = 461.51  # Gas constant for water vapour[J kg-1 K-1]
rdv = r_d / r_v
o_rdv = 1.0 - rdv
cp_d = 1005.0  # Specific heat capacity at constant pressure for dry air [J kg-1 K]
rvd = r_v / r_d
rdocp = r_d / cp_d
rvd_o = rvd - 1.0

# saturation vapour pressure (Tetens's formula, see
# http://www.ecmwf.int/sites/default/files/elibrary/2015/9208-part-i-observation-processing.pdf)
b1 = 611.21  # Pressure at triple point of water [Pa]
b2w = 17.502
b3 = 273.16  # Temperature at triple point of water [K]
b4w = 32.19  # [K]

# Surface pressure reference for omega slope
surface_pressure_ref = 101325.0  # [Pa]

# Radiation
emissivity_surface = 0.996  # [-]
boltzman_cst = 5.6697e-8  # [W m-2 K-4]
