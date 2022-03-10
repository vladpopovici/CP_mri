#   -*- coding: utf-8 -*-
#
#  --------------------------------------------------------------------
#  Copyright (c) 2022 Vlad Popovici <popovici@bioxlab.org>
#
#  Licensed under the MIT License. See LICENSE file in root folder.
#  --------------------------------------------------------------------

__author__ = "Vlad Popovici <popovici@bioxlab.org>"
__version__ = 0.2
__all__ = ['MRI']

import shapely.geometry as shg
import shapely.affinity as sha
import zarr
import pathlib
import numpy as np


#####
class MRI(object):
    """MultiResolution Image - a simple and convenient interface to access pixels from a
    pyramidal image. The image is supposed to by stored in ZARR format and to have an
    attributre 'pyramid' describing the properties of the pyramid levels. There is no
    information related to resolutions etc, these are charaterstic for a slide image -
    see ComPath.WSIInfo.

    Args:
        path (str): folder with a ZARR store providing the levels (indexed 0, 1, ...)
        of the pyramid

    Attributes:
        _path (Path)
        _pyramid (dict)
    """

    def __init__(self, path: str):
        self._path = pathlib.Path(path)

        with zarr.open_group(self._path, mode='r') as z:
            self._pyramid = z.attrs['pyramid']

        self._pyramid_levels = np.zeros((2, len(self._pyramid)), dtype=int)
        self._downsample_factors = np.zeros((len(self._pyramid)), dtype=int)
        for p in self._pyramid:
            self._pyramid_levels[:, p['level']] = [p['width'], p['height']]
            self._downsample_factors[p['level']] = p['downsample_factor']

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def widths(self) -> np.array:
        # All widths for the pyramid levels
        return self._pyramid_levels[0, :]

    @property
    def heights(self) -> np.array:
        # All heights for the pyramid levels
        return self._pyramid_levels[1, :]

    def extent(self, level: int = 0) -> (int, int):
        # width, height for a given level
        return tuple(self._pyramid_levels[:, level])

    @property
    def nlevels(self) -> int:
        return self._pyramid_levels.shape[1]

    def between_level_scaling_factor(self, from_level: int, to_level: int) -> float:
        """Return the scaling factor for converting coordinates (magnification)
        between two levels in the MRI.

        Args:
            from_level (int): original level
            to_level (int): destination level

        Returns:
            float
        """
        f = self._downsample_factors[from_level] / self._downsample_factors[to_level]

        return f

    def convert_px(self, point, from_level, to_level):
        """Convert pixel coordinates of a point from <from_level> to
        <to_level>

        Args:
            point (tuple): (x,y) coordinates in <from_level> plane
            from_level (int): original image level
            to_level (int): destination level

        Returns:
            x, y (float): new coodinates - no rounding is applied
        """
        if from_level == to_level:
            return point  # no conversion is necessary
        x, y = point
        f = self.between_level_scaling_factor(from_level, to_level)
        x *= f
        y *= f

        return x, y

    def get_region_px(self, x0: int, y0: int,
                      width: int, height: int,
                      level: int = 0, as_type=np.uint8) -> np.array:
        """Read a region from the image source. The region is specified in
            pixel coordinates.

            Args:
                x0, y0 (long): top left corner of the region (in pixels, at the specified
                level)
                width, height (long): width and height (in pixels) of the region.
                level (int): the magnification level to read from
                as_type: type of the pixels (default numpy.uint8)

            Returns:
                a numpy.ndarray
        """

        if level < 0 or level >= self.nlevels:
            raise RuntimeError("requested level does not exist")

        # check bounds:
        if x0 >= self.widths[level] or y0 >= self.heights[level] or \
                x0 + width > self.widths[level] or \
                y0 + height > self.heights[level]:
            raise RuntimeError("region out of layer's extent")

        with zarr.open_group(self.path, mode='r') as zarr_root:
            img = np.array(zarr_root[str(level)][y0:y0 + height, x0:x0 + width, :], dtype=as_type)

        return img

    def get_plane(self, level: int = 0, as_type=np.uint8) -> np.array:
        """Read a whole plane from the image pyramid and return it as a Numpy array.

        Args:
            level (int): pyramid level to read
            as_type: type of the pixels (default numpy.uint8)

        Returns:
            a numpy.ndarray
        """
        if level < 0 or level >= self.nlevels:
            raise RuntimeError("requested level does not exist")

        with zarr.open_group(self.path, mode='r') as zarr_root:
            img = np.array(zarr_root[str(level)][...], dtype=as_type)

        return img

    def get_polygonal_region_px(self, contour: shg.Polygon, level: int,
                                border: int = 0, as_type=np.uint8) -> np.ndarray:
        """Returns a rectangular view of the image source that minimally covers a closed
        contour (polygon). All pixels outside the contour are set to 0.

        Args:
            contour (shapely.geometry.Polygon): a closed polygonal line given in
                terms of its vertices. The contour's coordinates are supposed to be
                precomputed and to be represented in pixel units at the desired level.
            level (int): image pyramid level
            border (int): if > 0, take this many extra pixels in the rectangular
                region (up to the limits on the image size)
            as_type: pixel type for the returned image (array)

        Returns:
            a numpy.ndarray
        """
        x0, y0, x1, y1 = [int(_z) for _z in contour.bounds]
        x0, y0 = max(0, x0 - border), max(0, y0 - border)
        x1, y1 = min(x1 + border, self.extent(level)[0]), \
                 min(y1 + border, self.extent(level)[1])
        # Shift the annotation such that (0,0) will correspond to (x0, y0)
        contour = sha.translate(contour, -x0, -y0)

        # Read the corresponding region
        img = self.get_region_px(x0, y0, x1 - x0, y1 - y0, level, as_type=np.uint8)

        # mask out the points outside the contour
        for i in np.arange(img.shape[0]):
            # line mask
            lm = np.zeros((img.shape[1],), dtype=img.dtype)
            j = [_j for _j in np.arange(img.shape[1]) if shg.Point(_j, i).within(contour)]
            lm[j] = 1
            img[i,] = img[i,] * lm

        return img

##
