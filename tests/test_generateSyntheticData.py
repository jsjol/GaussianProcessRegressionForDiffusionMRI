# -*- coding: utf-8 -*-


import unittest
import unittest.mock as mock
import numpy as np
import numpy.testing as npt
from diGP.dataManipulations import generateCoordinates
from diGP.generateSyntheticData import (generatebVecs,
                                        generatebValsAndbVecs,
#                                        combineCoordinatesAndqVecs,
                                        generateSyntheticInputs,
                                        generateSyntheticOutputsFromMultiTensorModel)


class test_generateSyntheticData(unittest.TestCase):

    def test_bvecGeneration(self):
        np.random.seed(0)  # Fix random number generation for repeatibility
        numbVecs = 2
        syntheticbVecs = generatebVecs(numbVecs)
        npt.assert_equal(syntheticbVecs.shape, (numbVecs, 3))
        self.assertFalse(np.allclose(
            syntheticbVecs[0, :], syntheticbVecs[1, :]))

    @mock.patch('diGP.generateSyntheticData.generatebVecs')
    def test_bvecAndbValGeneration(self, mock_generatebVecs):
        uniquebVals = np.array([100, 400])
        numbVals = np.array([2, 3])
        totalNumberOfSamples = np.sum(numbVals)
        expectedbVals = np.array([100, 100, 400, 400, 400])
        expectedbVecs = np.array([[1, 0, 0],
                                  [0, 1, 0],
                                  [1, 0, 0],
                                  [0, 1, 0],
                                  [0, 0, 1]])
        mock_generatebVecs.return_value = expectedbVecs
        bVals, bVecs = generatebValsAndbVecs(uniquebVals, numbVals)
        mock_generatebVecs.assert_called_with(totalNumberOfSamples)
        npt.assert_array_equal(bVals, expectedbVals)
        npt.assert_array_equal(bVecs, expectedbVecs)

    @mock.patch('diGP.dataManipulations.generateCoordinates')
    def test_generateSyntheticInputs(self, mock_generateCoordinates):
        qMagnitudes = np.array([0, 5])
        bvecs = np.array([[0, 0, 0],
                          [0, 0, 1]])
        mock_gtab = mock.MagicMock(qvals=qMagnitudes, bvecs=bvecs)
        (nx, ny, nz) = (1, 1, 2)
        expectedCoordinates = np.array([[0, 0, 0],
                                        [0, 0, 1]])
        expectedResult = np.vstack(
            (np.r_[expectedCoordinates[0, :], qMagnitudes[0], bvecs[0, :]],
             np.r_[expectedCoordinates[0, :], qMagnitudes[1], bvecs[1, :]],
             np.r_[expectedCoordinates[1, :], qMagnitudes[0], bvecs[0, :]],
             np.r_[expectedCoordinates[1, :], qMagnitudes[1], bvecs[1, :]]))

        mock_generateCoordinates.return_value = expectedCoordinates
        syntheticInputs = generateSyntheticInputs((nx, ny, nz), mock_gtab)
        npt.assert_array_equal(syntheticInputs, expectedResult)

    @mock.patch('diGP.dataManipulations.generateCoordinates')
    def test_generateSyntheticInputsWithTransform(self,
                                                  mock_generateCoordinates):
        qMagnitudes = np.array([0, 5])
        bvecs = np.array([[0, 0, 0],
                          [0, 0, 1]])
        mock_gtab = mock.MagicMock(qvals=qMagnitudes, bvecs=bvecs)
        (nx, ny, nz) = (1, 1, 2)
        expectedCoordinates = np.array([[0, 0, 0],
                                        [0, 0, 1]])
        expectedResult = np.vstack(
            (np.r_[expectedCoordinates[0, :], qMagnitudes[0] + 1, bvecs[0, :]],
             np.r_[expectedCoordinates[0, :], qMagnitudes[1] + 1, bvecs[1, :]],
             np.r_[expectedCoordinates[1, :], qMagnitudes[0] + 1, bvecs[0, :]],
             np.r_[expectedCoordinates[1, :], qMagnitudes[1] + 1, bvecs[1, :]]))

        mock_generateCoordinates.return_value = expectedCoordinates
        syntheticInputs = generateSyntheticInputs(
            (nx, ny, nz), mock_gtab, qMagnitudeTransform=lambda x: x + 1)
        npt.assert_array_equal(syntheticInputs, expectedResult)

    @mock.patch('diGP.generateSyntheticData.multi_tensor')
    def test_generateSyntheticOutputsFromMultiTensorModel(self,
                                                          mock_multi_tensor):
        bvals = np.array([0, 1000])
        bvecs = np.array([[0, 0, 0],
                          [0, 0, 1]])
        mock_gtab = mock.MagicMock(bvals=bvals, bvecs=bvecs)
        tensorEigenvalues = np.array([[1, 2, 3], [1, 2, 3]])
        fractions = np.array([60, 40])
        mockSignal = np.arange(len(bvals))
        mock_multi_tensor.return_value = [mockSignal, None]
        (nx, ny, nz) = (2, 2, 2)
        syntheticOutputs = generateSyntheticOutputsFromMultiTensorModel(
            (nx, ny, nz), mock_gtab, tensorEigenvalues, fractions=fractions)
        mock_multi_tensor.assert_called_with(mock_gtab,
                                             tensorEigenvalues, S0=1.,
                                             fractions=fractions)
        self.assertTrue(mock_multi_tensor.call_count == nx * ny * nz)
        npt.assert_array_equal(syntheticOutputs,
                               np.tile(mockSignal, (nx * ny * nz,))[:, None])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
