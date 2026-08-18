import numpy as np
import xarray as xr
import os


def pre_process(
    files, possible_variables, min_lon, max_lon, min_lat, max_lat, calendar="360_day"
):
    # Ensure the input is a list or array and not empty
    if not files or not isinstance(files, (np.ndarray, list)):
        print("The input 'files' should be a non-empty list or array of file paths.")
        return None

    # If files is a numpy array, convert it to a list for easier processing
    if isinstance(files, np.ndarray):
        files = files.tolist()

    processed_data = []  # List to store processed data

    for file_path in files:
        # Ensure file_path is a string and check if it's a valid file
        if isinstance(file_path, str) and os.path.isfile(file_path):
            print(f"Processing file: {file_path}")

            # Open the NetCDF file
            try:
                ds = xr.open_dataset(file_path)
                # Round lons and lats to next 0.1
                ds = ds.assign_coords(
                    {"lon": np.round(ds.lon, 1), "lat": np.round(ds.lat, 1)}
                )
            except Exception as e:
                print(f"Failed to open {file_path}: {e}")
                continue  # Skip the file if opening it fails
            for variable in possible_variables:
                if variable in ds:
                    temp_data = ds[variable]

                    temp_data = temp_data.convert_calendar(calendar, align_on="year")

                    # Append the processed data to the list
                    processed_data.append(temp_data)
                    break
                else:
                    print(
                        f"Variable '{variable}' not found in {file_path}. Skipping this file."
                    )
            else:
                print(f"Skipping invalid file path: {file_path}")

    # Return the list containing all the processed datasets
    return processed_data


def select_time_frame(files, time=slice("2046-01-01", "2054-12-31")):
    new_files = [None] * len(files)
    for i in range(len(files)):
        current = files[i]
        # learn same bias correction as for historical data
        time_slice = current.sel(time=time)
        new_files[i] = time_slice
    # reference is without data that is used for qm adjustment
    return new_files


def marginal_average_seasonal_hourly(
    files, files_future, model_names, model_names_future
):
    """
    Computes seasonal mean per hour of the day for each model (no spatial averaging),
    and calculates DMPE relative to future datasets.

    Returns a list of dictionaries with seasonal DMPE maps (hour x lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    DMPE_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe = {}
        index = model_names_future.index(model_names[i])
        reference = files_future[index]

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)
            ref_season = reference.sel(time=reference["time.season"] == season)

            if temp_season.size == 0 or ref_season.size == 0:
                continue  # skip empty seasons

            # Group by hour and average over time for each hour
            temp_hourly = temp_season.mean(dim="time")
            ref_hourly = ref_season.mean(dim="time")

            # DMPE per hour and grid cell
            with np.errstate(divide="ignore", invalid="ignore"):
                dmpe_hourly = (ref_hourly - temp_hourly) / temp_hourly * 100

            mpe_mean = dmpe_hourly
            seasonal_dmpe[season] = mpe_mean  # dims: lat x lon

        DMPE_diff.append(seasonal_dmpe)

    return DMPE_diff


def marginal_var_seasonal(files, files_future, model_names, model_names_future):
    """
    Computes seasonal standard deviation for each model (no spatial averaging),
    calculates DMPE relative to future datasets.

    Returns a list of dictionaries with seasonal DMPE maps of variability (lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    DMPE_var_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe_var = {}
        index = model_names_future.index(model_names[i])
        reference = files_future[index]

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)
            ref_season = reference.sel(time=reference["time.season"] == season)

            if temp_season.size == 0 or ref_season.size == 0:
                continue  # skip empty seasons

            # Compute standard deviation over time (keep lat/lon)
            temp_std = temp_season.std(dim="time")
            ref_std = ref_season.std(dim="time")

            # DMPE per grid cell
            with np.errstate(divide="ignore", invalid="ignore"):
                dmpe_var = (ref_std - temp_std) / temp_std * 100

            seasonal_dmpe_var[season] = dmpe_var  # dims: lat x lon

        DMPE_var_diff.append(seasonal_dmpe_var)

    return DMPE_var_diff


def spatiotemporal_below_percentile_seasonal(
    files, files_future, model_names, model_names_future, percentile=90
):
    """
    Computes the directional mean percentage error (DMPE) of the percentile threshold value
    between present and future datasets for each season, keeping spatial dimensions (lat x lon).

    The percentile is computed separately for present and future for each season.

    Returns a list of dictionaries with seasonal DMPE maps (lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    threshold_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe = {}
        index = model_names_future.index(model_names[i])
        reference = files_future[index]

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)
            ref_season = reference.sel(time=reference["time.season"] == season)

            if temp_season.size == 0 or ref_season.size == 0:
                continue  # skip empty seasons

            # Compute percentile thresholds for present and future
            temp_threshold = temp_season.quantile(
                percentile / 100, dim="time", skipna=True
            )
            ref_threshold = ref_season.quantile(
                percentile / 100, dim="time", skipna=True
            )

            # Compute DMPE of threshold value per grid cell
            with np.errstate(divide="ignore", invalid="ignore"):
                dmpe_threshold = (ref_threshold - temp_threshold) / temp_threshold * 100

            # Keep dimensions consistent
            dmpe_threshold = dmpe_threshold.squeeze()

            seasonal_dmpe[season] = dmpe_threshold

        threshold_diff.append(seasonal_dmpe)

    return threshold_diff


import xarray as xr
import numpy as np
from scipy.stats import pearsonr


def correlation_over_space_diff(
    files_wind,
    files_solar,
    files_future_wind,
    files_future_solar,
    model_names_wind,
    model_names_solar,
    model_names_wind_future,
    model_names_solar_future,
    method,
):
    """
    Computes seasonal spatial correlations (current and future) and
    returns their relative difference in percent.
    Output: list of dicts {season: correlation_change_field}.
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    corr_diff_list = []

    for i, solar_data in enumerate(files_solar):
        seasonal_diff = {}
        name = model_names_solar[i]

        # match models across datasets
        wind_current = files_wind[model_names_wind.index(name)]
        solar_current = files_solar[model_names_solar.index(name)]
        wind_future = files_future_wind[model_names_wind_future.index(name)]
        solar_future = files_future_solar[model_names_solar_future.index(name)]
        # 1. Average to daily values
        wind_daily = wind_current.resample(time="1D").mean()
        solar_daily = solar_current.resample(time="1D").mean()
        wind_daily_future = wind_future.resample(time="1D").mean()
        solar_daily_future = solar_future.resample(time="1D").mean()
        # 2. Compute seasonal anomalies
        wind_anom = wind_daily.groupby("time.season") - wind_daily.groupby(
            "time.season"
        ).mean("time")
        solar_anom = solar_daily.groupby("time.season") - solar_daily.groupby(
            "time.season"
        ).mean("time")
        wind_anom_future = wind_daily_future.groupby(
            "time.season"
        ) - wind_daily_future.groupby("time.season").mean("time")
        solar_anom_future = solar_daily_future.groupby(
            "time.season"
        ) - solar_daily_future.groupby("time.season").mean("time")
        # seasonal loop
        for season in seasons:
            w_cur = wind_anom.sel(time=wind_anom["time.season"] == season)
            s_cur = solar_anom.sel(time=solar_anom["time.season"] == season)
            w_fut = wind_anom_future.sel(time=wind_anom_future["time.season"] == season)
            s_fut = solar_anom_future.sel(
                time=solar_anom_future["time.season"] == season
            )

            # 4. Compute correlation at each grid point
            def corr_func(x, y):
                if np.all(np.isnan(x)) or np.all(np.isnan(y)):
                    return np.nan
                return np.corrcoef(x, y)[0, 1]

            cur_corr = xr.apply_ufunc(
                corr_func,
                w_cur,
                s_cur,
                input_core_dims=[["time"], ["time"]],
                vectorize=True,
            )
            fut_corr = xr.apply_ufunc(
                corr_func,
                w_fut,
                s_fut,
                input_core_dims=[["time"], ["time"]],
                vectorize=True,
            )
            print(fut_corr)
            # Fisher z-transform
            cur_corr_z = np.arctanh(cur_corr)
            fut_corr_z = np.arctanh(fut_corr)
            print(fut_corr)
            # percent change relative to current
            diff = ((fut_corr_z - cur_corr_z) / cur_corr_z) * 100
            seasonal_diff[season] = diff

        corr_diff_list.append(seasonal_diff)

    return corr_diff_list


def marginal_average_seasonal_hourly(files):
    """
    Computes seasonal mean per hour of the day for each model (no spatial averaging),
    and calculates DMPE relative to future datasets.

    Returns a list of dictionaries with seasonal DMPE maps (hour x lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    DMPE_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe = {}

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)
            # Group by hour and average over time for each hour
            temp_hourly = temp_season.groupby("time.hour").mean(dim="time")

            mpe_mean = temp_hourly.mean(dim="hour")
            seasonal_dmpe[season] = mpe_mean  # dims: lat x lon

        DMPE_diff.append(seasonal_dmpe)

    return DMPE_diff


def marginal_var_seasonal(files):
    """
    Computes seasonal standard deviation for each model (no spatial averaging),
    calculates DMPE relative to future datasets.

    Returns a list of dictionaries with seasonal DMPE maps of variability (lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    DMPE_var_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe_var = {}

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)

            # Compute standard deviation over time (keep lat/lon)
            temp_std = temp_season.std(dim="time")

            seasonal_dmpe_var[season] = temp_std  # dims: lat x lon

        DMPE_var_diff.append(seasonal_dmpe_var)

    return DMPE_var_diff


def spatiotemporal_below_percentile_seasonal(files, percentile=90):
    """
    Computes directional mean percentage error of the number of time steps below a percentile
    for each season separately, keeping spatial dimensions (lat x lon).

    The percentile is computed from the reference (future) dataset for each season.

    Returns a list of dictionaries with seasonal DMPE maps (lat x lon) for each model.
    """
    import numpy as np

    seasons = ["DJF", "MAM", "JJA", "SON"]
    count_diff = []

    for i, temp_data in enumerate(files):
        seasonal_dmpe = {}

        for season in seasons:
            # Select seasonal data
            temp_season = temp_data.sel(time=temp_data["time.season"] == season)

            # Compute the percentile threshold from the reference dataset per grid cell
            ref_threshold = temp_season.quantile(percentile / 100, dim="time")
            # Count points below the percentile threshold per grid cell
            # temp_count = (temp_season < ref_threshold).sum(dim="time")
            seasonal_dmpe[season] = ref_threshold  # dims: lat x lon

        count_diff.append(seasonal_dmpe)

    return count_diff


def correlation_over_space(
    files_wind, files_solar, model_names_wind, model_names_solar
):
    """
    Computes seasonal grid-pointwise correlations between wind and solar for multiple models.
    Steps:
        1. Average sub-daily data to daily values.
        2. Compute seasonal anomalies (subtract seasonal mean at each grid point).
        3. Compute correlation along time at each grid point for each season.
        4. Apply Fisher z-transform for variance stabilization.

    Returns
    -------
    seasonal_corr_list : list of dicts
        Each dict corresponds to a model, keys are seasons ("DJF","MAM","JJA","SON"),
        values are (lat x lon) DataArray of Fisher z-transformed correlations.
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    seasonal_corr_list = []

    for i, solar_data in enumerate(files_solar):
        print(i)
        seasonal_corr = {}
        index = model_names_wind.index(model_names_solar[i])
        wind_data = files_wind[index]

        # 1. Average to daily values
        wind_daily = wind_data.resample(time="1D").mean()
        solar_daily = solar_data.resample(time="1D").mean()

        # 2. Compute seasonal anomalies
        wind_anom = wind_daily.groupby("time.season") - wind_daily.groupby(
            "time.season"
        ).mean("time")
        solar_anom = solar_daily.groupby("time.season") - solar_daily.groupby(
            "time.season"
        ).mean("time")

        for season in seasons:
            # 3. Select seasonal anomalies
            wind_season = wind_anom.sel(time=wind_anom["time.season"] == season)
            solar_season = solar_anom.sel(time=solar_anom["time.season"] == season)

            # Skip if not enough time points
            if wind_season.time.size < 2:
                seasonal_corr[season] = xr.full_like(wind_daily.isel(time=0), np.nan)
                continue

            # 4. Compute correlation at each grid point
            def corr_func(x, y):
                if np.all(np.isnan(x)) or np.all(np.isnan(y)):
                    return np.nan
                return np.corrcoef(x, y)[0, 1]

            corr_map = xr.apply_ufunc(
                corr_func,
                wind_season,
                solar_season,
                input_core_dims=[["time"], ["time"]],
                vectorize=True,
            )

            # 5. Fisher z-transform
            seasonal_corr[season] = np.arctanh(corr_map)

        seasonal_corr_list.append(seasonal_corr)

    return seasonal_corr_list


def co_occurrence_low_wind_solar_seasonal_spatial(wind, solar):
    """
    Computes the number of days per season where both wind and solar
    are below their 20th percentile thresholds at each grid point.
    Returns a dictionary keyed by season with DataArrays (lat x lon).
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    joint_low_days_seasonal = {}

    for season in seasons:
        # Select season
        wind_season = wind.sel(time=wind["time.season"] == season)
        solar_season = solar.sel(time=solar["time.season"] == season)

        # Resample to daily averages
        wind_daily = wind_season.resample(time="1D").mean(dim="time")
        solar_daily = solar_season.resample(time="1D").mean(dim="time")

        # Compute 20th percentile thresholds per grid point
        wind_thresh = np.nanpercentile(wind_daily, 20, axis=0)
        solar_thresh = np.nanpercentile(solar_daily, 20, axis=0)

        # Broadcast thresholds to time dimension for comparison
        low_wind = wind_daily < wind_thresh
        low_solar = solar_daily < solar_thresh

        # Count joint low days per grid point
        joint_low_days = (low_wind & low_solar).sum(dim="time")

        joint_low_days_seasonal[season] = joint_low_days

    return joint_low_days_seasonal


def dunkelflauten_index(files_wind, files_solar, model_names_wind, model_names_solar):
    """
    Computes seasonal co-occurrence of low wind and solar for each model at each grid point.
    Returns a list of dictionaries keyed by season, each containing a DataArray (lat x lon).
    """
    results = []
    for i, solar_current in enumerate(files_solar):
        index = model_names_wind.index(model_names_solar[i])
        wind_current = files_wind[index]
        seasonal_counts = co_occurrence_low_wind_solar_seasonal_spatial(
            wind_current, solar_current
        )
        results.append(seasonal_counts)
    return results


def compute_mape_zeroes(data1, data2):
    data1 = data1.mean(dim="time").values.ravel()
    data2 = data2.mean(dim="time").values.ravel()
    mask = data1 != 0
    absolute_percentage_error = np.abs((data1[mask] - data2[mask]) / data1[mask]) * 100
    mape = absolute_percentage_error.mean()
    return mape


def mape_average(files, reference_number):
    mape = []
    for i, temp_data in enumerate(files):
        if i == reference_number:
            continue  # Skip comparison with itself
        counter = compute_mape_zeroes(files[reference_number], temp_data)
        mape.append(counter)
    return mape


def compute_corr(data1, data2):
    # Flatten data
    data1 = data1.values.ravel()
    data2 = data2.values.ravel()

    # Remove NaNs
    mask = ~np.isnan(data1) & ~np.isnan(data2)
    data1 = data1[mask]
    data2 = data2[mask]

    if len(data1) == 0:
        return np.nan  # No data to compare

    corr, _ = pearsonr(data1, data2)
    return corr


def correlation(files, reference_number):
    mape = []
    # Compute Wasserstein distances
    for i, temp_data in enumerate(files):
        if i == reference_number:
            continue  # Skip comparison with itself
        counter = compute_corr(files[reference_number], temp_data)
        mape.append(counter)
    return mape
