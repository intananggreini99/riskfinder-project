"""Pipeline preprocessing — replikasi Step 1–11 dari Preprocessing_Modeling_EndToEnd.ipynb.

Menghasilkan X_train/X_test/y_train/y_test terproses + dict `artifacts` berisi
seluruh parameter yang "belajar" dari TRAIN (untuk inference identik di ca-service).
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif

CONTINUOUS = ["LIMIT_BAL", "AGE"] + [f"BILL_AMT{i}" for i in range(1, 7)] + [f"PAY_AMT{i}" for i in range(1, 7)]


def _find_outlier_boundary(df, col, k=1.5):
    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr  # (lower, upper)


def create_features(df_in: pd.DataFrame) -> pd.DataFrame:
    """Step 7 — feature extraction (selaras notebook)."""
    df = df_in.copy()
    bill = [f"BILL_AMT{i}" for i in range(1, 7)]
    payamt = [f"PAY_AMT{i}" for i in range(1, 7)]
    delay = [f"PAY_{i}" for i in range(1, 7)]

    df["AVG_UTIL_RATIO"] = df[bill].div(df["LIMIT_BAL"] + 1, axis=0).mean(axis=1)
    df["AVG_PAY_AMT"] = df[payamt].mean(axis=1)
    df["N_LATE_PAYMENTS"] = (df[delay] > 0).sum(axis=1)
    df["MAX_DELAY"] = df[delay].max(axis=1)
    df["BILL_TREND"] = df["BILL_AMT1"] - df["BILL_AMT6"]
    df["PAY_AMT_STD"] = df[payamt].std(axis=1).fillna(0)
    return df


def run_preprocessing(dataset_raw: pd.DataFrame, test_size=0.30, random_state=42):
    """Jalankan Step 1–11. Return: (X_train, X_test, y_train, y_test, artifacts)."""
    # ---- Step 1: drop ID, rename target, PAY_0 -> PAY_1 (internal) ----
    dataset = dataset_raw.copy()
    if "ID" in dataset.columns:
        dataset = dataset.drop(columns=["ID"])
    for cand in ["default payment next month", "default.payment.next.month", "Y", "DEFAULT"]:
        if cand in dataset.columns:
            dataset = dataset.rename(columns={cand: "DEFAULT"})
            break
    if "PAY_0" in dataset.columns:
        dataset = dataset.rename(columns={"PAY_0": "PAY_1"})

    # ---- Step 2: drop duplicates ----
    dataset = dataset.drop_duplicates().reset_index(drop=True)

    # ---- Step 3: tandai inkonsistensi EDUCATION/MARRIAGE sebagai NaN ----
    dataset["EDUCATION"] = dataset["EDUCATION"].apply(lambda x: np.nan if x in [0, 5, 6] else x)
    dataset["MARRIAGE"] = dataset["MARRIAGE"].apply(lambda x: np.nan if x == 0 else x)

    # ---- Step 4: train-test split (stratified) ----
    X = dataset.drop(columns=["DEFAULT"])
    y = dataset["DEFAULT"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # ---- Step 5: imputasi modus per-kelas (TRAIN), fallback mayoritas (TEST) ----
    tc = X_train.copy()
    tc["DEFAULT"] = y_train.values
    mode_edu = tc.groupby("DEFAULT")["EDUCATION"].agg(lambda s: s.mode().iloc[0]).to_dict()
    mode_mar = tc.groupby("DEFAULT")["MARRIAGE"].agg(lambda s: s.mode().iloc[0]).to_dict()
    for cls, val in mode_edu.items():
        X_train.loc[(y_train == cls) & (X_train["EDUCATION"].isna()), "EDUCATION"] = val
    for cls, val in mode_mar.items():
        X_train.loc[(y_train == cls) & (X_train["MARRIAGE"].isna()), "MARRIAGE"] = val
    majority = y_train.value_counts().idxmax()
    fallback_education = int(mode_edu[majority])
    fallback_marriage = int(mode_mar[majority])
    X_test["EDUCATION"] = X_test["EDUCATION"].fillna(fallback_education)
    X_test["MARRIAGE"] = X_test["MARRIAGE"].fillna(fallback_marriage)
    for d in (X_train, X_test):
        d["EDUCATION"] = d["EDUCATION"].astype(int)
        d["MARRIAGE"] = d["MARRIAGE"].astype(int)

    # ---- Step 6: outlier capping (IQR, batas dari TRAIN) ----
    Xtr = X_train.copy()
    Xte = X_test.copy()
    outlier_boundaries = {}
    for col in CONTINUOUS:
        lower, upper = _find_outlier_boundary(Xtr, col)
        outlier_boundaries[col] = (float(lower), float(upper))
        Xtr[col] = np.clip(Xtr[col], lower, upper)
        Xte[col] = np.clip(Xte[col], lower, upper)

    # ---- Step 7: feature extraction ----
    Xtr = create_features(Xtr)
    Xte = create_features(Xte)

    # ---- Step 8: encoding (OHE MARRIAGE, label SEX) ----
    Xtr = pd.get_dummies(Xtr, columns=["MARRIAGE"])
    Xte = pd.get_dummies(Xte, columns=["MARRIAGE"])
    for c in Xtr.columns:
        if c not in Xte.columns:
            Xte[c] = 0
    Xte = Xte[Xtr.columns]
    marriage_ohe = [c for c in Xtr.columns if c.startswith("MARRIAGE_")]
    Xtr[marriage_ohe] = Xtr[marriage_ohe].astype(int)
    Xte[marriage_ohe] = Xte[marriage_ohe].astype(int)

    label_encoder = LabelEncoder()
    Xtr["SEX"] = label_encoder.fit_transform(Xtr["SEX"])
    Xte["SEX"] = label_encoder.transform(Xte["SEX"])
    sex_mapping = {int(c): int(label_encoder.transform([c])[0]) for c in label_encoder.classes_}

    # ---- Step 9: binning AGE -> AGE_GROUP (ordinal) ----
    age_bins = [0, 25, 35, 45, 55, 200]
    age_labels = ["<25", "25-34", "35-44", "45-54", "55+"]
    age_group_mapping = {lab: i for i, lab in enumerate(age_labels)}
    for d in (Xtr, Xte):
        d["AGE_GROUP"] = (
            pd.cut(d["AGE"], bins=age_bins, labels=age_labels, right=False)
            .map(age_group_mapping)
            .astype(int)
        )

    # ---- Step 10: feature selection (korelasi > 0.85, ANOVA p > 0.05) ----
    corr = Xtr.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = set()
    for col in upper.columns:
        for row in upper.index[upper[col] > 0.85]:
            c1 = abs(Xtr[col].corr(y_train))
            c2 = abs(Xtr[row].corr(y_train))
            to_drop.add(col if c1 < c2 else row)
    if to_drop:
        Xtr = Xtr.drop(columns=list(to_drop))
        Xte = Xte.drop(columns=list(to_drop))

    fs = SelectKBest(score_func=f_classif, k="all").fit(Xtr, y_train)
    anova = pd.DataFrame({"f": fs.pvalues_}, index=Xtr.columns)
    insignif = anova[anova["f"] > 0.05].index.tolist()
    if insignif:
        Xtr = Xtr.drop(columns=insignif)
        Xte = Xte.drop(columns=insignif)

    # ---- Step 11: scaling (StandardScaler, kolom kontinu saja) ----
    binary_ordinal = ["SEX", "EDUCATION", "AGE_GROUP"] + [c for c in Xtr.columns if c.startswith("MARRIAGE_")]
    columns_to_stdscaler = [c for c in Xtr.columns if c not in binary_ordinal]
    scaler = StandardScaler()
    Xtr[columns_to_stdscaler] = scaler.fit_transform(Xtr[columns_to_stdscaler])
    Xte[columns_to_stdscaler] = scaler.transform(Xte[columns_to_stdscaler])

    final_columns = Xtr.columns.tolist()

    # ---- Artifact untuk inference (Step 17) ----
    artifacts = {
        "fallback_education": fallback_education,
        "fallback_marriage": fallback_marriage,
        "outlier_boundaries": outlier_boundaries,
        "sex_mapping": sex_mapping,
        "marriage_ohe_columns": marriage_ohe,
        "scaler": scaler,
        "columns_to_stdscaler": columns_to_stdscaler,
        "final_columns": final_columns,
        # diperlukan untuk binning AGE saat inference
        "age_bins": age_bins,
        "age_labels": age_labels,
        "age_group_mapping": age_group_mapping,
    }
    return Xtr, Xte, y_train, y_test, artifacts
