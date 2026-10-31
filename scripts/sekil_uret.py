"""Ders notu için veri tabanlı şekilleri üretir.

"Veri Madenciliğinde İleri Konular ve Büyük Veri" ders notundaki (ders_notu.md)
matplotlib şekillerini SVG olarak `images/` klasörüne yazar: kutu grafiği,
uzaklık ölçüleri, PCA, k-NN, ROC eğrisi, aşırı öğrenme, k-Means iterasyonları,
dendrogram, DBSCAN, aykırı değer türleri ve kavram kayması.

Çalıştırma (repo kökünden):
    python scripts/sekil_uret.py

Tüm rastgelelik sabit tohumla (42) üretildiği için betik her çalıştırıldığında
aynı dosyaları üretir.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Arc, Circle, Patch  # noqa: E402

CIKTI = Path(__file__).resolve().parent.parent / "images"

# Renk paleti (Tailwind tonları)
MAVI = "#3b82f6"
YESIL = "#10b981"
TURUNCU = "#f59e0b"
MOR = "#8b5cf6"
KIRMIZI = "#ef4444"
GRI = "#6b7280"
KOYU = "#1f2937"
ACIK_MAVI = "#dbeafe"
ACIK_YESIL = "#d1fae5"
ACIK_TURUNCU = "#fef3c7"
ACIK_MOR = "#ede9fe"
ACIK_KIRMIZI = "#fee2e2"
KUME_RENKLERI = [MAVI, YESIL, TURUNCU]

plt.rcParams.update(
    {
        "svg.fonttype": "none",
        "svg.hashsalt": "vm-ders",
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": GRI,
        "axes.labelcolor": KOYU,
        "text.color": KOYU,
        "xtick.color": KOYU,
        "ytick.color": KOYU,
        "legend.fontsize": 11,
        "legend.framealpha": 0.95,
        "legend.edgecolor": "#d1d5db",
    }
)

SONUCLAR = {}


def kaydet(fig, ad):
    yol = CIKTI / ad
    fig.savefig(yol, format="svg", facecolor="white", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    print(f"yazıldı: {yol}")


def ana_baslik(fig, metin, y=1.0):
    fig.suptitle(metin, fontsize=16, fontweight="bold", color=KOYU, y=y)


# ---------------------------------------------------------------------------
# 1. Kutu grafiği anatomisi
# ---------------------------------------------------------------------------
def sekil_kutu_grafigi():
    # 40 öğrencinin sınav notu: 37 "normal" not + 3 aykırı değer (15, 30, 99)
    notlar = np.array(
        [48, 52, 55, 57, 58, 60, 61, 63, 63, 63, 64, 65, 66, 67, 68, 68, 69, 70, 70, 71,
         72, 72, 73, 74, 75, 76, 76, 77, 77, 79, 80, 81, 82, 84, 86, 88, 90, 15, 30, 99]
    )
    q1, med, q3 = np.percentile(notlar, [25, 50, 75])
    iqr = q3 - q1
    alt_sinir, ust_sinir = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    icerde = notlar[(notlar >= alt_sinir) & (notlar <= ust_sinir)]
    alt_biyik, ust_biyik = icerde.min(), icerde.max()
    aykirilar = np.sort(notlar[(notlar < alt_sinir) | (notlar > ust_sinir)])
    SONUCLAR["kutu"] = dict(n=len(notlar), q1=q1, medyan=med, q3=q3, iqr=iqr, alt_sinir=alt_sinir,
                            ust_sinir=ust_sinir, alt_biyik=alt_biyik, ust_biyik=ust_biyik,
                            aykirilar=aykirilar.tolist(), ortalama=notlar.mean(),
                            veri=np.sort(notlar).tolist())

    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.boxplot(
        notlar, orientation="horizontal", widths=0.5, patch_artist=True, whis=1.5,
        boxprops=dict(facecolor=ACIK_MAVI, edgecolor=MAVI, linewidth=2),
        medianprops=dict(color=KIRMIZI, linewidth=2.5),
        whiskerprops=dict(color=MAVI, linewidth=2), capprops=dict(color=MAVI, linewidth=2),
        flierprops=dict(marker="o", markerfacecolor=KIRMIZI, markeredgecolor="white", markersize=10),
    )
    # Ham veri: kutunun altında hafif nokta şeridi
    rng = np.random.default_rng(42)
    ax.scatter(notlar, 0.62 + rng.uniform(-0.03, 0.03, len(notlar)), s=14, color=GRI, alpha=0.6, zorder=2)
    ax.text(101, 0.62, "ham veri\n(40 not)", fontsize=10, color=GRI, va="center", ha="left")

    # Çit (fence) çizgileri
    for x, etiket in [(alt_sinir, f"Q1 − 1.5·IQR = {alt_sinir:g}"), (ust_sinir, f"Q3 + 1.5·IQR = {ust_sinir:g}")]:
        ax.axvline(x, ymin=0.08, ymax=0.62, color=GRI, linestyle=":", linewidth=1.3)
        ax.text(x, 0.36, etiket, fontsize=10, color=GRI, ha="center", va="top",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"))

    ok = dict(arrowstyle="->", color=KOYU, linewidth=1.2)
    # Q1, Q3 (üstte), medyan (altta)
    ax.annotate(f"Q1 (%25) = {q1:g}", xy=(q1, 1.25), xytext=(q1 - 6, 1.66), ha="center", va="bottom",
                fontsize=12, arrowprops=ok)
    ax.annotate(f"Q3 (%75) = {q3:g}", xy=(q3, 1.25), xytext=(q3 + 6, 1.66), ha="center", va="bottom",
                fontsize=12, arrowprops=ok)
    ax.annotate(f"Medyan (Q2) = {med:g}", xy=(med, 0.75), xytext=(med, 0.47), ha="center", va="top",
                fontsize=12, color=KIRMIZI, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=KIRMIZI, linewidth=1.2))
    # IQR çift yönlü ok
    ax.annotate("", xy=(q1, 1.36), xytext=(q3, 1.36),
                arrowprops=dict(arrowstyle="<->", color=MOR, linewidth=1.8, shrinkA=0, shrinkB=0))
    ax.plot([q1, q1], [1.27, 1.42], color=MOR, linewidth=1.2)
    ax.plot([q3, q3], [1.27, 1.42], color=MOR, linewidth=1.2)
    ax.text(med, 1.45, f"IQR = Q3 − Q1 = {iqr:g}", ha="center", va="bottom", color=MOR, fontsize=12,
            fontweight="bold")
    # Bıyıklar
    ax.annotate(f"Minimum (alt bıyık) = {alt_biyik:g}", xy=(alt_biyik, 1.12), xytext=(alt_biyik - 4, 2.1),
                ha="center", va="bottom", fontsize=12, arrowprops=ok)
    ax.annotate(f"Maksimum (üst bıyık) = {ust_biyik:g}", xy=(ust_biyik, 1.12), xytext=(ust_biyik + 2, 2.1),
                ha="center", va="bottom", fontsize=12, arrowprops=ok)
    # Aykırı değerler
    alt_ayk = aykirilar[aykirilar < med]
    ust_ayk = aykirilar[aykirilar > med]
    ax.text(alt_ayk.mean(), 1.66, "Aykırı değerler\n(< Q1 − 1.5·IQR)", ha="center", va="bottom", fontsize=11,
            color=KIRMIZI, fontweight="bold")
    for x in alt_ayk:
        ax.annotate("", xy=(x, 1.07), xytext=(alt_ayk.mean(), 1.64),
                    arrowprops=dict(arrowstyle="->", color=KIRMIZI, linewidth=1.2))
    ax.text(ust_ayk.mean() + 4, 1.66, "Aykırı değer\n(> Q3 + 1.5·IQR)", ha="center", va="bottom", fontsize=11,
            color=KIRMIZI, fontweight="bold")
    for x in ust_ayk:
        ax.annotate("", xy=(x, 1.07), xytext=(ust_ayk.mean() + 3, 1.64),
                    arrowprops=dict(arrowstyle="->", color=KIRMIZI, linewidth=1.2))
    ax.set_ylim(0.1, 2.5)
    ax.set_xlim(5, 112)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Sınav notu")
    ax.set_xticks(range(10, 101, 10))
    ana_baslik(fig, "Kutu Grafiğinin (Box Plot) Anatomisi – 40 Öğrencinin Sınav Notu")
    kaydet(fig, "vm-kutu-grafigi.svg")


# ---------------------------------------------------------------------------
# 2. Uzaklık ölçüleri
# ---------------------------------------------------------------------------
def sekil_uzaklik_olculeri():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6))

    # Sol: Öklid ve Manhattan
    P, Q = np.array([1, 1]), np.array([4, 5])
    ax1.set_xticks(range(0, 7))
    ax1.set_yticks(range(0, 7))
    ax1.grid(True, color="#e5e7eb", linewidth=1)
    ax1.set_axisbelow(True)
    yol_x = [1, 2, 2, 3, 3, 4, 4, 4]
    yol_y = [1, 1, 2, 2, 3, 3, 4, 5]
    ax1.plot([P[0], Q[0]], [P[1], Q[1]], color=MAVI, linewidth=3, label="Öklid: √(3² + 4²) = 5", zorder=4)
    ax1.plot(yol_x, yol_y, color=TURUNCU, linewidth=3, label="Manhattan: |3| + |4| = 7", zorder=3,
             solid_joinstyle="miter")
    ax1.scatter(*np.vstack([P, Q]).T, s=110, color=KOYU, zorder=5)
    ax1.text(P[0] - 0.15, P[1] - 0.3, "P = (1, 1)", ha="right", va="top", fontsize=12, fontweight="bold")
    ax1.text(Q[0] + 0.15, Q[1] + 0.15, "Q = (4, 5)", ha="left", va="bottom", fontsize=12, fontweight="bold")
    ax1.set_xlim(-0.5, 6.5)
    ax1.set_ylim(-0.5, 6.5)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x₁")
    ax1.set_ylabel("x₂")
    ax1.set_title("Öklid ve Manhattan Uzaklığı")
    ax1.legend(loc="upper left", fontsize=11)

    # Sağ: Kosinüs benzerliği
    A, B, C = np.array([4, 1]), np.array([2, 3]), np.array([4, 6])
    cos_ab = A @ B / (np.linalg.norm(A) * np.linalg.norm(B))
    teta = np.degrees(np.arccos(cos_ab))
    SONUCLAR["kosinus"] = dict(cos_ab=cos_ab, teta_derece=teta,
                               cos_bc=B @ C / (np.linalg.norm(B) * np.linalg.norm(C)))
    ax2.grid(True, color="#f3f4f6", linewidth=1)
    ax2.set_axisbelow(True)
    ax2.annotate("", xy=C, xytext=(0, 0),
                 arrowprops=dict(arrowstyle="-|>", color=MOR, linewidth=2, linestyle=(0, (5, 4)),
                                 mutation_scale=18))
    for v, renk in [(A, MAVI), (B, YESIL)]:
        ax2.annotate("", xy=v, xytext=(0, 0),
                     arrowprops=dict(arrowstyle="-|>", color=renk, linewidth=3, mutation_scale=22))
    ax2.text(A[0] + 0.15, A[1] - 0.1, "A = (4, 1)", color=MAVI, fontsize=12, fontweight="bold", va="center")
    ax2.text(B[0] - 0.2, B[1] + 0.05, "B = (2, 3)", color=YESIL, fontsize=12, fontweight="bold", ha="right")
    ax2.text(C[0] + 0.15, C[1], "C = (4, 6) = 2·B", color=MOR, fontsize=12, fontweight="bold", va="center")
    a1, a2 = np.degrees(np.arctan2(A[1], A[0])), np.degrees(np.arctan2(B[1], B[0]))
    ax2.add_patch(Arc((0, 0), 2.4, 2.4, theta1=a1, theta2=a2, color=KOYU, linewidth=1.8))
    orta = np.radians((a1 + a2) / 2)
    ax2.text(1.55 * np.cos(orta), 1.55 * np.sin(orta), "θ", fontsize=16, ha="center", va="center",
             fontweight="bold")
    ax2.text(0.2, 7.3,
             f"cos θ = A·B / (‖A‖‖B‖) = 11 / (√17·√13) = {cos_ab:.3f}\n"
             f"θ ≈ {teta:.1f}°",
             fontsize=12, va="top",
             bbox=dict(boxstyle="round,pad=0.4", facecolor=ACIK_YESIL, edgecolor=YESIL))
    ax2.text(5.6, 2.9, "cos(B, C) = 1\nAynı yön, farklı uzunluk", fontsize=11, color=MOR, ha="center",
             va="center", bbox=dict(boxstyle="round,pad=0.35", facecolor=ACIK_MOR, edgecolor=MOR))
    ax2.text(7.0, 0.05, "Kosinüs benzerliği\nbüyüklüğe değil yöne bakar", fontsize=11, ha="right",
             va="bottom", style="italic", color=KOYU)
    ax2.set_xlim(-0.3, 7.2)
    ax2.set_ylim(-0.3, 7.5)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x₁")
    ax2.set_ylabel("x₂")
    ax2.set_title("Kosinüs Benzerliği")

    ana_baslik(fig, "Uzaklık ve Benzerlik Ölçüleri")
    fig.tight_layout()
    kaydet(fig, "vm-uzaklik-olculeri.svg")


# ---------------------------------------------------------------------------
# 3. PCA
# ---------------------------------------------------------------------------
def sekil_pca():
    from sklearn.decomposition import PCA

    rng = np.random.default_rng(42)
    X = rng.multivariate_normal([0, 0], [[3, 2.4], [2.4, 2.5]], size=200)
    pca = PCA(n_components=2).fit(X)
    bilesen = pca.components_.copy()
    for i in range(2):  # yönleri okunaklı olsun diye işaret sabitle
        if bilesen[i, 0] < 0 or (abs(bilesen[i, 0]) < 1e-9 and bilesen[i, 1] < 0):
            bilesen[i] *= -1
    if bilesen[1, 1] < 0:
        bilesen[1] *= -1
    oran = pca.explained_variance_ratio_ * 100
    var = pca.explained_variance_
    ort = pca.mean_
    z1 = (X - ort) @ bilesen[0]
    SONUCLAR["pca"] = dict(pc1_yuzde=oran[0], pc2_yuzde=oran[1], varyanslar=var.tolist(),
                           bilesenler=bilesen.tolist())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax1.scatter(X[:, 0], X[:, 1], s=22, color=MAVI, alpha=0.55, edgecolor="none")
    # Birkaç noktanın PC1'e izdüşümü
    for i in range(0, 200, 13):
        p = ort + z1[i] * bilesen[0]
        ax1.plot([X[i, 0], p[0]], [X[i, 1], p[1]], color=GRI, linewidth=0.8, alpha=0.7)
    t = np.linspace(-6, 6, 2)
    ax1.plot(ort[0] + t * bilesen[0, 0], ort[1] + t * bilesen[0, 1], color=KIRMIZI, linewidth=1,
             linestyle="--", alpha=0.6)
    for i, (renk, ad) in enumerate([(KIRMIZI, "PC1"), (TURUNCU, "PC2")]):
        uc = ort + 2 * np.sqrt(var[i]) * bilesen[i]
        ax1.annotate("", xy=uc, xytext=ort,
                     arrowprops=dict(arrowstyle="-|>", color=renk, linewidth=3.5, mutation_scale=22))
        ofset = bilesen[i] * 0.35
        ax1.text(uc[0] + ofset[0], uc[1] + ofset[1], f"{ad} (%{oran[i]:.1f} varyans)", color=renk,
                 fontsize=12, fontweight="bold", ha="left" if i == 0 else "right", va="center",
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.85))
    ax1.set_aspect("equal")
    ax1.set_xlim(-6.5, 6.5)
    ax1.set_ylim(-6, 6)
    ax1.set_xlabel("x₁")
    ax1.set_ylabel("x₂")
    ax1.set_title("Orijinal 2B veri ve temel bileşenler")

    ax2.hist(z1, bins=24, color=ACIK_MAVI, edgecolor=MAVI, linewidth=1)
    ax2.plot(z1, np.full_like(z1, -1.2), "|", color=KIRMIZI, markersize=14, alpha=0.6)
    ax2.axhline(0, color=GRI, linewidth=0.8)
    ax2.set_ylim(-2.5, None)
    ax2.set_xlabel("PC1 skoru (izdüşüm)")
    ax2.set_ylabel("Frekans")
    ax2.set_title("1 boyuta indirgenmiş veri (PC1)")
    ax2.text(0.02, 0.97, f"Korunan bilgi: varyansın %{oran[0]:.1f}'i\n2 özellik → 1 özellik",
             transform=ax2.transAxes, va="top", fontsize=11,
             bbox=dict(boxstyle="round,pad=0.4", facecolor=ACIK_KIRMIZI, edgecolor=KIRMIZI))

    ana_baslik(fig, "Temel Bileşen Analizi (PCA)")
    fig.tight_layout()
    kaydet(fig, "vm-pca.svg")


# ---------------------------------------------------------------------------
# 4. k-NN
# ---------------------------------------------------------------------------
def sekil_knn():
    sorgu = np.array([5.0, 5.0])

    def kutupsal(r, aci):
        a = np.radians(aci)
        return sorgu + r * np.array([np.cos(a), np.sin(a)])

    # Yakın komşular (uzaklıkları elle seçildi)
    A = [kutupsal(1.0, 160), kutupsal(1.3, 230), kutupsal(2.3, 120)]
    B = [kutupsal(1.5, 20), kutupsal(1.9, 300), kutupsal(2.1, 70), kutupsal(2.5, 340)]
    A += [np.array(p) for p in [(1.2, 6.5), (1.8, 4.2), (2.0, 7.5), (1.0, 3.0), (2.5, 2.2), (0.8, 5.2),
                                (2.6, 8.4), (1.5, 8.8), (0.5, 7.0)]]
    B += [np.array(p) for p in [(8.5, 6.5), (9.0, 4.0), (8.2, 2.8), (9.3, 7.6), (7.6, 1.6), (8.8, 5.4),
                                (7.8, 8.3), (9.5, 2.0)]]
    A, B = np.array(A), np.array(B)
    X = np.vstack([A, B])
    y = np.array(["A"] * len(A) + ["B"] * len(B))
    d = np.linalg.norm(X - sorgu, axis=1)
    sira = np.argsort(d)

    def oy(k):
        komsu = y[sira[:k]]
        return int((komsu == "A").sum()), int((komsu == "B").sum())

    a3, b3 = oy(3)
    a7, b7 = oy(7)
    assert (a3, b3) == (2, 1) and (a7, b7) == (3, 4), (a3, b3, a7, b7)
    r3 = (d[sira[2]] + d[sira[3]]) / 2
    r7 = (d[sira[6]] + d[sira[7]]) / 2
    SONUCLAR["knn"] = dict(nA=len(A), nB=len(B), k3=(a3, b3), k7=(a7, b7),
                           siralı_uzakliklar=[(y[i], round(float(d[i]), 2)) for i in sira[:8]])

    fig, ax = plt.subplots(figsize=(10.5, 8.6))
    ax.add_patch(Circle(sorgu, r3, fill=True, facecolor="#eef4fe", edgecolor=MAVI, linewidth=2.2))
    ax.add_patch(Circle(sorgu, r7, fill=False, edgecolor=TURUNCU, linewidth=2.2, linestyle=(0, (6, 4))))
    for i in sira[:7]:
        ax.plot([sorgu[0], X[i, 0]], [sorgu[1], X[i, 1]], color=GRI, linewidth=0.8, alpha=0.6, zorder=1)
    ax.scatter(A[:, 0], A[:, 1], s=110, marker="o", color=MAVI, edgecolor="white", linewidth=1.2,
               label="Sınıf A", zorder=3)
    ax.scatter(B[:, 0], B[:, 1], s=130, marker="^", color=TURUNCU, edgecolor="white", linewidth=1.2,
               label="Sınıf B", zorder=3)
    ax.scatter(*sorgu, s=420, marker="*", color=KOYU, zorder=4, label="Sorgu noktası (?)")
    ax.text(sorgu[0] + 0.22, sorgu[1] + 0.2, "?", fontsize=18, fontweight="bold", zorder=5)
    # Komşu sırası numaraları
    for n, i in enumerate(sira[:7], start=1):
        v = X[i] - sorgu
        v = v / np.linalg.norm(v)
        ax.text(X[i, 0] + 0.33 * v[0], X[i, 1] + 0.33 * v[1], str(n), fontsize=10, color=GRI,
                ha="center", va="center", fontweight="bold")

    ax.annotate(f"k = 3 → Sınıf A ({a3}–{b3})", xy=sorgu + r3 * np.array([np.cos(np.radians(250)),
                                                                         np.sin(np.radians(250))]),
                xytext=(3.2, 0.6), fontsize=13, fontweight="bold", color=MAVI, ha="center",
                arrowprops=dict(arrowstyle="->", color=MAVI, linewidth=1.4),
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=MAVI))
    ax.annotate(f"k = 7 → Sınıf B ({b7}–{a7})", xy=sorgu + r7 * np.array([np.cos(np.radians(95)),
                                                                         np.sin(np.radians(95))]),
                xytext=(5.0, 9.6), fontsize=13, fontweight="bold", color="#b45309", ha="center",
                arrowprops=dict(arrowstyle="->", color=TURUNCU, linewidth=1.4),
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=TURUNCU))
    ax.text(10.4, 0.0, "Gri sayılar: sorguya yakınlık sırası", fontsize=10, color=GRI, ha="right")
    ax.set_aspect("equal")
    ax.set_xlim(-0.2, 10.4)
    ax.set_ylim(-0.2, 10.4)
    ax.set_xlabel("Özellik 1")
    ax.set_ylabel("Özellik 2")
    ax.legend(loc="upper right", fontsize=11)
    ana_baslik(fig, "k-En Yakın Komşu (k-NN): k Değeri Kararı Değiştirebilir", y=0.93)
    kaydet(fig, "vm-knn.svg")


# ---------------------------------------------------------------------------
# 5. ROC eğrisi
# ---------------------------------------------------------------------------
def sekil_roc():
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, roc_curve
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    X, y = make_classification(n_samples=2000, n_features=20, n_informative=5, random_state=42)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    # Üçüncü model kasten zayıf: yalnızca tek bir özellik (x₃, indeks 2) kullanan lojistik regresyon
    modeller = [
        ("Lojistik Regresyon", LogisticRegression(max_iter=1000), slice(None), MAVI),
        ("Karar Ağacı (max_depth=3)", DecisionTreeClassifier(max_depth=3, random_state=42), slice(None), YESIL),
        ("Zayıf model: tek özellikli Lojistik Regresyon", LogisticRegression(max_iter=1000), [2], MOR),
    ]
    sonuc = []
    for ad, m, sut, renk in modeller:
        m.fit(Xtr[:, sut], ytr)
        p = m.predict_proba(Xte[:, sut])[:, 1]
        fpr, tpr, _ = roc_curve(yte, p)
        sonuc.append((ad, fpr, tpr, roc_auc_score(yte, p), renk))
    SONUCLAR["roc"] = {ad: round(auc, 4) for ad, _, _, auc, _ in sonuc}
    SONUCLAR["roc_bolme"] = dict(egitim=len(ytr), test=len(yte))

    fig, ax = plt.subplots(figsize=(9.5, 8.2))
    en_iyi = max(sonuc, key=lambda s: s[3])
    ax.fill_between(en_iyi[1], en_iyi[2], step=None, color=en_iyi[4], alpha=0.12, linewidth=0)
    for ad, fpr, tpr, auc, renk in sonuc:
        ax.plot(fpr, tpr, color=renk, linewidth=2.4, label=f"{ad} (AUC = {auc:.2f})")
    ax.plot([0, 1], [0, 1], color=GRI, linestyle="--", linewidth=1.6, label="Rastgele tahmin (AUC = 0.50)")
    ax.scatter([0], [1], s=90, color=KOYU, zorder=5, clip_on=False)
    ax.annotate("İdeal sınıflandırıcı", xy=(0, 1), xytext=(0.05, 0.94), fontsize=11, va="center",
                arrowprops=dict(arrowstyle="->", color=KOYU, linewidth=1.2, shrinkB=5))
    ax.text(0.62, 0.42, f"Gölgeli alan = AUC\n({en_iyi[0].split(' (')[0]})", fontsize=11, color=KOYU,
            ha="center", style="italic")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_aspect("equal")
    ax.set_xlabel("Sahte Pozitif Oranı (FPR)")
    ax.set_ylabel("Gerçek Pozitif Oranı (TPR = Duyarlılık)")
    ax.grid(True, color="#f3f4f6")
    ax.legend(loc="lower right", fontsize=11)
    ana_baslik(fig, "ROC Eğrisi ve Eğri Altındaki Alan (AUC)", y=0.97)
    kaydet(fig, "vm-roc-egrisi.svg")


# ---------------------------------------------------------------------------
# 6. Aşırı öğrenme
# ---------------------------------------------------------------------------
def sekil_overfitting():
    from numpy.polynomial import Polynomial

    rng = np.random.default_rng(42)
    gercek = lambda x: np.sin(2 * np.pi * x)  # noqa: E731
    x_tr = np.sort(rng.uniform(0, 1, 20))
    y_tr = gercek(x_tr) + rng.normal(0, 0.2, 20)
    x_val = rng.uniform(0, 1, 100)
    y_val = gercek(x_val) + rng.normal(0, 0.2, 100)
    xs = np.linspace(0, 1, 500)

    dereceler = np.arange(1, 16)
    e_tr, e_val = [], []
    for d in dereceler:
        p = Polynomial.fit(x_tr, y_tr, d)
        e_tr.append(np.mean((p(x_tr) - y_tr) ** 2))
        e_val.append(np.mean((p(x_val) - y_val) ** 2))
    e_tr, e_val = np.array(e_tr), np.array(e_val)
    en_iyi = int(dereceler[np.argmin(e_val)])
    SONUCLAR["overfitting"] = dict(en_iyi_derece=en_iyi,
                                   egitim_mse={int(d): round(float(e), 4) for d, e in zip(dereceler, e_tr)},
                                   dogrulama_mse={int(d): round(float(e), 4) for d, e in zip(dereceler, e_val)})

    fig = plt.figure(figsize=(13, 9.2))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[1, 1.1], hspace=0.42, wspace=0.22)
    paneller = [(1, "Eksik Öğrenme (Underfitting)\nderece 1", KIRMIZI),
                (4, "Uygun Model\nderece 4", YESIL),
                (15, "Aşırı Öğrenme (Overfitting)\nderece 15", MOR)]
    for j, (d, baslik, renk) in enumerate(paneller):
        ax = fig.add_subplot(gs[0, j])
        p = Polynomial.fit(x_tr, y_tr, d)
        ax.plot(xs, gercek(xs), color=GRI, linestyle="--", linewidth=1.5, label="Gerçek fonksiyon")
        ax.plot(xs, p(xs), color=renk, linewidth=2.4, label="Model")
        ax.scatter(x_tr, y_tr, s=36, color=MAVI, edgecolor="white", zorder=3, label="Eğitim verisi")
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlim(0, 1)
        ax.set_title(baslik, fontsize=13, color=renk)
        v = e_val[d - 1]
        us = int(np.floor(np.log10(v)))
        ust_simge = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        v_metin = f"= {v:.3f}" if v < 100 else f"≈ {v / 10 ** us:.1f} × 10{str(us).translate(ust_simge)}"
        ax.text(0.97, 0.04, f"Eğitim MSE = {e_tr[d - 1]:.3f}\nDoğrulama MSE {v_metin}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#d1d5db", alpha=0.9))
        ax.set_xlabel("x")
        if j == 0:
            ax.set_ylabel("y")
            ax.legend(loc="upper right", fontsize=10, framealpha=0.95)

    ax = fig.add_subplot(gs[1, :])
    ax.axvspan(0.5, en_iyi - 0.5, color=ACIK_KIRMIZI, alpha=0.6, linewidth=0)
    ax.axvspan(en_iyi + 0.5, 15.5, color=ACIK_MOR, alpha=0.6, linewidth=0)
    ax.plot(dereceler, e_tr, "-o", color=MAVI, linewidth=2.4, markersize=7, label="Eğitim hatası")
    ax.plot(dereceler, e_val, "-s", color=TURUNCU, linewidth=2.4, markersize=7, label="Doğrulama hatası")
    ax.scatter([en_iyi], [e_val[en_iyi - 1]], s=320, facecolor="none", edgecolor=YESIL, linewidth=2.5, zorder=5)
    ax.annotate(f"En düşük doğrulama hatası\n(derece {en_iyi}, MSE = {e_val[en_iyi - 1]:.3f})",
                xy=(en_iyi, e_val[en_iyi - 1]), xytext=(en_iyi + 1.0, 3.0),
                fontsize=11, color="#047857", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=YESIL, linewidth=1.4))
    ax.set_yscale("log")
    ax.set_xlim(0.5, 15.5)
    ax.set_xticks(dereceler)
    ax.set_xlabel("Model karmaşıklığı (polinom derecesi)")
    ax.set_ylabel("Hata (MSE, log ölçek)")
    ax.set_title("Eğitim ve Doğrulama Hatası – Yanlılık–Varyans Dengesi")
    ax.legend(loc="center left", fontsize=11)
    ax.text(0.03, 0.93, "Yüksek yanlılık (bias)\n← eksik öğrenme", transform=ax.transAxes, fontsize=12,
            color="#b91c1c", fontweight="bold", va="top")
    ax.text(12.6, 3e4, "Yüksek varyans\naşırı öğrenme →", fontsize=12,
            color="#6d28d9", fontweight="bold", va="center", ha="right")
    ax.grid(True, axis="y", color="#f3f4f6")
    ana_baslik(fig, "Eksik Öğrenme, Uygun Model ve Aşırı Öğrenme", y=0.995)
    kaydet(fig, "vm-overfitting.svg")


# ---------------------------------------------------------------------------
# 7. k-Means iterasyonları
# ---------------------------------------------------------------------------
def kmeans_elle(X, merkezler, maks_iter=100):
    """Lloyd algoritması; her adımın atama ve merkezlerini döndürür."""
    gecmis_merkez = [np.array(merkezler, dtype=float)]
    gecmis_atama = []
    C = gecmis_merkez[0]
    for _ in range(maks_iter):
        uzaklik = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        atama = uzaklik.argmin(1)
        yeni = np.array([X[atama == k].mean(0) if np.any(atama == k) else C[k] for k in range(len(C))])
        gecmis_atama.append(atama)
        gecmis_merkez.append(yeni)
        if len(gecmis_atama) > 1 and np.array_equal(gecmis_atama[-1], gecmis_atama[-2]):
            break
        C = yeni
    return gecmis_merkez, gecmis_atama


def sekil_kmeans_iterasyon():
    from sklearn.datasets import make_blobs

    X, _ = make_blobs(n_samples=150, centers=3, random_state=42)
    # Kasten kötü başlangıç: üç merkez de sol üst köşede, aynı kümenin yakınında
    baslangic = [(-4.0, 11.0), (-6.0, 10.0), (-4.0, 9.0)]
    merkez, atama = kmeans_elle(X, baslangic)
    n_iter = len(atama)  # son iterasyonda hiçbir nokta küme değiştirmedi
    son_hareket = [float(np.abs(merkez[i] - merkez[i - 1]).max()) for i in range(1, len(merkez))]
    sse = float(((X - merkez[-1][atama[-1]]) ** 2).sum())
    SONUCLAR["kmeans"] = dict(yakinsama_iterasyonu=n_iter, merkez_hareketleri=[round(h, 3) for h in son_hareket],
                              son_merkezler=np.round(merkez[-1], 2).tolist(), sse=round(sse, 2),
                              baslangic=baslangic)

    fig, eksenler = plt.subplots(2, 2, figsize=(12, 11))
    eksenler = eksenler.ravel()
    paneller = [
        (None, 0, "Başlangıç: rastgele 3 merkez"),
        (0, 1, "İterasyon 1"),
        (1, 2, "İterasyon 2"),
        (n_iter - 1, n_iter, f"Yakınsama (iterasyon {n_iter})"),
    ]
    for ax, (ai, mi, baslik) in zip(eksenler, paneller):
        if ai is None:
            ax.scatter(X[:, 0], X[:, 1], s=28, color="#9ca3af", edgecolor="white", linewidth=0.4)
        else:
            renkler = np.array(KUME_RENKLERI)[atama[ai]]
            ax.scatter(X[:, 0], X[:, 1], s=28, c=renkler, edgecolor="white", linewidth=0.4, alpha=0.9)
        C = merkez[mi]
        if mi >= 1:
            if mi == n_iter:  # son panel: tüm yörünge
                for k in range(3):
                    yorunge = np.array([m[k] for m in merkez])
                    ax.plot(yorunge[:, 0], yorunge[:, 1], color=KOYU, linewidth=1, linestyle=":", alpha=0.8)
                    ax.scatter(yorunge[:-1, 0], yorunge[:-1, 1], s=22, color=KOYU, alpha=0.5, zorder=4)
            else:
                onceki = merkez[mi - 1]
                for k in range(3):
                    ax.annotate("", xy=C[k], xytext=onceki[k],
                                arrowprops=dict(arrowstyle="-|>", color=KOYU, linewidth=1.6,
                                                mutation_scale=14, shrinkA=2, shrinkB=8))
                    ax.scatter(*onceki[k], s=110, marker="X", facecolor="white", edgecolor=KOYU,
                               linewidth=1.2, zorder=4)
        ax.scatter(C[:, 0], C[:, 1], s=320, marker="X", c=KUME_RENKLERI, edgecolor="black", linewidth=1.8,
                   zorder=6)
        ax.set_title(baslik)
        ax.set_xlim(-12, 9)
        ax.set_ylim(-11, 12.5)
        ax.set_aspect("equal")
        ax.grid(True, color="#f3f4f6")
    eksenler[1].text(0.02, 0.02, "Oklar: merkezin önceki konumundan\nyeni konumuna hareketi",
                     transform=eksenler[1].transAxes, fontsize=10, color=GRI, va="bottom")
    eksenler[3].text(0.02, 0.02, f"Noktalı çizgi: merkezlerin {n_iter} iterasyonluk yolu\n"
                                 f"Son iterasyonda hiçbir nokta küme değiştirmedi",
                     transform=eksenler[3].transAxes, fontsize=10, color=GRI, va="bottom")
    efsane = [Line2D([], [], marker="X", linestyle="none", markersize=14, markerfacecolor=MAVI,
                     markeredgecolor="black", label="Küme merkezi (centroid)"),
              Line2D([], [], marker="X", linestyle="none", markersize=10, markerfacecolor="white",
                     markeredgecolor=KOYU, label="Merkezin önceki konumu")]
    fig.legend(handles=efsane, loc="lower center", ncol=2, fontsize=11, bbox_to_anchor=(0.5, -0.01),
               frameon=False)
    ana_baslik(fig, "k-Means Algoritmasının Adım Adım Çalışması (k = 3)", y=0.995)
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    kaydet(fig, "vm-kmeans-iterasyon.svg")


# ---------------------------------------------------------------------------
# 8. Dendrogram
# ---------------------------------------------------------------------------
def sekil_dendrogram():
    from scipy.cluster.hierarchy import dendrogram, fcluster, linkage, set_link_color_palette

    noktalar = {
        "A": (1.0, 1.2), "C": (1.8, 2.1), "E": (2.3, 1.0),
        "B": (5.4, 5.0), "F": (6.3, 5.9), "H": (5.0, 6.3), "J": (6.1, 4.5),
        "D": (8.6, 1.4), "G": (9.4, 2.5), "I": (8.1, 2.7),
    }
    etiketler = sorted(noktalar)
    X = np.array([noktalar[e] for e in etiketler])
    Z = linkage(X, method="average")
    kesim = (Z[-3, 2] + Z[-2, 2]) / 2  # 3 küme veren yükseklik
    kume = fcluster(Z, t=3, criterion="maxclust")
    assert len(set(kume)) == 3

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw=dict(width_ratios=[1, 1.1]))
    set_link_color_palette(KUME_RENKLERI)
    dn = dendrogram(Z, labels=etiketler, ax=ax2, color_threshold=kesim, above_threshold_color=GRI,
                    leaf_font_size=13)
    set_link_color_palette(None)
    yaprak_renk = dict(zip(dn["ivl"], dn["leaves_color_list"]))
    for koll in ax2.collections:
        koll.set_linewidth(2.2)
    ax2.axhline(kesim, color=KIRMIZI, linestyle="--", linewidth=1.8)
    ax2.text(ax2.get_xlim()[1] * 0.99, kesim + 0.12, "Kesim → 3 küme", color=KIRMIZI, ha="right",
             va="bottom", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Birleşme uzaklığı")
    ax2.set_title("Dendrogram (ortalama bağlantı)")
    ax2.spines["bottom"].set_visible(False)

    for e, (x, y) in noktalar.items():
        ax1.scatter(x, y, s=180, color=yaprak_renk[e], edgecolor="white", linewidth=1.5, zorder=3)
        ax1.text(x + 0.22, y + 0.18, e, fontsize=13, fontweight="bold")
    ax1.set_xlim(0, 10.5)
    ax1.set_ylim(0, 7.5)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x₁")
    ax1.set_ylabel("x₂")
    ax1.set_title("10 nokta (A–J)")
    ax1.grid(True, color="#f3f4f6")
    SONUCLAR["dendrogram"] = dict(kesim=round(float(kesim), 3),
                                  birlesme_yukseklikleri=np.round(Z[:, 2], 3).tolist(),
                                  kumeler={e: int(k) for e, k in zip(etiketler, kume)})
    ana_baslik(fig, "Hiyerarşik Kümeleme ve Dendrogram")
    fig.tight_layout()
    kaydet(fig, "vm-dendrogram.svg")


# ---------------------------------------------------------------------------
# 9. DBSCAN
# ---------------------------------------------------------------------------
def sekil_dbscan():
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.datasets import make_moons

    X, _ = make_moons(n_samples=300, noise=0.07, random_state=42)
    rng = np.random.default_rng(42)
    gurultu = np.column_stack([rng.uniform(-1.5, 2.5, 15), rng.uniform(-1.0, 1.6, 15)])
    X = np.vstack([X, gurultu])
    eps, min_pts = 0.2, 5
    db = DBSCAN(eps=eps, min_samples=min_pts).fit(X)
    etiket = db.labels_
    cekirdek = np.zeros(len(X), dtype=bool)
    cekirdek[db.core_sample_indices_] = True
    sinir = (etiket != -1) & ~cekirdek
    gur = etiket == -1
    n_kume = len(set(etiket) - {-1})
    SONUCLAR["dbscan"] = dict(eps=eps, min_pts=min_pts, n_nokta=len(X), n_kume=n_kume,
                              n_cekirdek=int(cekirdek.sum()), n_sinir=int(sinir.sum()), n_gurultu=int(gur.sum()))
    km = KMeans(n_clusters=2, n_init=10, random_state=42).fit(X)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.6), gridspec_kw=dict(width_ratios=[1.45, 1]))
    renk = [MAVI, TURUNCU, YESIL, MOR]
    for k in range(n_kume):
        m = (etiket == k) & cekirdek
        ax1.scatter(X[m, 0], X[m, 1], s=42, color=renk[k], edgecolor="white", linewidth=0.5, zorder=3)
        m = (etiket == k) & sinir
        ax1.scatter(X[m, 0], X[m, 1], s=46, facecolor="white", edgecolor=renk[k], linewidth=1.8, zorder=4)
    ax1.scatter(X[gur, 0], X[gur, 1], s=60, marker="x", color=GRI, linewidth=2, zorder=4)
    # ε dairesi: üst hilalin sol ucundaki bir çekirdek nokta
    adaylar = np.where(cekirdek)[0]
    merkez_i = adaylar[np.argmin(np.linalg.norm(X[adaylar] - np.array([-0.9, 0.35]), axis=1))]
    c = X[merkez_i]
    ax1.add_patch(Circle(c, eps, fill=False, edgecolor=KOYU, linestyle="--", linewidth=1.6, zorder=5))
    ax1.plot([c[0], c[0] - eps], [c[1], c[1]], color=KOYU, linewidth=1.4, zorder=5)
    ax1.annotate(f"ε yarıçapı (ε = {eps})", xy=(c[0] - eps / 2, c[1]), xytext=(-1.55, -0.45), fontsize=11,
                 arrowprops=dict(arrowstyle="->", color=KOYU, linewidth=1.2))
    ax1.set_aspect("equal")
    ax1.set_xlim(-1.65, 2.65)
    ax1.set_ylim(-1.1, 1.75)
    ax1.set_title(f"DBSCAN (ε = {eps}, minPts = {min_pts}) → {n_kume} küme, {int(gur.sum())} gürültü")
    efsane = [
        Line2D([], [], marker="o", linestyle="none", markersize=9, markerfacecolor=MAVI, markeredgecolor="white",
               label="Çekirdek nokta"),
        Line2D([], [], marker="o", linestyle="none", markersize=9, markerfacecolor="white",
               markeredgecolor=MAVI, markeredgewidth=1.8, label="Sınır noktası"),
        Line2D([], [], marker="x", linestyle="none", markersize=9, color=GRI, markeredgewidth=2,
               label="Gürültü (aykırı)"),
    ]
    ax1.legend(handles=efsane, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=11,
               frameon=False)

    ax2.scatter(X[:, 0], X[:, 1], s=26, c=np.array([MAVI, TURUNCU])[km.labels_], edgecolor="white",
                linewidth=0.4)
    ax2.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1], s=260, marker="X",
                c=[MAVI, TURUNCU], edgecolor="black", linewidth=1.6, zorder=5)
    ax2.set_aspect("equal")
    ax2.set_xlim(-1.65, 2.65)
    ax2.set_ylim(-1.1, 1.75)
    ax2.set_title("Karşılaştırma: k-Means (k = 2)")
    ax2.text(0.5, 0.97, "k-Means hilal şekillerini ayıramaz", transform=ax2.transAxes, ha="center", va="top",
             fontsize=11, color="#b91c1c", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor=ACIK_KIRMIZI, edgecolor=KIRMIZI))
    ana_baslik(fig, "Yoğunluk Tabanlı Kümeleme: DBSCAN")
    fig.tight_layout()
    kaydet(fig, "vm-dbscan.svg")


# ---------------------------------------------------------------------------
# 10. Aykırı değer türleri
# ---------------------------------------------------------------------------
def sekil_aykiri_deger_turleri():
    rng = np.random.default_rng(42)
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5.2), gridspec_kw=dict(width_ratios=[1, 1.15, 1.3]))

    # (a) Global
    k1 = rng.normal([2, 2], 0.45, size=(40, 2))
    k2 = rng.normal([5, 4.5], 0.5, size=(40, 2))
    ax1.scatter(*k1.T, s=30, color=MAVI, edgecolor="white", linewidth=0.4)
    ax1.scatter(*k2.T, s=30, color=YESIL, edgecolor="white", linewidth=0.4)
    o = np.array([7.6, 0.8])
    ax1.scatter(*o, s=130, color=KIRMIZI, edgecolor="white", linewidth=1.2, zorder=4)
    ax1.annotate("Global aykırı değer", xy=o, xytext=(5.6, 2.0), fontsize=11, color="#b91c1c",
                 fontweight="bold", ha="center",
                 arrowprops=dict(arrowstyle="->", color=KIRMIZI, linewidth=1.4, shrinkB=7))
    ax1.set_xlim(0, 9)
    ax1.set_ylim(0, 6.5)
    ax1.set_xlabel("x₁")
    ax1.set_ylabel("x₂")
    ax1.set_title("(a) Global aykırı değer")
    ax1.text(0.03, 0.97, "Tüm veriden uzak", transform=ax1.transAxes, fontsize=10, color=GRI, va="top")

    # (b) Bağlamsal
    aylar = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    sicaklik = [5, 6, 10, 15, 20, 26, 30, 29, 24, 18, 12, 7]
    xs = np.arange(12)
    ax2.plot(xs, sicaklik, "-o", color=MAVI, linewidth=2.2, markersize=7, label="Aylık ortalama")
    ax2.axhline(25, xmin=0.04, xmax=0.55, color=GRI, linestyle=":", linewidth=1.3)
    ax2.scatter([0], [25], s=140, color=KIRMIZI, edgecolor="white", linewidth=1.2, zorder=5,
                label="Ocak'ta ölçülen 25°C")
    ax2.annotate("Ocak'ta 25°C aykırı,\nTemmuz'da normal", xy=(0, 25), xytext=(3.2, 33.5), fontsize=11,
                 color="#b91c1c", fontweight="bold", ha="center",
                 arrowprops=dict(arrowstyle="->", color=KIRMIZI, linewidth=1.4, shrinkB=7))
    ax2.set_xticks(xs)
    ax2.set_xticklabels(aylar, fontsize=10)
    ax2.set_ylim(0, 38)
    ax2.set_ylabel("Sıcaklık (°C)")
    ax2.set_title("(b) Bağlamsal (koşullu) aykırı değer")
    ax2.legend(loc="lower center", fontsize=10)

    # (c) Kolektif
    t = np.linspace(0, 10, 2500)

    def atim(tt):
        sinyal = np.zeros_like(tt)
        for t0 in np.arange(0.3, 10.5, 0.8):
            sinyal += 0.15 * np.exp(-((tt - t0 + 0.18) / 0.04) ** 2)  # P dalgası
            sinyal += -0.12 * np.exp(-((tt - t0 + 0.04) / 0.012) ** 2)  # Q
            sinyal += 1.0 * np.exp(-((tt - t0) / 0.015) ** 2)  # R
            sinyal += -0.2 * np.exp(-((tt - t0 - 0.04) / 0.015) ** 2)  # S
            sinyal += 0.3 * np.exp(-((tt - t0 - 0.28) / 0.06) ** 2)  # T dalgası
        return sinyal

    sinyal = atim(t) + rng.normal(0, 0.012, len(t))
    a, b = 4.05, 5.9
    duz = (t >= a) & (t <= b)
    sinyal[duz] = rng.normal(0, 0.012, duz.sum())
    ax3.axvspan(a, b, color=ACIK_KIRMIZI, linewidth=0)
    ax3.plot(t[t <= a], sinyal[t <= a], color=MAVI, linewidth=1.3)
    ax3.plot(t[t >= b], sinyal[t >= b], color=MAVI, linewidth=1.3)
    ax3.plot(t[duz], sinyal[duz], color=KIRMIZI, linewidth=1.8)
    ax3.text((a + b) / 2, 1.22, "Tek tek noktalar normal,\nbirlikte anormal", ha="center", va="bottom",
             fontsize=11, color="#b91c1c", fontweight="bold")
    ax3.set_ylim(-0.4, 1.6)
    ax3.set_xlim(0, 10)
    ax3.set_xlabel("Zaman (s)")
    ax3.set_ylabel("Genlik (mV)")
    ax3.set_title("(c) Kolektif aykırı değer")

    ana_baslik(fig, "Aykırı Değer Türleri", y=1.01)
    fig.tight_layout()
    kaydet(fig, "vm-aykiri-deger-turleri.svg")


# ---------------------------------------------------------------------------
# 11. Kavram kayması
# ---------------------------------------------------------------------------
def sekil_kavram_kaymasi():
    rng = np.random.default_rng(42)
    t = np.arange(200)
    eski, yeni, s = 0.0, 2.0, 0.28
    gecis = LinearSegmentedColormap.from_list("gecis", [MAVI, TURUNCU])

    fig, eksenler = plt.subplots(2, 2, figsize=(12.5, 8.4), sharex=True, sharey=True)
    eksenler = eksenler.ravel()

    # (a) Ani
    oran_a = (t >= 100).astype(float)
    # (b) Kademeli: yeni kavramın gelme olasılığı 60→140 arasında 0'dan 1'e çıkar
    oran_b = np.clip((t - 60) / 80, 0, 1)
    # (c) Artımlı: kavram doğrusal olarak kayar
    oran_c = np.clip((t - 60) / 80, 0, 1)
    # (d) Tekrarlayan: eski kavram geri döner
    oran_d = ((t >= 70) & (t < 130)).astype(float)

    paneller = [
        ("(a) Ani (Sudden)", oran_a, "secim", "Kavram bir anda değişir", "alt"),
        ("(b) Kademeli (Gradual)", oran_b, "kademeli",
         "Geçişte iki kavram bir arada;\nyeni kavramın payı giderek artar", "alt"),
        ("(c) Artımlı (Incremental)", oran_c, "karisim", "Kavram yavaş ve sürekli kayar", "alt"),
        ("(d) Tekrarlayan (Recurring)", oran_d, "secim", "Eski kavram geri döner", "ust"),
    ]
    for ax, (baslik, oran, tur, not_metni, not_yeri) in zip(eksenler, paneller):
        gurultu = rng.normal(0, s, len(t))
        if tur in ("secim", "kademeli"):
            yeni_mi = rng.uniform(size=len(t)) < oran
            y = np.where(yeni_mi, yeni, eski) + gurultu
            renk = np.where(yeni_mi, TURUNCU, MAVI)
            ax.scatter(t, y, s=16, c=renk, edgecolor="none", alpha=0.85)
            if tur == "secim":
                ax.plot(t, eski + (yeni - eski) * oran, color=KOYU, linewidth=1.8, alpha=0.75,
                        drawstyle="steps-mid")
            else:  # iki kavram düzeyi geçiş boyunca birlikte var
                ilk, son = np.argmax(oran > 0), np.argmax(oran >= 1)
                ax.plot(t[: son + 1], np.full(son + 1, eski), color=KOYU, linewidth=1.8, alpha=0.75)
                ax.plot(t[ilk:], np.full(len(t) - ilk, yeni), color=KOYU, linewidth=1.8, alpha=0.75)
                ax.axvspan(t[ilk], t[son], color="#f3f4f6", linewidth=0, zorder=0)
        else:
            ort = eski + (yeni - eski) * oran
            ax.scatter(t, ort + gurultu, s=16, c=gecis(oran), edgecolor="none", alpha=0.85)
            ax.plot(t, ort, color=KOYU, linewidth=1.8, alpha=0.75)
        ax.text(197, 2.95 if not_yeri == "ust" else -0.95, not_metni, ha="right",
                va="top" if not_yeri == "ust" else "bottom", fontsize=10.5, color=GRI, style="italic")
        ax.set_title(baslik, loc="left")
        ax.set_xticks([])
        ax.set_yticks([eski, yeni])
        ax.set_yticklabels(["Eski\nkavram", "Yeni\nkavram"], fontsize=10)
        ax.set_ylim(-1.1, 3.1)
        ax.set_xlim(-3, 202)
    for ax in eksenler[2:]:
        ax.set_xlabel("Zaman →")
    for ax in eksenler[::2]:
        ax.set_ylabel("Veri dağılımı / kavram")
    efsane = [
        Line2D([], [], marker="o", linestyle="none", markersize=8, color=MAVI, label="Eski kavramdan örnek"),
        Line2D([], [], marker="o", linestyle="none", markersize=8, color=TURUNCU, label="Yeni kavramdan örnek"),
        Line2D([], [], color=KOYU, linewidth=1.8, label="Kavramın düzeyi (ortalama)"),
    ]
    fig.legend(handles=efsane, loc="lower center", ncol=3, fontsize=11, frameon=False, bbox_to_anchor=(0.5, -0.02))
    ana_baslik(fig, "Kavram Kayması (Concept Drift) Türleri", y=0.995)
    fig.tight_layout(rect=(0, 0.04, 1, 0.98))
    kaydet(fig, "vm-kavram-kaymasi.svg")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    CIKTI.mkdir(parents=True, exist_ok=True)
    sekil_kutu_grafigi()
    sekil_uzaklik_olculeri()
    sekil_pca()
    sekil_knn()
    sekil_roc()
    sekil_overfitting()
    sekil_kmeans_iterasyon()
    sekil_dendrogram()
    sekil_dbscan()
    sekil_aykiri_deger_turleri()
    sekil_kavram_kaymasi()
    print("\nHesaplanan değerler:")
    for ad, deger in SONUCLAR.items():
        print(f"  {ad}: {deger}")


if __name__ == "__main__":
    main()
