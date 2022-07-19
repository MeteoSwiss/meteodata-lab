"""algorithm for the potential temperature theta"""


def ftheta(p, t):
    # Physical constants
    pc_r_d = 287.05  # Gas constant for dry air [J kg-1 K-1]
    pc_cp_d = 1005.0 # Specific heat capacity of dry air at 0 deg C and constant pressure [J kg-1 K-1]
    pc_rdocp = pc_r_d / pc_cp_d

    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5
    
    return (p0 / p) ** pc_rdocp * t