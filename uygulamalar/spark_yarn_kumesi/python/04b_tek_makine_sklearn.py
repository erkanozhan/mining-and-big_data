"""Uygulama 4b — Aynı hiperparametre aramasını TEK makinede scikit-learn ile yapmak.

Kullanım:  python python/04b_tek_makine_sklearn.py covtype.data
           (covtype.data'yı HDFS'ten almak için: hdfs dfs -get /veri/covtype/covtype.data)

Uygulama 4'teki ızgara (ağaç sayısı 20/40 × derinlik 10/15, 3 katlı çapraz
doğrulama) burada tek bilgisayarın tüm çekirdekleriyle çalıştırılır. Amaç,
"veri ne zaman Spark'ı gerektirecek kadar büyüktür?" sorusuna ölçerek cevap vermektir.
"""

import os
import sys
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from ortak import sonuc_kaydet  # noqa: E402

veri = np.loadtxt(sys.argv[1] if len(sys.argv) > 1 else "covtype.data", delimiter=",", dtype=np.int32)
X, y = veri[:, :-1], veri[:, -1] - 1
X_egitim, X_test, y_egitim, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Eğitim: {len(y_egitim):,} satır   Test: {len(y_test):,} satır   Çekirdek: {os.cpu_count()}")

arama = GridSearchCV(
    RandomForestClassifier(random_state=42),
    {"n_estimators": [20, 40], "max_depth": [10, 15]},
    cv=3, scoring="accuracy", n_jobs=-1,            # -1: makinenin bütün çekirdekleri
)
t0 = time.perf_counter()
arama.fit(X_egitim, y_egitim)
sure = time.perf_counter() - t0
print(f"[süre] Çapraz doğrulamalı arama (tek makine): {sure:.1f} sn")

for p, ort in zip(arama.cv_results_["params"], arama.cv_results_["mean_test_score"]):
    print(f"  ağaç={p['n_estimators']:>3}  derinlik={p['max_depth']:>3}  →  {ort:.4f}")
test_dogruluk = arama.score(X_test, y_test)
print(f"En iyi: {arama.best_params_}   Test doğruluğu: {test_dogruluk:.4f}")

sonuc_kaydet("04b_sklearn_tek_makine", {
    "cekirdek": os.cpu_count(), "sure_sn": round(sure, 1), "test_dogruluk": round(test_dogruluk, 4),
})
