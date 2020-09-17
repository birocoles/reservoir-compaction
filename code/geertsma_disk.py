"""
Forward modelling of elastic reservoir deformation produced by a single
disk-shaped reservoir.

The displacement and stress components are computed by using the Geertsma's
model (Fjær et al., 2008, Appendix D-5). The equations are valid outside the
reservoir.

References
----------

Fjær, E, Holt, R., M., Horsrud, P., Raaen, A. M., and Risnes, R. (2008).
Petroleum Related Rock Mechanics. Elsevier, 2nd edition. ISBN:978-0-444-50260-5

"""

import numpy as np
from scipy.special import ellipk, ellipe, ellipkinc, ellipeinc
from compaction import Cm


def Geertsma_disk_displacement(coordinates, disk, pressure, poisson, young):
    '''
    Radial and vertical components of the displacement field produced by a
    disk-shaped reservoir with center at (y0, x0, D), radius R and thickness h.

    Parameters
    ----------
    coordinates : 2d-array
        2d numpy array containing ``y``, ``x`` and ``z`` Cartesian cordinates
        of the computation points. All coordinates should be in meters.
    disk : list
        list containing y0, x0, D, R, h. All values should be in meters.
    pressure : scalar
        pressure variation of the reservoir in MPa.
    poisson : float
        Poisson’s ratio.
    young : float
        Young’s modulus in MPa.

    Returns
    -------
    ur, uz : arrays
        Radial and vertical components of the displacement field generated by
        the model at the computation points.
    '''
    assert len(disk) == 5, 'disk must contain y0, x0, D, R, and h'
    assert coordinates.shape[0] == 3, 'coordinates must have 3 rows'
    assert np.isscalar(pressure), 'pressure must be a scalar'
    assert np.isscalar(poisson), 'poisson must be a scalar'
    assert np.isscalar(young), 'young must be a scalar'

    y0, x0, D, R, h = disk

    Y = coordinates[0] - y0
    X = coordinates[1] - x0
    Z = coordinates[2] - D

    r = np.sqrt(Y**2 + X**2 + Z**2)

    Z2 = Z + 2*D

    # radial component
    ur = -pressure*(
        Int1(np.abs(Z),r,R)
        + (3 - 4*poisson)*Int1(Z2,r,R)
        - 2*coordinates[2]*Int2(Z2,r,R)
    )

    # vertical component
    uz = pressure*(
        np.sign(Z)*Int3(np.abs(Z),r,R)
        - (3 - 4*poisson)*Int3(Z2,r,R)
        - 2*coordinates[2]*Int4(Z2,r,R)
    )

    ur *= Cm(poisson, young)*R*h/2
    uz *= Cm(poisson, young)*R*h/2

    return ur, uz


def Geertsma_disk_stress(coordinates, disk, pressure, poisson, young):
    '''
    Radial, tangential and vertical components of the stress field produced by
    a disk-shaped reservoir with center at (y0, x0, D), radius R and
    thickness h.

    Parameters
    ----------
    coordinates : 2d-array
        2d numpy array containing ``y``, ``x`` and ``z`` Cartesian cordinates
        of the computation points. All coordinates should be in meters.
    disk : list
        list containing y0, x0, D, R, h. All values should be in meters.
    pressure : scalar
        pressure variation of the reservoir in MPa.
    poisson : float
        Poisson’s ratio.
    young : float
        Young’s modulus in MPa.

    Returns
    -------
    ur, uz : arrays
        Radial, tangential and vertical components of the stress field
        generated by the model at the computation points.
    '''
    assert len(disk) == 5, 'disk must contain y0, x0, D, R, and h'
    assert coordinates.shape[0] == 3, 'coordinates must have 3 rows'
    assert np.isscalar(pressure), 'pressure must be a scalar'
    assert np.isscalar(poisson), 'poisson must be a scalar'
    assert np.isscalar(young), 'young must be a scalar'

    y0, x0, D, R, h = disk

    Y = coordinates[0] - y0
    X = coordinates[1] - x0
    Z = coordinates[2] - D

    r = np.sqrt(Y**2 + X**2 + Z**2)

    Z2 = Z + 2*D

    # radial component
    sr = pressure*(
        Int4(np.abs(Z),r,R)
        + 3*Int4(Z2,r,R)
        - 2*coordinates[2]*Int6(Z2,r,R)
        - Int1(np.abs(Z),r,R)/r
        + (3 - 4*poisson)*Int1(Z2,r,R)/r
        - 2*coordinates[2]*Int2(Z2,r,R)/r
    )

    # tangential component
    st = pressure*(
        4*poisson*Int4(Z2,r,R)
        + Int1(np.abs(Z),r,R)/r
        + (3 - 4*poisson)*Int1(Z2,r,R)/r
        - 2*coordinates[2]*Int2(Z2,r,R)/r
    )

    # vertical component
    sz = -pressure*(
        -Int4(np.abs(Z),r,R)
        + Int4(Z2,r,R)
        + 2*coordinates[2]*Int6(Z2,r,R)
    )

    aux = G(poisson,young)*Cm(poisson,young)*R*h

    sr *= aux
    st *= aux
    sz *= aux

    return sr, st, sz


def Int1(q, r , R):
    '''
    Integral I1.
    '''
    m = 4*R*r/(q**2 + (r+R)**2)

    K = ellipk(m) # Complete elliptic integral of the first kind
    E0 = ellipe(m) # Complete elliptic integral of the second kind
    I1 = 2*((1-(m/2))*K - E0)/(np.pi*np.sqrt(m*r*R))

    return I1


def Int2(q, r , R):
    '''
    Integral I2.
    '''
    m = 4*R*r/(q**2 + (r+R)**2)

    K = ellipk(m) # Complete elliptic integral of the first kind
    E0 = ellipe(m) # Complete elliptic integral of the second kind
    I2 = q*np.sqrt(m)*((1-m/2)*E0/(1-m) - K)/(2*np.pi*np.sqrt(r*R)**3)

    return I2


def Int3(q, r , R):
    '''
    Integral I3.
    '''
    m = 4*R*r/(q**2 + (r+R)**2)

    K0 = ellipk(m) # Complete elliptic integral of the first kind
    K1 = ellipk(1-m)
    E0 = ellipe(m) # Complete elliptic integral of the second kind
    E1 = ellipe(1-m)

    beta = np.arcsin(q/np.sqrt(q**2 + (R-r)**2))
    K2 = ellipkinc(beta,1-m) # Incomplete elliptic integral of the first kind
    E2 = ellipeinc(beta,1-m) # Incomplete elliptic integral of the second kind

    Z = E2-E1*K2/K1  # Jacobi zeta function

    lamb = K2/K1 +2*K0*Z/np.pi # Heuman’s lambda function

    I3 = -q*np.sqrt(m)*K0/(2*np.pi*R*np.sqrt(r*R)) + (np.heaviside(r-R, 0.5)-np.heaviside(R-r, 0.5))*lamb/(
        2*R) + np.heaviside(R-r, 0.5)/R

    return I3


def Int4(q, r , R):
    '''
    Integral I4.
    '''
    m = 4*R*r/(q**2 + (r+R)**2)

    K0 = ellipk(m) # Complete elliptic integral of the first kind
    E0 = ellipe(m) # Complete elliptic integral of the second kind

    I4 = np.sqrt(m)**3*(R**2-r**2-q**2)*E0/(8*np.pi*np.sqrt(r*R)**3*R*(1-m)) + np.sqrt(m)*K0/(
        2*np.pi*R*np.sqrt(r*R))

    return I4


def Int6(q, r , R):
    '''
    Integral I6.
    '''
    m = 4*R*r/(q**2 + (r+R)**2)

    K0 = ellipk(m) # Complete elliptic integral of the first kind
    E0 = ellipe(m) # Complete elliptic integral of the second kind

    I6 = q*np.sqrt(m)**3*(3*E0 + m*(R**2-r**2-q**2)*((1-m/2)*E0/(1-m) - K0/4)/(r*R))/(
        8*np.pi*np.sqrt(r*R)**3*R*(1-m))

    return I6


def G(poisson, young):
    """
    Shear Modulus in MPa.
    """
    result = young/(2*(1+poisson))
    return result