from __future__ import print_function
import xarray as xr
import numpy as np
# import time
import os
import os.path
from xarrayutils.numpy_utils import interp_map_regular_grid
from .utils import writable_mds_store
from dask.diagnostics import ProgressBar


def aviso_validmask(da, xi, yi):
    x = da.lon.data
    y = da.lat.data
    validmask_coarse = ~xr.ufuncs.isnan(da).all(dim='time').data.compute()
    validmask_fine = interp_map_regular_grid(validmask_coarse, x, y, xi, yi)
    return np.isclose(validmask_fine, 1.0)


def block_interpolate(array, x, y, xi, yi):
    a = interp_map_regular_grid(np.squeeze(array), x, y, xi, yi)
    return a[np.newaxis, :, :]


def interpolate_aviso(ds, XC, XG, YC, YG,
                      debug=True, verbose=True):

    """Interpolate aviso dataset onto model coordinates (regular lat lon grid)

    PARAMETERS
    ----------
    ds : xarray Dataset from reading in Aviso data
        (e.g. from aviso_products.merge_aviso)

    XC : numpy.array Longitude at cell center (needs to be a vector)

    XG : numpy.array Longitude at cell boundary

    YC : numpy.array Latitude at cell center

    YG : numpy.array Latitude at cell boundary

    RETURNS
    -------
    ds_interpolated : xarray Dataset with interpolated values
    validmask : indicates data points that were not interpolated
    """

    x = ds.lon.data
    y = ds.lat.data
    nx = len(XG)
    ny = len(YC)

    #  Velocities near the coast are padded with zeros and then interpolated
    u_interpolated = ds.u.fillna(0).data.map_blocks(block_interpolate, x, y,
                                                    XG, YC,
                                                    dtype=np.float64,
                                                    chunks=(1, ny, nx))

    v_interpolated = ds.v.fillna(0).data.map_blocks(block_interpolate, x, y,
                                                    XC, YG,
                                                    dtype=np.float64,
                                                    chunks=(1, ny, nx))

    return u_interpolated, v_interpolated


def aviso_store_daily(u, v, odir, verbose=True):
    if not os.path.exists(odir):
        os.mkdir(odir)
    iters = range(u.shape[0])
    uvel_store = writable_mds_store(os.path.join(odir, 'uvel'), iters)
    vvel_store = writable_mds_store(os.path.join(odir, 'vvel'), iters)

    if verbose:
        print('Writing interpolated u velocities to ' + odir)
    with ProgressBar():
        u.store(uvel_store)

    if verbose:
        print('Writing interpolated v velocities to ' + odir)
    with ProgressBar():
        v.store(vvel_store)


# def combine_validmask(data_dir, shape=None, debug=False):
#     fnames = []
#     for dirpath, dirnames, filenames in os.walk(data_dir):
#         for filename in [f for f in filenames if f == 'validmask.bin']:
#             print('found validmask at '+os.path.join(dirpath, filename))
#             fnames.append(os.path.join(dirpath, filename))
#     if debug:
#         print('data_dir', data_dir)
#         print(fnames)
#
#     if shape:
#         masks = np.array([readbin(f, shape) for f in fnames])
#     else:
#         raise RuntimeWarning('When shape is not given')
#
#     combo = np.all(np.stack(masks, axis=2), axis=2)
#
#     fpath = data_dir+'/validmask_combined.bin'
#     writebin(combo, fpath)
#     print('--- combined validmask written to '+fpath+' ---')
