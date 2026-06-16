import pandas as pd
import time
import random

from firebase_config import root

# =====================================
# LOAD DATASET
# =====================================

df = pd.read_excel("Dataset_Signal_Brut.xlsx")

channels = [
    "x_direction_housing_A",
    "y_direction_housing_A",
    "x_direction_housing_B",
    "y_direction_housing_B"
]

print("Predictive Maintenance Simulator Started...")

# =====================================
# LOOP
# =====================================

while True:

    # 80% : كل النقاط Normal
    # 20% : Fault واحد فقط

    if random.random() < 0.80:
        fault_channel = None
    else:
        fault_channel = random.choice(channels)

    print(f"\nCurrent Fault Point: {fault_channel}")

    for channel in channels:

        # ==========================
        # NORMAL POINT
        # ==========================

        if channel != fault_channel:

            point_data = df[
                (df["Channel"] == channel)
                &
                (df["Defaut"] == "Normal")
            ]

            if point_data.empty:
                point_data = df[
                    (df["Channel"] == channel)
                ]

            row = point_data.sample(n=1).iloc[0]

            payload = {

                "Channel": str(row["Channel"]),

                "RMS": float(row["RMS"]),

                "Kurtosis": float(row["Kurtosis"]),

                "Skewness": float(row["Skewness"]),

                "CrestFactor": float(row["CrestFactor"]),

                "PeakAmp": float(row["PeakAmp"]),

                "PeakFreq_Hz": float(row["PeakFreq_Hz"]),

                "SpectralCentroid_Hz": float(row["SpectralCentroid_Hz"]),

                "SpectralBandwidth_Hz": float(row["SpectralBandwidth_Hz"]),

                "Fault": "Normal",

                "Severity": "Low",

                "Condition": "Healthy",

                "HealthScore": random.randint(90, 100)
            }

        # ==========================
        # FAULT POINT
        # ==========================

        else:

            point_data = df[
                (df["Channel"] == channel)
                &
                (df["Defaut"] != "Normal")
            ]

            if point_data.empty:
                point_data = df[
                    (df["Channel"] == channel)
                ]

            row = point_data.sample(n=1).iloc[0]

            severity = random.choice(
                [
                    "Medium",
                    "High",
                    "Critical"
                ]
            )

            if severity == "Medium":
                health_score = random.randint(70, 89)

            elif severity == "High":
                health_score = random.randint(40, 69)

            else:
                health_score = random.randint(10, 39)

            payload = {

                "Channel": str(row["Channel"]),

                "RMS": float(row["RMS"]),

                "Kurtosis": float(row["Kurtosis"]),

                "Skewness": float(row["Skewness"]),

                "CrestFactor": float(row["CrestFactor"]),

                "PeakAmp": float(row["PeakAmp"]),

                "PeakFreq_Hz": float(row["PeakFreq_Hz"]),

                "SpectralCentroid_Hz": float(row["SpectralCentroid_Hz"]),

                "SpectralBandwidth_Hz": float(row["SpectralBandwidth_Hz"]),

                "Fault": str(row["Defaut"]),

                "Severity": severity,

                "Condition": str(row["Condition"]),

                "HealthScore": health_score
            }

        root.child("current_data").child(channel).set(payload)

        print(
            f"{channel} -> "
            f"{payload['Fault']} | "
            f"Health={payload['HealthScore']}%"
        )

    print("--------------------------------")

    # تحديث كل 10 ثواني
    time.sleep(10)