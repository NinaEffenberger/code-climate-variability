import numpy as np
import pandas as pd
import xarray as xr
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm


def compute_anova_variance(dataset, gcm_labels, rcm_labels):
    n_models, n_seasons, n_lat, n_lon = dataset.shape
    var_gcm = np.full((n_seasons, n_lat, n_lon), np.nan)
    var_rcm = np.full((n_seasons, n_lat, n_lon), np.nan)
    var_inter = np.zeros((n_seasons, n_lat, n_lon))  # interaction ignored
    var_resid = np.full((n_seasons, n_lat, n_lon), np.nan)

    for s in range(n_seasons):
        for i in range(n_lat):
            for j in range(n_lon):
                df = pd.DataFrame(
                    {
                        "Change": dataset[:, s, i, j],
                        "GCM": gcm_labels,
                        "RCM": rcm_labels,
                    }
                ).dropna()

                # skip if too few unique labels
                if df["GCM"].nunique() < 2 or df["RCM"].nunique() < 2:
                    continue

                # skip if constant data
                if df["Change"].std() == 0:
                    var_gcm[s, i, j] = 0
                    var_rcm[s, i, j] = 0
                    var_resid[s, i, j] = 1
                    continue

                try:
                    m = ols("Change ~ C(GCM) + C(RCM)", data=df).fit()
                    a = anova_lm(m, typ=2)
                    ss_g = a.loc["C(GCM)", "sum_sq"]
                    ss_r = a.loc["C(RCM)", "sum_sq"]
                    ss_e = a.loc["Residual", "sum_sq"]
                    tot = ss_g + ss_r + ss_e
                    if tot > 0:
                        var_gcm[s, i, j] = ss_g / tot
                        var_rcm[s, i, j] = ss_r / tot
                        var_resid[s, i, j] = ss_e / tot
                except Exception:
                    continue

    return var_gcm, var_rcm, var_inter, var_resid


def co_occurrence_low_wind_solar_seasonal_spatial(wind, solar):
    """
    Computes the number of days per season where both wind and solar
    are below their 20th percentile thresholds at each grid point.
    Returns a dictionary keyed by season with DataArrays (lat x lon).
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    joint_low_days_seasonal = {}

    for season in seasons:
        wind_season = wind.sel(time=wind["time.season"] == season)
        solar_season = solar.sel(time=solar["time.season"] == season)

        wind_daily = wind_season.resample(time="1D").mean(dim="time")
        solar_daily = solar_season.resample(time="1D").mean(dim="time")

        wind_thresh = np.nanpercentile(wind_daily, 20, axis=0)
        solar_thresh = np.nanpercentile(solar_daily, 20, axis=0)

        low_wind = wind_daily < wind_thresh
        low_solar = solar_daily < solar_thresh

        joint_low_days = (low_wind & low_solar).sum(dim="time")
        joint_low_days_seasonal[season] = joint_low_days

    return joint_low_days_seasonal


def dunkelflauten_index_diff(
    files_wind,
    files_solar,
    files_future_wind,
    files_future_solar,
    model_names_wind,
    model_names_solar,
    model_names_wind_future,
    model_names_solar_future,
):
    """
    Computes seasonal co-occurrence of low wind and solar for current and future
    climate, and returns their relative difference in percent.
    Output: list of dicts {season: DataArray(lat x lon)} per model.
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    results_diff = []

    for i, solar_current in enumerate(files_solar):
        name = model_names_solar[i]

        wind_current = files_wind[model_names_wind.index(name)]
        solar_future = files_future_solar[model_names_solar_future.index(name)]
        wind_future = files_future_wind[model_names_wind_future.index(name)]

        # compute co-occurrence maps
        cur_counts = co_occurrence_low_wind_solar_seasonal_spatial(
            wind_current, solar_current
        )
        fut_counts = co_occurrence_low_wind_solar_seasonal_spatial(
            wind_future, solar_future
        )

        # compute percent difference per season
        diff_seasonal = {}
        for season in seasons:
            cur = cur_counts[season]
            fut = fut_counts[season]
            diff = xr.where(cur != 0, ((fut - cur) / cur) * 100, np.nan)
            diff_seasonal[season] = diff

        results_diff.append(diff_seasonal)

    return results_diff
