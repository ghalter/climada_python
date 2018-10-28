"""
This file is part of CLIMADA.

Copyright (C) 2017 CLIMADA contributors listed in AUTHORS.

CLIMADA is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation, version 3.

CLIMADA is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with CLIMADA. If not, see <https://www.gnu.org/licenses/>.

---

Define GridPoints class
"""

__all__ = ['GridPoints']

import os.path
import logging
import numpy as np
import shapefile
from cartopy.io import shapereader
import shapely.vectorized
import shapely.ops
from shapely.geometry import LineString, Polygon
from sklearn.neighbors import BallTree

from climada.util.interpolation import METHOD, DIST_DEF, interpol_index
from climada.util.constants import SYSTEM_DIR, EARTH_RADIUS_KM

LOGGER = logging.getLogger(__name__)

GLOBE_LAND = "global_country_borders"
""" Name of the earth's country borders shape file generated in function
get_land_geometry"""

GLOBE_COASTLINES = "global_coastlines"
""" Name of the earth's coastlines shape file generated in function
get_coastlines"""

class GridPoints(np.ndarray):
    """Define grid using 2d numpy array. Each row is a point. The first column
    is for latitudes and the second for longitudes (in degrees)."""
    def __new__(cls, input_array=None):
        if input_array is not None:
            obj = np.asarray(input_array).view(cls)
            obj.check()
        else:
            obj = np.empty((0, 2)).view(cls)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

    def check(self):
        """Check shape. Repeated points are allowed"""
        if self.shape[1] != 2:
            LOGGER.error("GridPoints with wrong shape: %s != %s",
                         self.shape[1], 2)
            raise ValueError

    def resample_nn(self, coord, threshold=None):
        """ Input GridPoints are resampled to current grid by calculating the
        nearest neighbor. For every input coord point, its corresponding
        GridPoint in self is returned.

        Parameters:
            coord (2d array): First column contains latitude, second
                column contains longitude. Each row is a geographic point.
            threshold (float, optional): distance threshold in km over which no
                neighbor will be found. Those are assigned with a -1 index.
                Default: THRESHOLD in interpolation (100km)
        Returns:
            np.array (with shape of coord)
        """
        if threshold:
            return interpol_index(self, coord, method=METHOD[0],
                                  distance=DIST_DEF[1], threshold=threshold)
        return interpol_index(self, coord, method=METHOD[0],
                              distance=DIST_DEF[1])

    def is_regular(self):
        """Return True if grid is regular."""
        regular = False
        _, count_lat = np.unique(self[:, 0], return_counts=True)
        _, count_lon = np.unique(self[:, 1], return_counts=True)
        uni_lat_size = np.unique(count_lat).size
        uni_lon_size = np.unique(count_lon).size
        if uni_lat_size == uni_lon_size and uni_lat_size == 1 \
        and count_lat[0] > 1 and count_lon[0] > 1:
            regular = True
        return regular

    @property
    def lat(self):
        """Get latitude."""
        return self[:, 0]

    @property
    def lon(self):
        """Get longitude."""
        return self[:, 1]

def get_coastlines(border=None, resolution=110):
    """Get latitudes and longitudes of the coast lines inside border. All
    earth if no border.

    Parameters:
        border (tuple, optional): (min_lon, max_lon, min_lat, max_lat)
        resolution (float, optional): 10, 50 or 110. Resolution in m. Default:
            110m, i.e. 1:110.000.000

    Returns:
        lat (np.array), lon(np.array)
    """
    resolution = nat_earth_resolution(resolution)
    file_globe = os.path.join(SYSTEM_DIR, GLOBE_COASTLINES + "_" + resolution +
                              ".shp")
    if not os.path.isfile(file_globe):
        shp_file = shapereader.natural_earth(resolution=resolution,
                                             category='physical',
                                             name='coastline')
        shp = shapereader.Reader(shp_file)

        coast_lon, coast_lat = [], []
        for multi_line in list(shp.geometries()):
            coast_lon += multi_line.geoms[0].xy[0]
            coast_lat += multi_line.geoms[0].xy[1]
        coast = np.array((coast_lat, coast_lon)).transpose()

        LOGGER.info('Writing file %s', file_globe)

        shapewriter = shapefile.Writer()
        shapewriter.field("global_coastline")
        converted_shape = shapely_to_pyshp(LineString(coast))
        shapewriter._shapes.append(converted_shape)
        shapewriter.record(["empty record"])
        shapewriter.save(file_globe)

        LOGGER.info('Written file %s', file_globe)
    else:
        reader = shapereader.Reader(file_globe)
        all_geom = list(reader.geometries())[0].geoms[0]
        coast = np.array((all_geom.xy)).transpose()

    if border is None:
        return coast

    in_lon = np.logical_and(coast[:, 1] >= border[0], coast[:, 1] <= border[1])
    in_lat = np.logical_and(coast[:, 0] >= border[2], coast[:, 0] <= border[3])
    return coast[np.logical_and(in_lon, in_lat)].reshape(-1, 2)

def dist_to_coast(coord_lat, lon=None):
    """ Comput distance to coast from input points.

    Parameters:
        coord_lat (np.array or tuple or float):
            - np.array with two columns, first for latitude of each point and
                second with longitude.
            - np.array with one dimension containing latitudes
            - tuple with first value latitude, second longitude
            - float with a latitude value
        lon (np.array or float, optional):
            - np.array with one dimension containing longitudes
            - float with a longitude value

    Returns:
        np.array
    """
    if lon is None:
        if isinstance(coord_lat, tuple):
            coord = np.array([[coord_lat[0], coord_lat[1]]])
        elif isinstance(coord_lat, np.ndarray):
            if coord_lat.shape[1] != 2:
                LOGGER.error('Missing longitude values.')
                raise ValueError
            coord = coord_lat
        else:
            LOGGER.error('Missing longitude values.')
            raise ValueError
    elif isinstance(lon, np.ndarray):
        if coord_lat.size != lon.size:
            LOGGER.error('Wrong input coordinates size: %s != %s',
                         coord_lat.size, lon.size)
            raise ValueError
        coord = np.empty((lon.size, 2))
        coord[:, 0] = coord_lat
        coord[:, 1] = lon
    elif isinstance(lon, float):
        if not isinstance(coord_lat, float):
            LOGGER.error('Wrong input coordinates values.')
            raise ValueError
        coord = np.array([[coord_lat, lon]])

    marg = 10
    lat = coord[:, 0]
    lon = coord[:, 1]
    coast = get_coastlines((np.min(lon) - marg, np.max(lon) + marg,
                            np.min(lat) - marg, np.max(lat) + marg), 10)

    tree = BallTree(np.radians(coast), metric='haversine')
    dist_coast, _ = tree.query(np.radians(coord), k=1, return_distance=True,
                               dualtree=True, breadth_first=False)
    return dist_coast.reshape(-1,) * EARTH_RADIUS_KM

def get_land_geometry(country_names=None, border=None, resolution=10):
    """Get union of all the countries or the provided ones or the points inside
    the border. If all the countries are selected, write shp file in SYSTEM
    folder which can be directly read in following computations.

    Parameters:
        country_names (list, optional): list with ISO3 names of countries, e.g
            ['ZWE', 'GBR', 'VNM', 'UZB']
        border (tuple, optional): (min_lon, max_lon, min_lat, max_lat)
        resolution (float, optional): 10, 50 or 110. Resolution in m. Default:
            10m, i.e. 1:10.000.000

    Returns:
        shapely.geometry.multipolygon.MultiPolygon
    """
    resolution = nat_earth_resolution(resolution)
    shp_file = shapereader.natural_earth(resolution=resolution,
                                         category='cultural',
                                         name='admin_0_countries')
    reader = shapereader.Reader(shp_file)
    file_globe = os.path.join(SYSTEM_DIR, GLOBE_LAND + "_" + resolution +
                              ".shp")
    geom = Polygon()
    if (not os.path.isfile(file_globe)) and (country_names is None) and \
    (border is None):
        LOGGER.info("Computing earth's land geometry ...")
        geom = [cntry_geom for cntry_geom in reader.geometries()]
        geom = shapely.ops.cascaded_union(geom)

        LOGGER.info('Writing file %s', file_globe)

        shapewriter = shapefile.Writer()
        shapewriter.field("global_country_borders")
        converted_shape = shapely_to_pyshp(geom)
        shapewriter._shapes.append(converted_shape)
        shapewriter.record(["empty record"])
        shapewriter.save(file_globe)

        LOGGER.info('Written file %s', file_globe)

    elif country_names:
        countries = list(reader.records())
        geom = [country.geometry for country in countries
                if country.attributes['ISO_A3'] in country_names]
        geom = shapely.ops.cascaded_union(geom)

    elif border:
        border_poly = Polygon([(border[0], border[2]), (border[0], border[3]),
                               (border[1], border[3]), (border[1], border[2])])
        geom = []
        for cntry_geom in reader.geometries():
            inter_poly = cntry_geom.intersection(border_poly)
            if not inter_poly.is_empty:
                geom.append(inter_poly)
        geom = shapely.ops.cascaded_union(geom)
    else:
        geom = list(reader.geometries())
        geom = shapely.ops.cascaded_union(geom)

    return geom

def coord_on_land(lat, lon, land_geom=None):
    """Check if point is on land (True) or water (False) of provided countries.
    All globe considered if no input countries.

    Parameters:
        land_geometry (shapely.geometry.multipolygon.MultiPolygon): profiles of
            land.
        lat (np.array): latitude of points
        lon (np.array): longitude of points

    Returns:
        np.array(bool)
    """
    if lat.size != lon.size:
        LOGGER.error('Wrong size input coordinates: %s != %s.', lat.size,
                     lon.size)
        raise ValueError
    delta_deg = 1
    if land_geom is None:
        land_geom = get_land_geometry(border=(np.min(lon)-delta_deg, \
            np.max(lon)+delta_deg, np.min(lat)-delta_deg, \
            np.max(lat)+delta_deg), resolution=10)
    return shapely.vectorized.contains(land_geom, lon, lat)

def nat_earth_resolution(resolution):
    """Check if resolution is available in Natural Earth. Build string.

    Parameters:
        resolution (int): resolution in millions, 110 == 1:110.000.000.

    Returns:
        str

    Raises:
        ValueError
    """
    avail_res = [10, 50, 110]
    if resolution not in avail_res:
        LOGGER.error('Natural Earth does not accept resolution %s m.',
                     resolution)
        raise ValueError
    return str(resolution) + 'm'

GEOMETRY_TYPE = {"Null": 0, "Point": 1, "LineString": 3, "Polygon": 5,
                 "MultiPoint": 8, "MultiLineString": 3, "MultiPolygon": 5}

def shapely_to_pyshp(shapely_geom):
    """ Shapely geometry to pyshp. Code adapted from
    https://gis.stackexchange.com/questions/52705/
    how-to-write-shapely-geometries-to-shapefiles.

    Parameters:
        shapely_geom(shapely.geometry): shapely geometry to convert

    Returns:
        shapefile._Shape

    """
    # first convert shapely to geojson
    geoj = shapely.geometry.mapping(shapely_geom)
    # create empty pyshp shape
    record = shapefile._Shape()
    # set shapetype
    pyshptype = GEOMETRY_TYPE[geoj["type"]]
    record.shapeType = pyshptype
    # set points and parts
    if geoj["type"] == "Point":
        record.points = geoj["coordinates"]
        record.parts = [0]
    elif geoj["type"] in ("MultiPoint", "LineString"):
        record.points = geoj["coordinates"]
        record.parts = [0]
    elif geoj["type"] == "Polygon":
        index = 0
        points = []
        parts = []
        for eachmulti in geoj["coordinates"]:
            points.extend(eachmulti)
            parts.append(index)
            index += len(eachmulti)
        record.points = points
        record.parts = parts
    elif geoj["type"] in ("MultiPolygon", "MultiLineString"):
        index = 0
        points = []
        parts = []
        for polygon in geoj["coordinates"]:
            for part in polygon:
                points.extend(part)
                parts.append(index)
                index += len(part)
        record.points = points
        record.parts = parts
    return record
