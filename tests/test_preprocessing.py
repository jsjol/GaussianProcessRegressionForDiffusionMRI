# -*- coding: utf-8 -*-


from os import makedirs, rmdir, rename, remove
from os.path import dirname, abspath, join, expanduser, exists
import numpy as np
import numpy.testing as npt
import unittest
import nibabel as nib
from dipy.core.gradients import gradient_table
from dipy.data import fetch_isbi2013_2shell
from dipy.core.gradients import GradientTable
from diGP.preprocessing import (readHCP,
                                averageb0Volumes,
                                createBrainMaskFromb0Data,
                                replaceNegativeData)


class TestReadHCP(unittest.TestCase):

    def test_fileNotFoundRaisesFileNotFoundException(self):
        pathToThisFile = dirname(abspath(__file__))
        pathToIntentionallyEmptyDirectory = join(pathToThisFile,
                                                 'intentionallyEmptyDirectory')
        makedirs(pathToIntentionallyEmptyDirectory)
        self.assertRaises(FileNotFoundError,
                          readHCP, pathToIntentionallyEmptyDirectory)
        rmdir(pathToIntentionallyEmptyDirectory)

    def test_returnsCorrect(self):
        homeDirectory = expanduser('~')
        dataDirectory = join(homeDirectory, '.dipy', 'isbi2013')

        if not exists(dataDirectory):
            fetch_isbi2013_2shell()

            oldFileNamebval = join(dataDirectory, 'phantom64.bval')
            newFileNamebval = join(dataDirectory, 'bvals.txt')
            rename(oldFileNamebval, newFileNamebval)

            oldFileNamebvecs = join(dataDirectory, 'phantom64.bvec')
            newFileNamebvecs = join(dataDirectory, 'bvecs_moco_norm.txt')
            rename(oldFileNamebvecs, newFileNamebvecs)

            oldFileNameData = join(dataDirectory, 'phantom64.nii.gz')
            newDataDirectory = join(dataDirectory, 'mri')
            makedirs(newDataDirectory)
            newFileNameData = join(newDataDirectory, 'diff_preproc.nii.gz')
            rename(oldFileNameData, newFileNameData)

        gtab, data, voxelSize = readHCP(dataDirectory)
        self.assertIsInstance(gtab, GradientTable)
        self.assertEqual(gtab.bvals.shape, np.array([64, ]))
        self.assertTrue(np.allclose(np.unique(np.round(gtab.bvals)),
                                    np.array([0., 1500., 2500.])))
        self.assertTrue(np.array_equal(gtab.bvecs.shape, np.array([64, 3])))
        self.assertEqual(voxelSize, (1., 1., 1.))

        normOfbvecs = np.sum(gtab.bvecs ** 2, 1)
        self.assertTrue(np.allclose(normOfbvecs[np.invert(gtab.b0s_mask)], 1.))

        smallDelta = 12.9
        bigDelta = 21.8
        tau = bigDelta-smallDelta / 3.0
        expectedqvals = np.sqrt(gtab.bvals / tau) / (2 * np.pi)
        self.assertTrue(np.allclose(gtab.qvals, expectedqvals))

        self.assertTrue(np.array_equal(data.shape, np.array([50, 50, 50, 64])))
        self.assertTrue(np.all(data >= 0))


class TestAverageb0Volumes(unittest.TestCase):

    def test_averageb0Volumes(self):
        mockbvals = np.array([0., 0., 1000.])
        mockbvecs = np.array([[1., 0., 0.], [0., 1., 0], [0., 0., 1.]])
        mockData = np.ones((4, 5, 6, 3))
        mockData[:, :, :, 1] = 3*np.ones((4, 5, 6))

        gtab = gradient_table(mockbvals, mockbvecs)
        averagedVolume = averageb0Volumes(mockData, gtab)
        npt.assert_array_almost_equal(averagedVolume, 2*np.ones((4, 5, 6)))


class TestCreateBrainMask(unittest.TestCase):
    dataDirectory = None
    b0Data = np.array([0])
    affine = np.eye(4)

    def setUp(self):
        homeDirectory = expanduser('~')
        self.dataDirectory = join(homeDirectory, '.dipy')
        self.b0Data = np.reshape(np.arange(3375.0), (15, 15, 15))
        self.affine = np.array([[1., 0., 0., 1.],
                                [0., 2., 0., 2.],
                                [0., 0., 3., 3.],
                                [0., 0., 0., 1.]])

    def tearDown(self):
        try:
            remove(join(self.dataDirectory, 'brainMask.nii.gz'))
        except OSError:
            pass

    def test_createBrainMaskFromb0Data(self):
        brainMask = createBrainMaskFromb0Data(self.b0Data)
        self.assertTrue(np.array_equal(brainMask.shape, self.b0Data.shape))
        # Want to test that brainMask is boolean, but couldn't find a built-in
        # function
        dataIsTrueOrFalse = np.logical_or(brainMask == 0, brainMask == 1)
        self.assertTrue(np.array_equal(dataIsTrueOrFalse,
                                       np.ones(brainMask.shape)))
        self.assertTrue(np.all(self.b0Data[brainMask == 1] > 0))

    def test_saveAndLoadBrainMask(self):
        brainMask = createBrainMaskFromb0Data(self.b0Data,
                                              affineMatrix=self.affine,
                                              saveDir=self.dataDirectory)
        loadedBrainMaskNifti = nib.load(join(self.dataDirectory,
                                             'brainMask.nii.gz'))
        self.assertTrue(np.allclose(brainMask,
                                    loadedBrainMaskNifti.get_data()))
        self.assertTrue(np.allclose(loadedBrainMaskNifti.affine, self.affine))


class TestReplaceNegativeData(unittest.TestCase):

    def test_replaceNegativeData(self):
        bvals = np.array([0., 0., 0., 1000.])
        bvecs = np.array([[1., 0., 0.],
                          [0., 1., 0],
                          [0., 0., 1.],
                          [0., 0., 1.]])
        data = np.ones((2, 2, 3, 4))
        data[:, :, :, 1] = -2*np.ones((2, 2, 3))
        data[:, :, :, 3] = -3*np.ones((2, 2, 3))

        gtab = gradient_table(bvals, bvecs)
        processedData = replaceNegativeData(data, gtab)

        expectedProcessedData = np.ones((2, 2, 3, 4))
        expectedProcessedData[:, :, :, 1] = 2/3*np.ones((2, 2, 3))
        expectedProcessedData[:, :, :, 3] = np.zeros((2, 2, 3))

        npt.assert_allclose(processedData, expectedProcessedData)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
