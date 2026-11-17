import numpy as np
import pandas as pd

from medimesh_ml.data_cleaning import clean_hospital_data, data_quality_report
from medimesh_ml.features import LOAD_FEATURES, TIME_FEATURES, build_feature_frame, time_features_from
from medimesh_ml.scenarios import generate_hospital_data


def test_time_features_saturday_afternoon():
    f = time_features_from(pd.Series(pd.to_datetime(["2026-01-10 14:00"])))
    assert f.loc[0, "hour"] == 14
    assert f.loc[0, "day_of_week"] == 5
    assert f.loc[0, "is_weekend"] == 1
    assert f.loc[0, "part_of_day"] == 2


def test_build_feature_frame_has_all_columns_and_no_nans():
    feats = build_feature_frame(generate_hospital_data(days=5))
    for col in TIME_FEATURES + LOAD_FEATURES:
        assert col in feats.columns
        assert not feats[col].isna().any()


def test_lag_and_rolling_features_use_only_the_past():
    df = generate_hospital_data(days=5)
    feats = build_feature_frame(df)
    assert feats["volume_lag1"].iloc[10] == df["patient_volume"].iloc[9]
    assert feats["volume_lag24"].iloc[30] == df["patient_volume"].iloc[6]
    assert np.isclose(feats["volume_roll3"].iloc[10], df["patient_volume"].iloc[8:11].mean())


def test_cleaning_fixes_duplicates_negatives_and_overflow():
    df = generate_hospital_data(days=3)
    df = pd.concat([df, df.iloc[[5]]])
    df.loc[df.index[10], "ed_wait_minutes"] = -5
    df.loc[df.index[11], "bed_occupancy_pct"] = 140
    df.loc[df.index[12], "patient_volume"] = np.nan
    clean = clean_hospital_data(df)

    assert clean["timestamp"].is_unique and clean["timestamp"].is_monotonic_increasing
    assert (clean["ed_wait_minutes"] >= 0).all()
    assert clean["bed_occupancy_pct"].max() <= 100
    assert not clean[["patient_volume", "staff_on_duty"]].isna().any().any()


def test_quality_report_counts_problems():
    df = generate_hospital_data(days=2)
    df = pd.concat([df, df.iloc[[0]]])
    report = data_quality_report(df)
    assert report["duplicate_timestamps"] == 1
    assert report["rows"] == len(df)