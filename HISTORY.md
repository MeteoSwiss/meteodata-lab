# History

## [0.2.0] (2025-03-20)

### Additions

- Added `save` function to `grib_decoder` module
- Added `operators.crop` module
- Added `feature` attribute to the `mars.Request` class
- Added `archive_to_fdb` function to the `mch_model_data` module
- Added `URLDataSource` to `data_source` module
- The CLI includes a subcommand for the regrid operator
- `data_source.DataSource.retrieve` accepts an argument of type `mars.Request`
- Added `FDBDataSource`, `FileDataSource`, `PolytopeDataSource` that inherit from `DataSource`
- Added dimension `ref_time` with type `datetime64[ns]`
- `grib_decoder.load` is able to read GRIB containing data in the ICON native grid
- Added `regrid.icon2rotlatlon`, `regrid.icon2geolatlon` and `regrid.iconremap` functions
- Added `geo_coords` optional argument to the `grib_decoder.load` function
- Added `ogd_api.get_from_ogd` function

### Changes

- The constants module is renamed to physical constants and the `pc_` prefix is dropped in favour of aliasing the module to `pc` at the call sites
- The grib definitions context is no longer derived from the request model attribute.
  In practice, all defined models required the cosmo definitions as IFS grib data does not define the model mars key.
  Setting `data_scope` config to `ifs` to disable the cosmo definitions context remains possible.
- `data_source.DataSource` is now an abstract base class
- dimension `time` renamed to `lead_time` and type changed from `int` to `timedelta64[ns]`
- `DataArray` objects representing a field no longer have the `message`
  attribute but now have a `metadata` attribute that is an instance of
  `StandAloneGribMetadata` from earthkit-data.
- `FDBDataSource`, `mch_model_data.get_from_fdb` and `mch_model_data.archive_to_fdb` require the `fdb` extra dependency
- `PolytopeDataSource` and `mch_mode_data.get_from_polytope` requires the `polytope` extra dependency
- The `regrid` module now requires the `regrid` extra dependencies


## [0.2.0-rc3] (2023-12-18)

- Added vertical interpolation operator `interpolate_k2any`
- Testing data marker determines the test data that should be used
- Removed the `system_definitions` module


## [0.2.0-rc2] (2023-12-11)

- Added `product.run_products` function
- Updated field mappings
- Data cache will inject the step and number in the request depending on the file pattern
- `mars.Request` now supports multiple params


## [0.2.0-rc1] (2023-12-01)

- Added support for the FDB data source
- Added support for running tests on balfrin (FDB only)
- Added modules
    - `config`: manage configuration
    - `data_cache`: support fieldextra testing from FDB
    - `data_source`: enable reading from files or from FDB
    - `mars`: mars request validation
    - `product`: product description
    - `tasking`: dask delayed wrapper
- Added operators
    - atmo
    - gis
    - lateral_operators
    - regrid
    - relhum
    - time_operators
    - wind
- Changed: flexpart operator no longer uses cosmo naming conventions
- **Breaking:** removed the `load_fields` method from the GribReader class
- **Breaking:** the `load` method of GribReader class now takes a mapping of labels to requests and returns a mapping of labels to `xarray.DataArray`


## [0.1.0] (2023-07-11)

- Added operators
    * brn
    * curl
    * destagger
    * diff
    * flexpart (for IFS model output)
    * hzerocl
    * omega_slope
    * pot_vortic
    * rho
    * theta
    * thetav
    * time_rate
    * interpolate_k2p
    * interpolate_k2theta
    * minmax_k
    * integrate_k
- Added ninjo_k2th product
- Added GRIB data loader based on earthkit-data

[0.2.0]: https://github.com/MeteoSwiss/meteodata-lab/compare/v0.2.0-rc3..v0.2.0
[0.2.0-rc3]: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.2.0-rc2..v0.2.0-rc3
[0.2.0-rc2]: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.2.0-rc1..v0.2.0-rc2
[0.2.0-rc1]: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/compare/v0.1.0..v0.2.0-rc1
[0.1.0]: https://github.com/MeteoSwiss-APN/icon_data_processing_incubator/tree/v0.1.0
