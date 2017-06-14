# -*- coding: utf-8 -*-


import numpy as np
from dipy.sims.voxel import multi_tensor
from diGP.dataManipulations import (generateCoordinates,
                                    combineCoordinatesAndqVecs)


def generatebVecs(numbVecs):
    """Generate random b-vectors from a sphere

    Parameters:
    ----------
    numbVecs : array-like
        Number of b-vectors to generate

    Returns:
    --------
    bVecs : ndarray
        numbVecs x 3 array of b-vectors randomly sampled
        from the sphere.
    """
    bVecs = _samplesOnTheSphere(numbVecs)
    return bVecs


def generatebValsAndbVecs(uniquebVals, numbVecs):
    """Generate synthetic bval- and bvec-arrays in a format suitable for
    gradient table creation.

    Parameters:
    ----------
    uniquebVals : array-like
        An array of unique b-values (defining the radii of b-value shells)
    numbVecs : array-like
        The number of samples to generate for each b-value

    Returns:
    --------
    bVals : array
        Array of shape (N,) with each unique b-value repeated as many times as
        specified by numbVals
    bVecs : ndarray
        (N, 3) array of unit vectors

    """
    bVals = [np.ones(n) for n in numbVecs] * uniquebVals
    bVals = np.concatenate(np.asarray(bVals))
    totalNumber = np.sum(numbVecs)
    bVecs = generatebVecs(totalNumber)
    return bVals, bVecs


def generateSyntheticInputs(voxelsInEachDim, gtab,
                            qMagnitudeTransform=lambda x: x):
    """Generate inputs (i.e. features) for the machine learning algorithm.

    Parameters:
    -----------
    voxelsInEachDim : array-like
        The dimensions, (nx, ny, nz), of a 3D grid.

    gtab : GradientTable
        Specification of the diffusion MRI measurement.

    qMagnitudeTransform : function
        Function that maps q-magnitudes to corresponding features.
        Default is identity.

    Returns:
    --------
    inputs : ndarray
        (N, 7) = (nx*ny*nz*nq, 3 + 1 + 3) array of inputs.
        Each row corresponds to a single diffusion MRI measurement in
        a single voxel. It is formatted as [coordinates, qMagnitudes, bvecs].
    """
    coordinates = generateCoordinates(voxelsInEachDim)
    qMagnitudes = gtab.qvals[:, np.newaxis]
    qMagnitudeFeature = qMagnitudeTransform(qMagnitudes)
    bvecs = gtab.bvecs
    qFeatures = np.column_stack((qMagnitudeFeature, bvecs))
    return combineCoordinatesAndqVecs(coordinates, qFeatures)


def generateSyntheticOutputsFromMultiTensorModel(voxelsInEachDim,
                                                 gtab, eigenvalues, **kwargs):
    """Generate a signal simulated from a multi-tensor model for each voxel.

    Parameters:
    -----------
    voxelsInEachDim : array-like
        The dimensions, (nx, ny, nz), of a 3D grid.

    gtab : GradientTable
        Specification of the diffusion MRI measurement.

    eigenvalues : (K, 3) array
        Each tensor's eigenvalues in each row

    kwargs : dict
        Keyword arguments passed to the underlying signal generation:
        DiPy's multi_tensor().

    Returns:
    --------
    output : (nx*ny*nz*nq,) array
        Simulated outputs.
    """
    N = np.prod(voxelsInEachDim)
    numberOfMeasurements = len(gtab.bvals)
    output = np.zeros((N, numberOfMeasurements))
    for i in range(N):
        output[i, :] = multi_tensor(gtab, eigenvalues, S0=1., **kwargs)[0]
    return output.flatten(order='C')[:, None]


def _samplesOnTheSphere(n):
    """Generate random samples from the 3D unit sphere.

    Parameters
    ----------
    n : int
        Number of samples.

    Returns
    -------
    out : ndarray
        n x 3 array where each row corresponds to a point on the unit sphere.
    """
    randomVectors = np.random.randn(n, 3)
    norms = np.linalg.norm(randomVectors, axis=1)
    return randomVectors / norms[:, np.newaxis]
