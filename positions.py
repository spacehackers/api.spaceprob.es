"""
Calculate spacecraft, planet positions in an ecliptic cartesian plane.

You can run these functions from another script like this:

    import positions            # this loads the most recent DSN
    positions.spacecraft_position(<spacecraft name>)
    positions.planet_position(<planet name>)

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from astropy.utils.data import download_file
import json
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import (SkyCoord, AltAz, Angle, EarthLocation)
import ephem

def download_dsn():
    """
    Download the DSN data from spaceprob.es
    """
    dsn_url = 'http://murmuring-anchorage-8062.herokuapp.com/dsn/probes.json'
    f = download_file(dsn_url, cache=False)
    dsn = json.loads(open(f).read())['dsn_by_probe']
    return dsn

DSN = download_dsn()

# Define the positions of the DSN dishes
canberra = EarthLocation.from_geodetic(-149.1244*u.deg, -35.3075*u.deg, 0*u.m)
goldstone = EarthLocation.from_geodetic(Angle('-116d53m24s'),
                                        Angle('35d25m36s'), 0*u.m)
madrid = EarthLocation.from_geodetic(Angle('-4d14m57s'),
                                     Angle('40d25m45s'), 0*u.m)
DISHES = dict(Canberra=canberra,
              Goldstone=goldstone,
              Madrid=madrid)

PLANETS = dict(mercury=ephem.Mercury(),
               venus=ephem.Venus(),
               mars=ephem.Mars(),
               jupiter=ephem.Jupiter(),
               saturn=ephem.Saturn(),
               uranus=ephem.Uranus(),
               neptune=ephem.Neptune(),
               pluto=ephem.Pluto())

def spacecraft_position(spacecraft_name):
    """
    Get spacecraft position in ecliptic cartesian coordinates

    Parameters
    ----------
    spacecraft_name : string
        Name of the spacecraft in the DSN dictionary

    Returns
    -------
    tuple
        (x, y) position of spacecraft in units of AU
    """
    if spacecraft_name not in DSN:
        raise ValueError("Spacecraft {0} is not in DSN file"
                         .format(spacecraft_name))

    if ('downlegRange' not in DSN[spacecraft_name] or 'azimuthAngle' not in DSN[spacecraft_name] or
        DSN[spacecraft_name]['downlegRange'] == '-1.0'):
        raise ValueError("No distance/alt/az for spacecraft {0}"
                         .format(spacecraft_name))
    altitude = float(DSN[spacecraft_name]['elevationAngle'])*u.deg
    if altitude > u.Quantity(90, unit=u.deg):
        altitude = 90*u.deg
    azimuth = float(DSN[spacecraft_name]['azimuthAngle'])*u.deg
    distance = float(DSN[spacecraft_name]['downlegRange'])*u.km
    time = Time(DSN[spacecraft_name]['last_conact'][:-1], format='isot')
    dish = DSN[spacecraft_name]['station']

    c = SkyCoord(alt=altitude, az=azimuth, distance=distance,
                 frame=AltAz(obstime=time,
                             location=DISHES[dish]))
    cartesian_coord = c.barycentrictrueecliptic.cartesian
    return (cartesian_coord.x.to(u.AU).value, cartesian_coord.y.to(u.AU).value)

def planet_position(planet):
    """
    Get planet position in ecliptic cartesian coordinates

    Parameters
    ----------
    planet : string
        Name of the planet

    Returns
    -------
    tuple
        (x, y) position of spacecraft in units of AU
    """
    planet = planet.lower()

    if planet not in PLANETS and planet != 'earth':
        raise ValueError("{0} not a valid planet".format(planet))

    if planet != 'earth':
        p = PLANETS[planet]
        observer = ephem.Observer()
        observer.date = Time.now().datetime
        planet.compute(observer)
        c = SkyCoord(ra=float(planet.ra)*u.rad,
                     dec=float(planet.dec)*u.rad,
                     distance=planet.earth_distance*u.AU, frame='gcrs',
                     obstime=Time.now())
        planet_cartesian = c.barycentrictrueecliptic.cartesian
        return (planet_cartesian.x.to(u.AU).value,
                planet_cartesian.y.to(u.AU).value)

    else:
        earth_coord = SkyCoord(ra=0*u.deg, dec=0*u.deg, distance=0*u.m,
                               frame='gcrs', obstime=Time.now())
        cartesian_earth = earth_coord.icrs.barycentrictrueecliptic.cartesian
        return (cartesian_earth.x.to(u.AU).value,
                cartesian_earth.y.to(u.AU).value)
