"""Pipeline preprocessing — implementasi produksi dari Step 1–11 notebook
`Preprocessing_Modeling_EndToEnd_.ipynb`.

Pipeline ini menghasilkan artifact preprocessing yang kompatibel dengan file
`preprocessing_artifacts_V1.pkl` dari notebook: KNNImputer untuk EDUCATION dan
MARRIAGE, batas outlier IQR dari TRAIN, OHE MARRIAGE, label encoding SEX,
feature engineering, feature selection, dan StandardScaler.
"""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import KNNImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

CONTINUOUS = ["LIMIT_BAL", "AGE"] + [f"BILL_AMT{i}" for i in range(1, 7)] + [f"PAY_AMT{i}" for i in range(1, 7)]
TARGET_CANDIDATES = ["default payment next month", "default.payment.next.month", "Y", "DEFAULT"]


def _find_outlier_boundary(df: pd.DataFrame, col: str, k: float = 1.5) -> tuple[float, float]:
    """Return (lower, upper) memakai aturan IQR, selaras notebook."""
    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return float(lower), float(upper)


def _standardize_dataset(dataset_raw: pd.DataFrame) -> pd.DataFrame:
    """Standarisasi nama kolom dataset UCI/defaultCreditCardClients.xls."""
    dataset = dataset_raw.copy()
    if "ID" in dataset.columns:
        dataset = dataset.drop(columns=["ID"])
    for cand in TARGET_CANDIDATES:
        if cand in dataset.columns:
            dataset = dataset.rename(columns={cand: "DEFAULT"})
            break
    if "PAY_0" in dataset.columns:
        dataset = dataset.rename(columns={"PAY_0": "PAY_1"})
    if "DEFAULT" not in dataset.columns:
        raise ValueError("Kolom target DEFAULT/default payment next month tidak ditemukan.")
    return dataset


def create_features(df_in: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering Step 7 notebook."""
    df = df_in.copy()
    bill_cols = [f"BILL_AMT{i}" for i in range(1, 7)]
    payamt_cols = [f"PAY_AMT{i}" for i in range(1, 7)]
    delay_cols = [f"PAY_{i}" for i in range(1, 7)]

    df["AVG_UTIL_RATIO"] = df[bill_cols].div(df["LIMIT_BAL"] + 1, axis=0).mean(axis=1)
    df["AVG_PAY_AMT"] = df[payamt_cols].mean(axis=1)
    df["N_LATE_PAYMENTS"] = (df[delay_cols] > 0).sum(axis=1)
    df["MAX_DELAY"] = df[delay_cols].max(axis=1)
    df["BILL_TREND"] = df["BILL_AMT1"] - df["BILL_AMT6"]
    df["PAY_AMT_STD"] = df[payamt_cols].std(axis=1).fillna(0)
    return df


def run_preprocessing(dataset_raw: pd.DataFrame, test_size: float = 0.30, random_state: int = 42):
    """Jalankan Step 1–11 notebook.

    Return: (X_train_processed, X_test_processed, y_train, y_test, artifacts)
    dengan struktur artifacts kompatibel dengan `preprocessing_artifacts_V1.pkl`.
    """
    # Step 1: drop ID, rename target, PAY_0 -> PAY_1.
    dataset = _standardize_dataset(dataset_raw)

    # Step 2: drop duplicate.
    dataset = dataset.drop_duplicates().reset_index(drop=True)

    # Step 3: inkonsistensi EDUCATION/MARRIAGE -> NaN.
    dataset["EDUCATION"] = dataset["EDUCATION"].apply(lambda x: np.nan if x in [0, 5, 6] else x)
    dataset["MARRIAGE"] = dataset["MARRIAGE"].apply(lambda x: np.nan if x == 0 else x)

    # Step 4: train-test split stratified.
    X = dataset.drop(columns=["DEFAULT"])
    y = dataset["DEFAULT"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Step 5: KNN imputation bebas leakage, fit pada TRAIN saja.
    cols_with_na = ["EDUCATION", "MARRIAGE"]
    valid_ranges = {"EDUCATION": (1, 4), "MARRIAGE": (1, 3)}
    knn_feature_columns = X_train.columns.tolist()

    scaler_knn = StandardScaler()
    X_train_scaled = scaler_knn.fit_transform(X_train[knn_feature_columns])
    X_test_scaled = scaler_knn.transform(X_test[knn_feature_columns])

    knn_imputer = KNNImputer(n_neighbors=5, weights="distance")
    X_train_imp = knn_imputer.fit_transform(X_train_scaled)
    X_test_imp = knn_imputer.transform(X_test_scaled)

    X_train_inv = pd.DataFrame(
        scaler_knn.inverse_transform(X_train_imp), columns=knn_feature_columns, index=X_train.index
    )
    X_test_inv = pd.DataFrame(
        scaler_knn.inverse_transform(X_test_imp), columns=knn_feature_columns, index=X_test.index
    )

    for col in cols_with_na:
        lo, hi = valid_ranges[col]
        X_train.loc[:, col] = X_train_inv[col].round().clip(lo, hi).astype(int)
        X_test.loc[:, col] = X_test_inv[col].round().clip(lo, hi).astype(int)

    fallback_education = int(X_train["EDUCATION"].mode().iloc[0])
    fallback_marriage = int(X_train["MARRIAGE"].mode().iloc[0])

    # Step 6: IQR outlier capping (batas dari TRAIN saja).
    Xtr = X_train.copy()
    Xte = X_test.copy()
    outlier_boundaries = {}
    for col in CONTINUOUS:
        lower, upper = _find_outlier_boundary(Xtr, col)
        outlier_boundaries[col] = (lower, upper)
        Xtr[col] = np.clip(Xtr[col], lower, upper)
        Xte[col] = np.clip(Xte[col], lower, upper)

    # Step 7: feature extraction.
    Xtr = create_features(Xtr)
    Xte = create_features(Xte)

    # Step 8: one-hot encode MARRIAGE dan label encode SEX.
    Xtr = pd.get_dummies(Xtr, columns=["MARRIAGE"])
    Xte = pd.get_dummies(Xte, columns=["MARRIAGE"])
    for col in Xtr.columns:
        if col not in Xte.columns:
            Xte[col] = 0
    Xte = Xte[Xtr.columns]

    marriage_ohe = [c for c in Xtr.columns if c.startswith("MARRIAGE_")]
    Xtr[marriage_ohe] = Xtr[marriage_ohe].astype(int)
    Xte[marriage_ohe] = Xte[marriage_ohe].astype(int)

    label_encoder = LabelEncoder()
    Xtr["SEX"] = label_encoder.fit_transform(Xtr["SEX"])
    Xte["SEX"] = label_encoder.transform(Xte["SEX"])
    sex_mapping = {int(c): int(label_encoder.transform([c])[0]) for c in label_encoder.classes_}

    # Step 9/10: feature selection, sesuai notebook: korelasi > 0.85 lalu ANOVA p > 0.05.
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
    anova = pd.DataFrame({"Feature": Xtr.columns, "F": fs.scores_, "p": fs.pvalues_})
    insignif = anova[anova["p"] > 0.05]["Feature"].tolist()
    if insignif:
        Xtr = Xtr.drop(columns=insignif)
        Xte = Xte.drop(columns=insignif)

    # Step 11: scaling. Notebook memasukkan AGE_GROUP di daftar exclude walau kolom tidak dibuat.
    binary_and_ordinal = ["SEX", "EDUCATION", "AGE_GROUP"] + [
        c for c in Xtr.columns if c.startswith("MARRIAGE_")
    ]
    columns_to_stdscaler = [c for c in Xtr.columns if c not in binary_and_ordinal]
    scaler = StandardScaler()
    Xtr[columns_to_stdscaler] = scaler.fit_transform(Xtr[columns_to_stdscaler])
    Xte[columns_to_stdscaler] = scaler.transform(Xte[columns_to_stdscaler])

    final_columns = Xtr.columns.tolist()
    artifacts = {
        "fallback_education": int(fallback_education),
        "fallback_marriage": int(fallback_marriage),
        "outlier_boundaries": outlier_boundaries,
        "sex_mapping": sex_mapping,
        "marriage_ohe_columns": marriage_ohe,
        "scaler": scaler,
        "columns_to_stdscaler": columns_to_stdscaler,
        "final_columns": final_columns,
        "scaler_knn": scaler_knn,
        "knn_imputer": knn_imputer,
        "knn_feature_columns": knn_feature_columns,
        "knn_valid_ranges": valid_ranges,
        "imbalance_method": "None",
    }
    return Xtr, Xte, y_train, y_test, artifacts
