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

Define constants.
"""

__all__ = ['SOURCE_DIR',
           'DATA_DIR',
           'SYSTEM_DIR',
           'HAZ_DEMO_MAT',
           'HAZ_DEMO_FLDDPH',
           'HAZ_DEMO_FLDFRC',
           'ENT_TEMPLATE_XLS',
           'ONE_LAT_KM',
           'EARTH_RADIUS_KM',
           'GLB_CENTROIDS_MAT',
           'GLB_CENTROIDS_NC',
           'ISIMIP_GPWV3_NATID_150AS',
           'NATEARTH_CENTROIDS_150AS',
           'NATEARTH_CENTROIDS_360AS',
           'DEMO_GDP2ASSET',
           'RIVER_FLOOD_REGIONS_CSV',
           'TC_ANDREW_FL',
           'HAZ_DEMO_H5',
           'EXP_DEMO_H5',
           'WS_DEMO_NC']

import os
from fiona.crs import from_epsg

SOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          os.pardir))
""" climada directory """

DATA_DIR = os.path.abspath(os.path.join(SOURCE_DIR, os.pardir, 'data'))
""" Folder containing the data """

SYSTEM_DIR = os.path.abspath(os.path.join(DATA_DIR, 'system'))
""" Folder containing the data used internally """


ISIMIP_GPWV3_NATID_150AS = os.path.join(SYSTEM_DIR, 'NatID_grid_0150as.nc')
""" Compressed version of National Identifier Grid in 150 arc-seconds from
    ISIMIP project, based on GPWv3:

    ISIMIP2a/InputData/landuse_humaninfluences/population/ID_GRID/Nat_id_grid_ISIMIP.nc

    More references:

    * https://www.isimip.org/gettingstarted/input-data-bias-correction/details/13/
    * https://sedac.ciesin.columbia.edu/data/set/gpw-v3-national-identifier-grid
"""

GLB_CENTROIDS_NC = ISIMIP_GPWV3_NATID_150AS
""" For backwards compatibility, it remains available under its old name. """

GLB_CENTROIDS_MAT = os.path.join(SYSTEM_DIR, 'GLB_NatID_grid_0360as_adv_2.mat')
""" Global centroids """

NATEARTH_CENTROIDS_150AS = os.path.join(SYSTEM_DIR, 'NatEarth_Centroids_150as.hdf5')
""" Global centroids at 150 arc-seconds resolution,
    including region ids from Natural Earth."""

NATEARTH_CENTROIDS_360AS = os.path.join(SYSTEM_DIR, 'NatEarth_Centroids_360as.hdf5')
""" Global centroids at 360 arc-seconds resolution,
    including region ids from Natural Earth and distance to coast from NASA."""

ENT_TEMPLATE_XLS = os.path.join(SYSTEM_DIR, 'entity_template.xlsx')
""" Entity template in xls format."""

HAZ_TEMPLATE_XLS = os.path.join(SYSTEM_DIR, 'hazard_template.xlsx')
""" Hazard template in xls format."""

RIVER_FLOOD_REGIONS_CSV = os.path.join(SYSTEM_DIR, 'NatRegIDs.csv')
""" Look-up table for river flood module """

HAZ_DEMO_FL = os.path.join(DATA_DIR, 'demo', 'SC22000_VE__M1.grd.gz')
""" Raster file of flood over Venezuela. Model from GAR2015"""

HAZ_DEMO_FLDDPH = os.path.join(DATA_DIR, 'demo',
    'flddph_WaterGAP2_miroc5_historical_flopros_gev_picontrol_2000_0.1.nc')
""" NetCDF4 Flood depth from isimip simulations"""

HAZ_DEMO_FLDFRC = os.path.join(DATA_DIR, 'demo',
    'fldfrc_WaterGAP2_miroc5_historical_flopros_gev_picontrol_2000_0.1.nc')
""" NetCDF4 Flood fraction from isimip simulations"""

HAZ_DEMO_MAT = os.path.join(DATA_DIR, 'demo', 'atl_prob.mat')
""" Hazard demo from climada in MATLAB: hurricanes from 1851 to 2011 over
    Florida with 100 centroids.
"""

HAZ_DEMO_H5 = os.path.join(DATA_DIR, 'demo', 'tc_fl_1975_2011.h5')
""" Hazard demo in h5 format: ibtracs from 1975 to 2011 over Florida with
    2500 centroids.
"""

DEMO_GDP2ASSET = os.path.join(DATA_DIR, 'demo', 'gdp2asset_CHE_exposure.nc')
"""Exposure demo file for GDP2Asset"""

WS_DEMO_NC = [os.path.join(DATA_DIR, 'demo', 'fp_lothar_crop-test.nc'),
              os.path.join(DATA_DIR, 'demo', 'fp_xynthia_crop-test.nc')]
""" Winter storm in Europe files. These test files have been generated using
   the netCDF kitchen sink:

    ncks -d latitude,50.5,54.0 -d longitude,3.0,7.5 ./file_in.nc ./file_out.nc
"""


ENT_DEMO_TODAY = os.path.join(DATA_DIR, 'demo', 'demo_today.xlsx')
""" Entity demo present in xslx format."""

ENT_DEMO_FUTURE = os.path.join(DATA_DIR, 'demo', 'demo_future_TEST.xlsx')
""" Entity demo future in xslx format."""

EXP_DEMO_H5 = os.path.join(DATA_DIR, 'demo', 'exp_demo_today.h5')
""" Exposures over Florida """


TC_ANDREW_FL = os.path.join(DATA_DIR, 'demo',
                            'ibtracs_global_intp-None_1992230N11325.csv')
""" Tropical cyclone Andrew in Florida """


ISIMIP_NATID_TO_ISO = [
       '', 'ABW', 'AFG', 'AGO', 'AIA', 'ALB', 'AND', 'ANT', 'ARE', 'ARG', 'ARM',
    'ASM', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BFA', 'BGD', 'BGR',
    'BHR', 'BHS', 'BIH', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN',
    'BWA', 'CAF', 'CAN', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD', 'COG', 'COK',
    'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA',
    'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI', 'ESP', 'EST', 'ETH', 'FIN', 'FJI',
    'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 'GHA', 'GIB', 'GIN',
    'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG',
    'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IRL', 'IRN', 'IRQ', 'ISL',
    'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'JPN', 'KAZ', 'KEN', 'KGZ', 'KHM', 'KIR',
    'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO',
    'LTU', 'LUX', 'LVA', 'MAC', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL',
    'MKD', 'MLI', 'MLT', 'MMR', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR', 'MTQ', 'MUS',
    'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK', 'NGA', 'NIC', 'NIU', 'NLD',
    'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW',
    'PNG', 'POL', 'PRI', 'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU',
    'RUS', 'RWA', 'SAU', 'SCG', 'SDN', 'SEN', 'SGP', 'SHN', 'SJM', 'SLB', 'SLE',
    'SLV', 'SMR', 'SOM', 'SPM', 'STP', 'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SYC',
    'SYR', 'TCA', 'TCD', 'TGO', 'THA', 'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO',
    'TUN', 'TUR', 'TUV', 'TWN', 'TZA', 'UGA', 'UKR', 'URY', 'USA', 'UZB', 'VCT',
    'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM', 'ZAF', 'ZMB', 'ZWE',
]
""" ISO3166 alpha-3 codes of countries used in ISIMIP_GPWV3_NATID_150AS """


RIVER_GEO_REGIONS = {
    'NO_REGION': [
        'CYP', 'MAC', 'MCO', 'MUS', 'PLW', 'REU', 'SMR', 'SPM', 'SYC'
    ],
    # Southern Africa
    'SAF': [
        'AGO', 'BWA', 'LSO', 'NAM', 'SHN', 'SWZ', 'ZAF'
    ],
    # Central Africa (including West and East)
    'SSA': [
        'BDI', 'BEN', 'BFA', 'CAF', 'CIV', 'CMR', 'COD', 'COG', 'COM', 'CPV',
        'ERI', 'ETH', 'GAB', 'GHA', 'GIN', 'GMB', 'GNB', 'GNQ', 'KEN', 'LBR',
        'MDG', 'MLI', 'MOZ', 'MRT', 'MWI', 'MYT', 'NER', 'NGA', 'RWA', 'SDN',
        'SEN', 'SLE', 'SOM', 'STP', 'TCD', 'TGO', 'TZA', 'UGA', 'ZMB', 'ZWE'
    ],
    # Northern Africa
    'NAF': [
        'DZA', 'EGY', 'LBY', 'MAR', 'TUN'
    ],
    # Central and Northern Europe
    'EUR': [
        'ALB', 'AND', 'AUT', 'BEL', 'BIH', 'CHE', 'CZE', 'DEU', 'DNK', 'ESP',
        'FIN', 'FRA', 'FRO', 'GBR', 'GGY', 'GIB', 'GRC', 'HRV', 'HUN', 'IMN',
        'IRL', 'ISL', 'ITA', 'JEY', 'LIE', 'LUX', 'MLT', 'NLD', 'NOR', 'POL',
        'PRT', 'SCG', 'SJM', 'SVK', 'SVN', 'SWE'
    ],
    # Eastern Europe
    'EUA': [
        'ARM', 'AZE', 'BGR', 'BLR', 'EST', 'GEO', 'LTU', 'LVA', 'MDA', 'MKD',
        'ROU', 'RUS', 'UKR'
    ],
    # Arab states in Western Asia
    'ARA': [
        'ARE', 'BHR', 'DJI', 'IRN', 'IRQ', 'ISR', 'JOR', 'KWT', 'LBN', 'OMN',
        'PSE', 'QAT', 'SAU', 'SYR', 'TKM', 'TUR', 'YEM'
    ],
    # Southwest Asia
    'SWA': [
        'AFG', 'BGD', 'BTN', 'IND', 'LKA', 'MDV', 'MMR', 'NPL', 'PAK'
    ],
    # Central Asia
    'CAS': [
        'KAZ', 'KGZ', 'MNG', 'TJK', 'UZB'
    ],
    # Eastern Asia
    'CHN': [
        'CHN', 'HKG', 'JPN', 'KOR', 'PRK', 'TWN'
    ],
    # Southeast Asia
    'SEA': [
        'BRN', 'IDN', 'KHM', 'LAO', 'MYS', 'PHL', 'PNG', 'SGP', 'THA', 'TLS',
        'VNM',
    ],
    # Australia and New Zealand
    'AUS': [
        'AUS', 'NZL'
    ],
    # Pacific Island States, 1
    'PIS1': [
        'FJI', 'FSM', 'GUM', 'KIR', 'MHL', 'MNP', 'NCL', 'NFK', 'NRU', 'SLB',
        'TUV', 'VUT'
    ],
    # Pacific Island States, 2
    'PIS2': [
        'ASM', 'COK', 'NIU', 'PCN', 'PYF', 'TKL', 'TON', 'WLF', 'WSM'
    ],
    # Latin America, South
    'LAS': [
        'ARG', 'CHL', 'FLK', 'PRY', 'URY'
    ],
    # Latin America, North
    'LAN': [
        'BOL', 'BRA', 'COL', 'ECU', 'GUF', 'GUY', 'PER', 'SUR', 'TTO', 'VEN'
    ],
    # Carribbean and Central America
    'CAR': [
        'ABW', 'AIA', 'ANT', 'ATG', 'BHS', 'BLZ', 'BMU', 'BRB', 'CRI', 'CUB',
        'CYM', 'DMA', 'DOM', 'GLP', 'GRD', 'GTM', 'HND', 'HTI', 'JAM', 'KNA',
        'LCA', 'MEX', 'MSR', 'MTQ', 'NIC', 'PAN', 'PRI', 'SLV', 'TCA', 'VCT',
        'VGB', 'VIR'
    ],
    # North America, Mainland
    'NAM': [
        'CAN', 'USA'
    ],
}
""" Geographical groups of countries, used for river flood modeling """


ONE_LAT_KM = 111.12
""" Mean one latitude (in degrees) to km """

EARTH_RADIUS_KM = 6371
""" Earth radius in km """

DEF_EPSG = 4326
""" Default EPSG code """

DEF_CRS = from_epsg(DEF_EPSG)
""" Default coordinate reference system WGS 84 """
