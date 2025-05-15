History
=======

`0.3.0`_ (2025-04-11)
--------------------------------------------------------------------------------------------

**Additions**

- Updated eccodes to version 2.38.3 which includes a binary distribution in PyPI.
- The python package is now pushed to PyPI.
- ``ogd_api``:

  - Added ``get_collection_asset_url`` function to fetch pre-signed URLs for static assets from a STAC collection.
  - ``download_from_ogd`` function performs checksum verification.

- ``mars``:

  - Added default number of levels for icon and kenda models.
  - Added support for bounding box feature extraction requests.

**Fixes**

- ``regrid``:

  - ``regrid`` and ``iconremap`` functions now correctly set the metadata section 3 for destinations grids in the CRS UTM 32N (Switzerland).

**Breaking Changes**

- The ``geo_coords_urls.yaml`` file containing pre-signed URLs for coordinate files has been removed. Coordinate URLs are now resolved dynamically using the new ``get_collection_asset_url`` function.
- The URL domain in ``ogd_api`` has been changed from the integration to the production environment.
- The eccodes definitions are installed using the ``eccodes-cosmo-resources-python`` package from PyPI.


`0.2.0`_ (2025-03-20)
------------------------------------------------------------------------------------------------

**Additions**

- ``cli``: Added subcommand for the regrid operator
- ``data_source``:

  - Added ``URLDataSource``, ``FDBDataSource``, ``FileDataSource``, ``PolytopeDataSource`` as implementations of ``DataSource``
  - ``retrieve`` accepts an argument of type ``mars.Request``

- ``grib_decoder``:

  - Added ``save`` function
  - ``load`` supports the ICON native grid
  - Added ``geo_coords`` optional argument to the ``load`` function

- ``mars``: Added ``feature`` attribute to the ``mars.Request`` class
- ``mch_model_data``: Added ``archive_to_fdb`` function
- ``ogd_api``:

  - Added ``get_from_ogd`` function
  - Added ``ogd_api.Request`` class

- ``operators``:

  - ``regrid``: Added ``icon2rotlatlon``, ``icon2geolatlon`` and ``iconremap`` functions
  - Added ``crop`` module

**Breaking Changes**

- The constants module is renamed to physical constants and the ``pc_`` prefix is dropped in favour of aliasing the module to ``pc`` at the call sites.
- The grib definitions context is no longer derived from the request model attribute.
  In practice, all defined models required the cosmo definitions as IFS grib data does not define the model mars key.
  Setting ``data_scope`` config to ``ifs`` to disable the cosmo definitions context remains possible.
- ``data_source.DataSource`` is now an abstract base class.
- Renamed dimension ``time`` to ``lead_time`` and changed its type from ``int`` to ``numpy.timedelta64[ns]``.
- Added dimension ``ref_time`` with type ``numpy.datetime64[ns]``.
- ``DataArray`` objects representing a field no longer have the ``message`` attribute but now have a ``metadata`` attribute that is an instance of ``StandAloneGribMetadata`` from earthkit-data.
- ``FDBDataSource``, ``mch_model_data.get_from_fdb`` and ``mch_model_data.archive_to_fdb`` require the ``fdb`` extra dependency.
- ``PolytopeDataSource`` and ``mch_mode_data.get_from_polytope`` require the ``polytope`` extra dependency.
- The ``operators.regrid`` module now requires the ``regrid`` extra dependencies.



`0.2.0-rc3 <https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.2.0-rc2..v0.2.0-rc3>`_ (2023-12-18)
----------------------------------------------------------------------------------------------------------------------------

- Added vertical interpolation operator ``interpolate_k2any``
- Testing data marker determines the test data that should be used
- Removed the ``system_definitions`` module


`0.2.0-rc2`_ (2023-12-11)
----------------------------------------------------------------------------------------------------------------------------

- Added ``product.run_products`` function
- Updated field mappings
- Data cache will inject the step and number in the request depending on the file pattern
- ``mars.Request`` now supports multiple params


`0.2.0-rc1`_ (2023-12-01)
------------------------------------------------------------------------------------------------------------------------

- Added support for the FDB data source
- Added support for running tests on balfrin (FDB only)
- Added modules:
    - ``config``: manage configuration
    - ``data_cache``: support fieldextra testing from FDB
    - ``data_source``: enable reading from files or from FDB
    - ``mars``: mars request validation
    - ``product``: product description
    - ``tasking``: dask delayed wrapper
- Added operators:
    - ``atmo``
    - ``gis``
    - ``lateral_operators``
    - ``regrid``
    - ``relhum``
    - ``time_operators``
    - ``wind``
- Changed: flexpart operator no longer uses cosmo naming conventions
- **Breaking:** removed the ``load_fields`` method from the ``GribReader`` class
- **Breaking:** the ``load`` method of ``GribReader`` now takes a mapping of labels to requests and returns a mapping of labels to ``xarray.DataArray``


`0.1.0`_ (2023-07-11)
-----------------------------------------------------------------------------------------------------

- Added operators:
    * ``brn``
    * ``curl``
    * ``destagger``
    * ``diff``
    * ``flexpart`` (for IFS model output)
    * ``hzerocl``
    * ``omega_slope``
    * ``pot_vortic``
    * ``rho``
    * ``theta``
    * ``thetav``
    * ``time_rate``
    * ``interpolate_k2p``
    * ``interpolate_k2theta``
    * ``minmax_k``
    * ``integrate_k``
- Added ``ninjo_k2th`` product
- Added GRIB data loader based on ``earthkit-data``

.. _0.3.0: https://github.com/MeteoSwiss/meteodata-lab/compare/v0.2.0..v0.3.0
.. _0.2.0: https://github.com/MeteoSwiss/meteodata-lab/compare/v0.2.0-rc3..v0.2.0
.. _0.2.0-rc3: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.2.0-rc2..v0.2.0-rc3
.. _0.2.0-rc2: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.2.0-rc1..v0.2.0-rc2
.. _0.2.0-rc1: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.1.0..v0.2.0-rc1
.. _0.1.0: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/tree/v0.1.0
