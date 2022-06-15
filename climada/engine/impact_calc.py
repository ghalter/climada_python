"""
This file is part of CLIMADA.

Copyright (C) 2017 ETH Zurich, CLIMADA contributors listed in AUTHORS.

CLIMADA is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free
Software Foundation, version 3.

CLIMADA is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with CLIMADA. If not, see <https://www.gnu.org/licenses/>.

---

Define Impact and ImpactFreqCurve classes.
"""

__all__ = ['ImpactCalc']

import logging
import numpy as np
from scipy import sparse
import geopandas as gpd

from climada import CONFIG
from climada.engine import Impact

LOGGER = logging.getLogger(__name__)

class ImpactCalc():
    """
    Class to compute impacts from exposures, impact function set and hazard
    """

    def __init__(self,
                 exposures,
                 impfset,
                 hazard,
                 imp_mat=None):
        """
        Initialize an ImpactCalc object.

        The dimension of the imp_mat variable must be compatible with the
        exposures and hazard objects.

        Parameters
        ----------
        exposures : climada.entity.Exposures
            exposure used to compute imp_mat
        impf_set: climada.entity.ImpactFuncSet
            impact functions set used to compute imp_mat
        hazard : climada.Hazard
            hazard used to compute imp_mat
        imp_mat : sparse.csr_matrix, optional
            matrix num_events x num_exp with impacts.
            Default is an empty matrix.

        Returns
        -------
        None.

        """

        self.exposures = exposures
        self.impfset = impfset
        self.hazard = hazard
        self.imp_mat = imp_mat if imp_mat is not None else sparse.csr_matrix((0, 0))
        self.n_exp_pnt = self.exposures.gdf.shape[0]
        self.n_events = self.hazard.size

    @property
    def deductible(self):
        """
        Deductibles from the exposures. Returns empty array
        if no deductibles defined.

        Returns
        -------
        np.array
            The deductible per exposure point

        """
        if 'deductible' in self.exposures.gdf.columns:
            return self.exposures.gdf['deductible'].to_numpy()
        return np.array([])

    @property
    def cover(self):
        """
        Covers from the exposures. Returns empty array if no covers defined.

        Returns
        -------
        np.array
            The cover per exposure point

        """
        if 'cover' in self.exposures.gdf.columns:
            return self.exposures.gdf['cover'].to_numpy()
        return np.array([])

    def impact(self, save_mat=True):
        """Compute the impact of a hazard on exposures.

        Parameters
        ----------
        save_mat : bool
            if true, save the total impact matrix (events x exposures)

        Examples
        --------
            >>> haz = Hazard.from_mat(HAZ_DEMO_MAT)  # Set hazard
            >>> impfset = ImpactFuncSet.from_excel(ENT_TEMPLATE_XLS) # Set impact functions
            >>> exp = Exposures(pd.read_excel(ENT_TEMPLATE_XLS)) # Set exposures
            >>> impcalc = ImpactCal(exp, impfset, haz)
            >>> imp = impcalc.insured_impact()
            >>> imp.aai_agg

        Note
        ----
        Deductible and/or cover values in the exposures are ignored.
        """
        impf_col = self.exposures.get_impf_column(self.hazard.haz_type)
        exp_gdf = self.minimal_exp_gdf(impf_col)
        LOGGER.info('Calculating impact for %s assets (>0) and %s events.',
                    self.n_events, self.n_events)
        imp_mat_gen = self.imp_mat_gen(exp_gdf, impf_col)
        return self._return_impact(imp_mat_gen, save_mat)

#TODO: make a better impact matrix generator for insured impacts when
# the impact matrix is already present
    def insured_impact(self, save_mat=False):
        """Compute the impact of a hazard on exposures with a deductible and/or
        cover.

        For each exposure point, the impact per event is obtained by
        substracting the deductible (and is maximally equal to the cover).

        Parameters
        ----------
        save_mat : bool
            if true, save the total impact matrix (events x exposures)

        Examples
        --------
            >>> haz = Hazard.from_mat(HAZ_DEMO_MAT)  # Set hazard
            >>> impfset = ImpactFuncSet.from_excel(ENT_TEMPLATE_XLS) # Set impact functions
            >>> exp = Exposures(pd.read_excel(ENT_TEMPLATE_XLS)) # Set exposures
            >>> impcalc = ImpactCal(exp, impfset, haz)
            >>> imp = impcalc.insured_impact()
            >>> imp.aai_agg

        See also
        --------
        apply_deductible_to_mat:
            apply deductible to impact matrix
        apply_cover_to_mat:
            apply cover to impact matrix
        """
        if self.cover.size == 0 and self.deductible.size == 0:
            raise AttributeError("Neither cover nor deductible defined."
                                 "Please set exposures.gdf.cover"
                                 "and/or exposures.gdf.deductible")
        impf_col = self.exposures.get_impf_column(self.hazard.haz_type)
        exp_gdf = self.minimal_exp_gdf(impf_col)
        LOGGER.info('Calculating impact for %s assets (>0) and %s events.',
                    exp_gdf.size, self.hazard.size)

        if self.imp_mat.size == 0:
            imp_mat_gen = self.imp_mat_gen(exp_gdf, impf_col)
        else:
            imp_mat_gen = ((self.imp_mat, np.arange(1, len(exp_gdf))) for n in range(1))
        ins_mat_gen = self.insured_mat_gen(imp_mat_gen, exp_gdf, impf_col)
        return self._return_impact(ins_mat_gen, save_mat)

    def _return_impact(self, imp_mat_gen, save_mat):
        """Return an impact object from an impact matrix generator

        Parameters
        ----------
        imp_mat_gen : generator
            Generator of impact matrix and corresponding exposures index
        save_mat : boolean
            if true, save the impact matrix

        Returns
        -------
        Impact
            Impact Object initialize from the impact matrix

        See Also
        --------
        imp_mat_gen: impact matrix generator
        insured_mat_gen: insured impact matrix generator

        """
        if save_mat:
            self.imp_mat = self.stitch_impact_matrix(imp_mat_gen)
            at_event, eai_exp, aai_agg = self.risk_metrics(self.imp_mat, self.hazard.frequency)
        else:
            at_event, eai_exp, aai_agg = self.stitch_risk_metrics(imp_mat_gen)
        return Impact.from_eih(
            self.exposures, self.impfset, self.hazard,
            at_event, eai_exp, aai_agg, self.imp_mat
            )

    def minimal_exp_gdf(self, impf_col):
        """Get minimal exposures geodataframe for impact computation

        Parameters
        ----------
        exposures : climada.entity.Exposures
        hazard : climada.Hazard
        impf_col: stirng
            name of the impact function column in exposures.gdf

        """
        self.exposures.assign_centroids(self.hazard, overwrite=False)

        mask = (
            (self.exposures.gdf.value.values != 0)
            & (self.exposures.gdf[self.hazard.centr_exp_col].values >= 0)
        )
        exp_gdf = gpd.GeoDataFrame({
            col: self.exposures.gdf[col].values[mask]
            for col in ['value', impf_col, self.hazard.centr_exp_col]
        })
        if exp_gdf.size == 0:
            LOGGER.warning("No exposures with value >0 in the vicinity of the hazard.")
        return exp_gdf

    def imp_mat_gen(self, exp_gdf, impf_col):
        """
        Generator of impact sub-matrices and correspoding exposures indices

        The exposures gdf is decomposed into chunks that fit into the max
        defined memory size. For each chunk, the impact matrix is computed
        and returned, together with the corresponding exposures points index.

        Parameters
        ----------
        exp_gdf : GeoDataFrame
            Geodataframe of the exposures with columns required for impact
            computation.
        impf_col : string
            name of the desired impact column in the exposures.

        Raises
        ------
        ValueError
            if the hazard is larger than the memory limit

        Yields
        ------
        scipy.sparse.crs_matrix, np.ndarray
            impact matrix and corresponding exposures indices for each chunk.

        """

        def _chunk_exp_idx(haz_size, idx_exp_impf):
            max_size = CONFIG.max_matrix_size.int()
            if haz_size > max_size:
                raise ValueError(
                    f'Increase max_matrix_size configuration parameter to > {self.hazard.size}')
            n_chunks = np.ceil(haz_size * len(idx_exp_impf) / max_size)
            return np.array_split(idx_exp_impf, n_chunks)

        for impf_id in exp_gdf[impf_col].dropna().unique():
            impf = self.impfset.get_func(haz_type=self.hazard.haz_type, fun_id=impf_id)
            idx_exp_impf = (exp_gdf[impf_col].values == impf_id).nonzero()[0]
            for exp_idx in _chunk_exp_idx(self.hazard.size, idx_exp_impf):
                exp_values = exp_gdf.value.values[exp_idx]
                cent_idx = exp_gdf[self.hazard.centr_exp_col].values[exp_idx]
                yield (self.impact_matrix(exp_values, cent_idx, impf), exp_idx)

    def insured_mat_gen(self, imp_mat_gen, exp_gdf, impf_col):
        """
        Generator of insured impact sub-matrices (with applied cover and deductible)
        and corresponding exposures indices
        """
        for mat, exp_idx in imp_mat_gen:
            impf_id = exp_gdf[impf_col][exp_idx].unique()[0]
            deductible = self.deductible[exp_idx]
            cent_idx = exp_gdf[self.hazard.centr_exp_col].values[exp_idx]
            impf = self.impfset.get_func(haz_type=self.hazard.haz_type, fun_id=impf_id)
            mat = self.apply_deductible_to_mat(mat, deductible, self.hazard, cent_idx, impf)
            cover = self.cover[exp_idx]
            mat = self.apply_cover_to_mat(mat, cover)
            yield (mat, exp_idx)

    def impact_matrix(self, exp_values, cent_idx, impf):
        """
        Compute the impact matrix for given exposure values,
        assigned centroids, a hazard, and one impact function.

        Parameters
        ----------
        exp_values : np.array
            Exposure values
        cent_idx : np.array
            Hazard centroids assigned to each exposure location
        hazard : climada.Hazard
           Hazard object
        impf : climada.entity.ImpactFunc
            one impactfunction comon to all exposure elements in exp_gdf

        Returns
        -------
        scipy.sparse.csr_matrix
            Impact per event (rows) per exposure point (columns)
        """
        n_centroids = cent_idx.size
        mdr = self.hazard.get_mdr(cent_idx, impf)
        fract = self.hazard.get_fraction(cent_idx)
        exp_values_csr = sparse.csr_matrix(
            (exp_values, np.arange(n_centroids), [0, n_centroids]),
            shape=(1, n_centroids))
        return fract.multiply(mdr).multiply(exp_values_csr)

    def stitch_impact_matrix(self, imp_mat_gen):
        """
        Make an impact matrix from an impact sub-matrix generator
        """
        data, row, col = np.hstack([
            (mat.data, mat.nonzero()[0], idx[mat.nonzero()[1]])
            for mat, idx in imp_mat_gen
            ])
        return sparse.csr_matrix(
            (data, (row, col)), shape=(self.n_events, self.n_exp_pnt)
            )

    def stitch_risk_metrics(self, imp_mat_gen):
        """
        Compute the impact metrics from an impact sub-matrix generator
        """
        at_event = np.zeros(self.n_events)
        eai_exp = np.zeros(self.n_exp_pnt)
        for sub_imp_mat, exp_idx in imp_mat_gen:
            at_event += self.at_event_from_mat(sub_imp_mat)
            eai_exp[exp_idx] += self.eai_exp_from_mat(sub_imp_mat, self.hazard.frequency)
        aai_agg = self.aai_agg_from_eai_exp(eai_exp)
        return at_event, eai_exp, aai_agg

    @staticmethod
    def apply_deductible_to_mat(mat, deductible, hazard, cent_idx, impf):
        """
        Apply a deductible per exposure point to an impact matrix at given
        centroid points for given impact function.

        All exposure points must have the same impact function. For different
        impact functions apply use this method repeatedly on the same impact
        matrix.

        Parameters
        ----------
        imp_mat : scipy.sparse.csr_matrix
            impact matrix (events x exposure points)
        deductible : np.array()
            deductible for each exposure point
        hazard : climada.Hazard
            hazard used to compute the imp_mat
        cent_idx : np.array()
            index of centroids associated with each exposure point
        impf : climada.entity.ImpactFunc
            impact function associated with the exposure points

        Returns
        -------
        imp_mat : scipy.sparse.csr_matrix
            impact matrix with applied deductible

        """
        paa = hazard.get_paa(cent_idx, impf)
        mat -= paa.multiply(sparse.csr_matrix(deductible))
        mat.eliminate_zeros()
        return mat

    @staticmethod
    def apply_cover_to_mat(mat, cover):
        """
        Apply cover to impact matrix.

        The impact data is clipped to the range [0, cover]. The cover is defined
        per exposure point.

        Parameters
        ----------
        imp_mat : scipy.sparse.csr_matrix
            impact matrix
        cover : np.array()
            cover per exposures point (columns of imp_mat)

        Returns
        -------
        imp_mat : scipy.sparse.csr_matrix
            impact matrix with applied cover

        """
        mat.data = np.clip(mat.data, 0, cover[mat.nonzero()[1]])
        mat.eliminate_zeros()
        return mat

    @staticmethod
    def eai_exp_from_mat(mat, freq):
        """
        Compute impact for each exposures from the total impact matrix

        Parameters
        ----------
        imp_mat : sparse.csr_matrix
            matrix num_events x num_exp with impacts.
        frequency : np.array
            annual frequency of events
        Returns
        -------
        eai_exp : np.array
            expected annual impact for each exposure
        """
        n_events = freq.size
        freq_csr = sparse.csr_matrix(
            (freq, np.zeros(n_events), np.arange(n_events + 1)),
            shape=(n_events, 1))
        return mat.multiply(freq_csr).sum(axis=0).A1

    @staticmethod
    def at_event_from_mat(mat):
        """
        Compute impact for each hazard event from the total impact matrix
        Parameters
        ----------
        imp_mat : sparse.csr_matrix
            matrix num_events x num_exp with impacts.
        Returns
        -------
        at_event : np.array
            impact for each hazard event
        """
        return np.squeeze(np.asarray(np.sum(mat, axis=1)))

    @staticmethod
    def aai_agg_from_eai_exp(eai_exp):
        """
        Aggregate impact.eai_exp

        Parameters
        ----------
        eai_exp : np.array
            expected annual impact for each exposure point

        Returns
        -------
        float
            average annual impact aggregated
        """
        return np.sum(eai_exp)

    @classmethod
    def risk_metrics(cls, mat, freq):
        """
        Compute risk metricss eai_exp, at_event, aai_agg
        for an impact matrix and a frequency vector.

        Parameters
        ----------
        mat : sparse.csr_matrix
            matrix num_events x num_exp with impacts.
        freq : np.array
            array with the frequency per event

        Returns
        -------
        eai_exp: np.array
            expected annual impact at each exposure point
        at_event: np.array()
            total impact for each event
        aai_agg : float
            average annual impact aggregated over all exposure points
        """
        eai_exp = cls.eai_exp_from_mat(mat, freq)
        at_event = cls.at_event_from_mat(mat)
        aai_agg = cls.aai_agg_from_eai_exp(eai_exp)
        return at_event, eai_exp, aai_agg
