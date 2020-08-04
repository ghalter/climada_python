"""
This file is part of CLIMADA.

Copyright (C) 2017 ETH Zurich, CLIMADA contributors listed in AUTHORS.

CLIMADA is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation, version 3.

CLIMADA is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with CLIMADA. If not, see <https://www.gnu.org/licenses/>.

---

Georegion objects for the hazard event emulator.
"""

import logging
import numpy as np
import geopandas as gpd
import shapely.ops
import shapely.vectorized
from shapely.geometry import Polygon

from climada.hazard import Centroids
from climada.util.coordinates import get_country_geometries, NE_CRS
import climada.hazard.emulator.const as const

LOGGER = logging.getLogger(__name__)


class HazRegion():
    """Hazard region for given geo information"""

    def __init__(self, extent=None, geometry=None, country=None, season=(1, 12)):
        """Initialize HazRegion

        If several arguments are passed, the spatial intersection is taken.

        Parameters
        ----------
        extent : tuple (min_lon, max_lon, min_lat, max_lat)
        geometry : GeoPandas DataFrame
        country :  str or list of str
            Countries are represented by their ISO 3166-1 alpha-3 identifiers.
        season : pair of int
            First and last month of hazard-specific season within this region
        """
        self._set_geometry(extent=extent, geometry=geometry, country=country)
        self.geometry['const'] = 0
        self.shape = self.geometry.dissolve(by='const').geometry[0]
        self.season = season


    def _set_geometry(self, extent=None, geometry=None, country=None):
        self.meta = {}

        if extent is not None:
            self.meta['extent'] = extent

        if country is not None:
            self.meta['country'] = country
            if not isinstance(country, list):
                country = [country]

        self.geometry = get_country_geometries(country_names=country, extent=extent)

        if geometry is not None:
            self.meta['geometry'] = repr(geometry)
            self.geometry = gpd.overlay(self.geometry, geometry, how="intersection")


    def centroids(self, latlon=None):
        """Return centroids in this region

        Parameters
        ----------
        latlon : pair (lat, lon)
            Latitude and longitude of centroids.
            If not given, values are taken from CLIMADA's 150 arc-second base grid.

        Returns
        -------
        centroids : climada.hazard.Centroids object
        """
        if latlon is None:
            centroids = Centroids.from_base_grid(res_as=150)
            centroids.set_meta_to_lat_lon()
            latlon = centroids.lat, centroids.lon
        lat, lon = latlon
        msk = shapely.vectorized.contains(self.shape, lon, lat)
        centroids = Centroids()
        centroids.set_lat_lon(lat[msk], lon[msk])
        centroids.id = np.arange(centroids.lon.shape[0])
        return centroids


class TCRegion(HazRegion):
    """Hazard region with support for TC ocean basins"""

    def __init__(self, tc_basin=None, season=None, **kwargs):
        """Initialize TCRegion

        The given geo information must be such that everything is contained in a single
        TC ocean basin.

        Parameters
        ----------
        tc_basin : str
            TC (sub-)basin abbreviated name, such as "SIW". If not given, automatically determined
            from geometry and basin bounds.
        **kwargs : see HazRegion.__init__
        """
        self._set_geometry(**kwargs)

        if tc_basin is not None:
            df2 = get_tc_basin_geometry(tc_basin)
            self.geometry = gpd.overlay(self.geometry, df2, how="intersection")
            self.meta['tc_basin'] = tc_basin
            self.tc_basin = tc_basin

        self.geometry['const'] = 0
        self.shape = self.geometry.dissolve(by='const').geometry[0]

        if self.tc_basin is None:
            self._determine_tc_basin()

        if season is None:
            season = const.TC_BASIN_SEASONS[self.tc_basin[:2]]
        self.season = season


    def _determine_tc_basin(self):
        for basin in const.TC_SUBBASINS:
            basin_geom = get_tc_basin_geometry(basin)
            if all(basin_geom.contains(self.shape)):
                self.tc_basin = basin
                break
        if self.tc_basin is None:
            raise ValueError("Region is not contained in a single basin!")
        for tc_basin in const.TC_SUBBASINS[self.tc_basin]:
            tc_basin_geom = get_tc_basin_geometry(tc_basin)
            if all(tc_basin_geom.contains(self.shape)):
                self.tc_basin = tc_basin
                break
        LOGGER.info("Automatically determined TC basin: %s", self.tc_basin)


def get_tc_basin_geometry(tc_basin):
    """Get TC (sub-)basin geometry

    Parameters
    ----------
    tc_basin : str
        TC (sub-)basin abbreviated name, such as "SIW" or "NA".

    Returns
    -------
    df : GeoPandas DataFrame
    """
    polygons = []
    for rect in const.TC_BASIN_GEOM[tc_basin]:
        lonmin, lonmax, latmin, latmax = rect
        polygons.append(Polygon([
            (lonmin, latmin),
            (lonmin, latmax),
            (lonmax, latmax),
            (lonmax, latmin)
        ]))
    polygons = shapely.ops.unary_union(polygons)
    polygons = gpd.GeoSeries(polygons, crs=NE_CRS)
    return gpd.GeoDataFrame({'geometry': polygons}, crs=NE_CRS)