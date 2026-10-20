# =============================================================================
# Veri Ön İşleme Uygulaması — R (tidyverse) sürümü
#
# Kirli bir müşteri veri setini ve ikinci bir kaynaktan gelen sipariş verisini
# uçtan uca temizler, bütünleştirir, dönüştürür ve indirger. Python sürümüyle
# (../python/on_isleme.py) aynı adımları aynı kurallarla uygular; her adım
# konsola ne yaptığını yazar, grafikler ../ciktilar/r/ klasörüne kaydedilir.
#
# Adımlar
#   1. Veriyi tanıma
#   2. Veri temizleme    : gizli eksikler, metin standardizasyonu, tip dönüşümü,
#                          mükerrer kayıtlar, geçersiz değerler
#   3. Veri bütünleştirme: anahtar eşleme, para birimi, toplulaştırma, birleştirme,
#                          fazlalık analizi (korelasyon, ki-kare)
#   4. Aykırı değerler   : IQR ve z-skor, baskılama (winsorizing)
#   5. Eksik değerler    : sütun/satır silme, doldurma yöntemlerinin karşılaştırılması
#   6. Veri dönüştürme   : özellik türetme, log, normalizasyon, ayrıklaştırma, kodlama
#   7. Veri indirgeme    : sabit sütun, PCA, tabakalı örnekleme
#   8. Kaydetme ve kalite raporu
#
# Çalıştırma (uygulama klasöründen):
#   Rscript r/on_isleme.R
# RStudio'da: dosyayı açıp "Source" düğmesine basın.
#
# Gerekli paketler:
#   install.packages(c("dplyr", "tidyr", "readr", "stringr", "stringi",
#                      "ggplot2", "patchwork", "scales", "VIM"))
# =============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(readr)
  library(stringr)
  library(stringi)
  library(ggplot2)
  library(patchwork)
})

options(width = 150, dplyr.summarise.inform = FALSE)

bul_klasor <- function() {
  arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(arg)) return(normalizePath(file.path(dirname(sub("^--file=", "", arg)), "..")))
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    yol <- rstudioapi::getSourceEditorContext()$path
    if (nzchar(yol)) return(normalizePath(file.path(dirname(yol), "..")))
  }
  if (dir.exists("veri")) return(normalizePath("."))
  if (dir.exists("../veri")) return(normalizePath(".."))
  stop("Çalışma dizinini uygulama klasörüne ayarlayın: setwd('.../veri_on_isleme')")
}

KLASOR <- bul_klasor()
VERI <- file.path(KLASOR, "veri")
CIKTI <- file.path(KLASOR, "ciktilar", "r")
dir.create(CIKTI, recursive = TRUE, showWarnings = FALSE)

# "Bugün" yerine sabit bir tarih: betik hangi gün çalışırsa çalışsın aynı sonucu üretir
# (tekrar üretilebilirlik / reproducibility).
REFERANS_TARIH <- as.Date("2025-12-31")   # analizin yapıldığı gün
USD_TL <- 40                              # sabit kabul edilen döviz kuru
GIZLI_EKSIK <- c("?", "-", "N/A", "Bilinmiyor", "")

# Grafik ayarları
MAVI <- "#2a78d6"; TURUNCU <- "#eb6834"; YESIL <- "#1baf7a"
KIRMIZI <- "#e34948"; GRI <- "#a3a29d"; KOYU <- "#1f2937"
theme_set(
  theme_minimal(base_size = 11) +
    theme(plot.title = element_text(face = "bold", size = 12, hjust = 0.5),
          plot.background = element_rect(fill = "white", colour = NA),
          panel.grid.minor = element_blank(),
          panel.grid.major = element_line(colour = "#e7e6e2"),
          axis.line = element_line(colour = GRI),
          text = element_text(colour = KOYU))
)
bin_tl <- scales::label_number(scale = 1e-3, suffix = " bin")
sol <- function(x, n) str_pad(x, n, "right")   # sprintf("%-20s") Türkçe harfleri 2 karakter sayar
nokta <- function(x, d = 0) formatC(x, format = "f", digits = d, big.mark = ".", decimal.mark = ",")

baslik <- function(m) cat("\n", strrep("=", 78), "\n", m, "\n", strrep("=", 78), "\n", sep = "")
alt_baslik <- function(m) cat("\n---", m, "---\n")
kaydet <- function(grafik, ad, genislik, yukseklik) {
  ggsave(file.path(CIKTI, ad), grafik, width = genislik, height = yukseklik, dpi = 130, bg = "white")
  cat("[grafik] ciktilar/r/", ad, "\n", sep = "")
}
ana_baslik <- function(metin) {
  plot_annotation(title = metin,
                  theme = theme(plot.title = element_text(face = "bold", size = 14, hjust = 0.5)))
}

# =============================================================================
# 1. VERİYİ TANIMA
# =============================================================================
baslik("1. VERİYİ TANIMA")

# Önce "saf" okuma: readr sütun tiplerini kendisi tahmin etsin (tip çıkarımı).
# Bu tablo yalnızca teşhis içindir: Tek bir "?" bile sütunun tamamını metin yapar,
# böylece hangi sütunlarda sayıya benzemeyen değer olduğunu görürüz.
saf <-read_csv(file.path(VERI, "musteriler_kirli.csv"), show_col_types = FALSE)
alt_baslik("readr'ın tahmin ettiği sütun tipleri")
print(sapply(saf, function(s) class(s)[1]))
cat("\nyas, gelir_aylik ve memnuniyet sayı olmalıydı ama 'character' (metin) okundu:\n")
cat("bu sütunlarda sayıya çevrilemeyen değerler var. Bu yüzden veriyi önce METİN\n")
cat("olarak okuyup her sütunu bilinçli olarak dönüştüreceğiz.\n")

# Tüm sütunları metin olarak oku; yalnızca tamamen boş hücreler NA olsun,
# boşluklar silinmesin (trim_ws = FALSE) ki sorunları görebilelim
ham <- read_csv(file.path(VERI, "musteriler_kirli.csv"),
                col_types = cols(.default = col_character()), na = "", trim_ws = FALSE)
df <- ham     # ham'a dokunmuyoruz: 8. adımdaki önce/sonra raporu için saklanır

alt_baslik("Boyut ve ilk satırlar")
cat(nrow(df), "satır,", ncol(df), "sütun\n")
print(as.data.frame(head(df, 8)))

alt_baslik("Kategorik sütunlarda kaç farklı yazım var?")
# Farklı değer sayısı (kardinalite): 6 şehir beklerken 33 görmek, yazım tutarsızlığının
# kesin işaretidir.
for (s in c("cinsiyet", "sehir", "egitim", "uyelik_tipi", "kampanya_yanit")) {
  degerler <- sort(unique(na.omit(df[[s]])))
  cat(sprintf("%s: %3d farklı değer -> %s ...\n", sol(s, 15), length(degerler),
              paste0("'", head(degerler, 8), "'", collapse = ", ")))
}

alt_baslik("Hızlı kalite kontrolleri")
# duplicated() her satır için TRUE/FALSE döndürür; sum() TRUE'ları sayar (TRUE = 1).
# Tüm satıra göre ve anahtara göre sayım arasındaki fark "yarı kopyaları" gösterir.
cat("Boş hücre sayısı (yalnızca tamamen boş olanlar):", sum(is.na(df)), "\n")
cat("Birebir aynı (mükerrer) satır sayısı          :", sum(duplicated(df)), "\n")
cat("Tekrarlanan musteri_id sayısı                 :", sum(duplicated(df$musteri_id)), "\n")

# =============================================================================
# 2. VERİ TEMİZLEME
# =============================================================================
baslik("2. VERİ TEMİZLEME")

# --- 2.1 Boşluklar ve gizli eksik değerler ------------------------------------
alt_baslik("2.1 Baş/son boşlukları silme ve gizli eksik değerleri NA yapma")
# Sıralama önemli: Önce boşluklar silinir, yoksa " ? " listedeki "?" ile eşleşmez.
# Listedeki "" de bu yüzden var: Yalnızca boşluktan oluşan hücre str_trim() sonrası "" olur.
# across(everything(), f): aynı fonksiyonu tüm sütunlara uygula (vektörel, satır döngüsü yok).
df <- df |> mutate(across(everything(), str_trim))

bos_hucre <- colSums(is.na(ham))
gizli <- colSums(sapply(df, function(s) s %in% GIZLI_EKSIK))
# if_else() iki koldan aynı tipi bekler; bu yüzden NA değil NA_character_ (metin NA).
# 0 ve 999 listede yok: 0 bazı sütunlarda gerçek değerdir; onları 2.5'te kurallarla yakalarız.
df <- df |> mutate(across(everything(), ~ if_else(.x %in% GIZLI_EKSIK, NA_character_, .x)))

eksik_tablo <- tibble(sutun = names(bos_hucre), bos_hucre = bos_hucre, gizli_eksik = gizli) |>
  mutate(toplam = bos_hucre + gizli_eksik, oran = round(100 * toplam / nrow(df), 1)) |>
  arrange(desc(toplam))
print(as.data.frame(filter(eksik_tablo, toplam > 0)))
cat("Gizli eksik değerlerle birlikte toplam eksik hücre:", sum(is.na(df)), "\n")

harita <- df |> mutate(satir = row_number()) |>
  pivot_longer(-satir, names_to = "sutun", values_to = "deger", values_transform = as.character) |>
  mutate(eksik = is.na(deger), sutun = factor(sutun, levels = names(df)))
g1 <- ggplot(harita, aes(sutun, satir, fill = eksik)) +
  geom_raster() +
  scale_fill_manual(values = c(`FALSE` = "#f1f0ec", `TRUE` = MAVI), guide = "none") +
  scale_y_reverse(expand = c(0, 0)) +
  labs(title = "Eksik değer haritası (mavi = eksik)", x = NULL, y = "Satır (kayıt) numarası") +
  theme(axis.text.x = element_text(angle = 60, hjust = 1, size = 8), panel.grid = element_blank())
cubuk <- eksik_tablo |> filter(toplam > 0) |>
  pivot_longer(c(bos_hucre, gizli_eksik), names_to = "tur", values_to = "n") |>
  mutate(sutun = factor(sutun, levels = rev(filter(eksik_tablo, toplam > 0)$sutun)),
         tur = factor(tur, levels = c("gizli_eksik", "bos_hucre"),
                      labels = c('Gizli eksik ("?", "-", "N/A", "Bilinmiyor")', "Boş hücre")))
g2 <- ggplot(cubuk, aes(100 * n / nrow(df), sutun, fill = tur)) +
  geom_col(width = 0.7, colour = "white", linewidth = 0.4) +
  geom_text(data = filter(eksik_tablo, toplam > 0), inherit.aes = FALSE,
            aes(oran + 1, sutun, label = paste0("%", oran)), hjust = 0, size = 3) +
  scale_fill_manual(values = setNames(c(MAVI, TURUNCU), levels(cubuk$tur)[2:1]),
                    breaks = levels(cubuk$tur)[2:1]) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
  labs(title = "Sütunlara göre eksik oranı", x = "Eksik oranı (%)", y = NULL, fill = NULL) +
  theme(legend.position = "inside", legend.position.inside = c(0.6, 0.15),
        panel.grid.major.y = element_blank())
kaydet(g1 + g2 + plot_layout(widths = c(1.3, 1)), "01_eksik_degerler.png", 14, 5.5)

# --- 2.2 Metin standardizasyonu ------------------------------------------------
alt_baslik("2.2 Kategorik sütunlarda yazım birliği")

# Karşılaştırma anahtarı: aksanları ve noktalamayı at, küçült, boşlukları sadeleştir.
# "İstanbul", " İSTANBUL ", "Istanbul", "i̇stanbul", "İst." -> "istanbul" / "ist"
# ICU zinciri: ayrıştır (NFD: ş -> s + çengel) -> birleşik işaretleri sil -> yeniden birleştir.
anahtar <- function(x) {
  x <- stri_trans_general(x, "NFD; [:Nonspacing Mark:] Remove; NFC")  # ş -> s, İ -> I, i̇ -> i
  x <- tolower(chartr("ı", "i", x))                                    # ı ayrıştırılamaz, elle çevrilir
  x <- str_replace_all(x, "[^[:alnum:][:space:]]", " ")                # noktalama -> boşluk (silme değil:
                                                                       # "Y.Lisans" -> "y lisans")
  str_squish(x)                                                        # baş/son + çoklu boşluk
}

# Anahtar -> standart yazım sözlüğü (adlandırılmış vektör: STANDART$sehir["ankra"] -> "Ankara").
# Neden bulanık eşleme (Levenshtein) değil? Bulanık eşleme "İst." gibi kısaltmaları ve
# "Altın" -> "Gold" gibi eş anlamlıları bulamaz, "Lise" ile "Lisans"ı yanlışlıkla
# birleştirebilir. Kategori sayısı az ve biliniyorsa elle yazılmış sözlük en güvenli ve
# denetlenebilir yöntemdir.
STANDART <- list(
  sehir = c(istanbul = "İstanbul", ist = "İstanbul", ankara = "Ankara", ankra = "Ankara",
            izmir = "İzmir", tekirdag = "Tekirdağ", bursa = "Bursa", antalya = "Antalya"),
  egitim = c(ilkokul = "İlkokul", lise = "Lise", lisans = "Lisans",
             "yuksek lisans" = "Yüksek Lisans", "y lisans" = "Yüksek Lisans", yl = "Yüksek Lisans",
             doktora = "Doktora", dr = "Doktora"),
  uyelik_tipi = c(standart = "Standart", gold = "Gold", altin = "Gold",
                  platin = "Platin", platinum = "Platin"),
  cinsiyet = c(e = "E", erkek = "E", k = "K", kadin = "K"),
  kampanya_yanit = c(evet = "Evet", e = "Evet", hayir = "Hayır", h = "Hayır")
)

sehir_once <- df$sehir
for (sutun in names(STANDART)) {
  once <- n_distinct(na.omit(df[[sutun]]))
  anahtarlar <- anahtar(df[[sutun]])
  yeni <- unname(STANDART[[sutun]][anahtarlar])    # sözlükte olmayan anahtar NA -> "tanınmayan"
  taninmayan <- unique(df[[sutun]][!is.na(anahtarlar) & is.na(yeni)])
  df[[sutun]] <- yeni
  cat(sprintf("%s: %3d farklı yazım -> %d kategori%s\n", sol(sutun, 15), once,
              n_distinct(na.omit(df[[sutun]])),
              if (length(taninmayan)) paste0("  (tanınmayan: ", paste(taninmayan, collapse = ", "), ")") else ""))
}

cat("\nÖrnek: şehir sütunundaki yazımlar ve standart karşılıkları\n")
print(as.data.frame(tibble(ham = sehir_once, standart = df$sehir) |> na.omit() |> distinct() |>
                      arrange(standart, ham) |> head(14)))

# Türkçe kurallara uygun "Baş Harf Büyük" yazımı: locale = "tr" ı/I ve i/İ ayrımını korur.
# (ICU, Türkçe için ayrı bir kelime bölücü tanımı bulamadığında zararsız bir uyarı verir.)
ad_once <- df$ad_soyad
df$ad_soyad <- suppressWarnings(
  str_to_title(str_squish(str_remove_all(df$ad_soyad, "\u0307")), locale = "tr"))
df$e_posta <- str_to_lower(df$e_posta)
degisen <- which(ad_once != df$ad_soyad)
cat(sprintf("\nad_soyad: %d kayıt düzeltildi, ör. %s\n", length(degisen),
            paste0("'", ad_once[degisen[1:3]], "' -> '", df$ad_soyad[degisen[1:3]], "'", collapse = ", ")))
cat("Not: locale belirtilmezse str_to_title('YILMAZ') -> 'Yilmaz' olur (yanlış).\n")

ham_sayim <- as.data.frame(table(sehir_once), stringsAsFactors = FALSE) |> arrange(Freq)
std_sayim <- as.data.frame(table(df$sehir), stringsAsFactors = FALSE) |> arrange(Freq)
g1 <- ggplot(ham_sayim, aes(Freq, factor(paste0("'", sehir_once, "'"), levels = paste0("'", sehir_once, "'")))) +
  geom_col(fill = GRI, width = 0.75) +
  labs(title = paste("Önce:", nrow(ham_sayim), "farklı yazım"), x = "Kayıt sayısı", y = NULL) +
  theme(panel.grid.major.y = element_blank(), axis.text.y = element_text(size = 8))
g2 <- ggplot(std_sayim, aes(Freq, factor(Var1, levels = Var1))) +
  geom_col(fill = MAVI, width = 0.6) +
  geom_text(aes(label = Freq), hjust = -0.3, size = 3.5) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(title = paste("Sonra:", nrow(std_sayim), "şehir"), x = "Kayıt sayısı", y = NULL) +
  theme(panel.grid.major.y = element_blank())
kaydet(g1 + g2 + plot_layout(widths = c(1.2, 1)) + ana_baslik("Şehir sütununun standardizasyonu"),
       "02_metin_standardizasyonu.png", 13, 7)

# --- 2.3 Veri tipi dönüşümleri ---------------------------------------------------
alt_baslik("2.3 Metin olarak saklanmış sayıları ve tarihleri dönüştürme")

yas_metin <- df$yas
# Desen: isteğe bağlı eksi (-?) + bir veya daha fazla rakam (\\d+). Eksiyi bilerek yakalıyoruz:
# "-4" sessizce 4 olmasın, -4 olarak kalsın ki 2.5'teki kural onu imkânsız değer diye yakalasın.
df$yas <-as.numeric(str_extract(df$yas, "-?\\d+"))                  # "50 yaş" -> 50
cat("yas         : '... yaş' biçimindekiler ->",
    paste0("'", yas_metin[str_detect(yas_metin, "yaş") %in% TRUE], "'", collapse = ", "),
    "| sayıya çevrilemeyen ->", yas_metin[!is.na(yas_metin) & is.na(df$yas)], "\n")

gelir_metin <- df$gelir_aylik
# "36.500 TL": nokta binlik ayırıcıdır (veride ondalık nokta yok, önceden kontrol edildi).
# fixed(".") şart: düzenli ifadede "." HERHANGİ bir karakter demektir; o zaman her şey silinirdi.
df$gelir_aylik <-as.numeric(str_trim(str_remove_all(str_remove(df$gelir_aylik, "TL"), fixed("."))))
tl_li <- which(str_detect(gelir_metin, "TL"))
cat(sprintf("gelir_aylik : %d değer 'TL' içeriyordu, ör. %s\n", length(tl_li),
            paste0("'", gelir_metin[tl_li[1:3]], "' -> ", df$gelir_aylik[tl_li[1:3]], collapse = ", ")))

df <- df |> mutate(across(c(musteri_id, gelir_yillik, memnuniyet), as.numeric))

# Üç farklı biçimi sırayla dener: 2023-05-14, 14/05/2023, 14.05.2023
# Uymayan biçim NA verir; coalesce() soldan sağa ilk NA olmayan sonucu alır (şelale mantığı).
# Biçimleri açıkça yazıyoruz, çünkü otomatik tahmin 03/08/2019'u sessizce 8 Mart sanabilir.
tarih_coz <- function(x) {
  coalesce(as.Date(x, format = "%Y-%m-%d"),
           as.Date(x, format = "%d/%m/%Y"),
           as.Date(x, format = "%d.%m.%Y"))
}
tarih_metin <- df$kayit_tarihi
df$kayit_tarihi <- tarih_coz(df$kayit_tarihi)
bicim <- case_when(str_detect(tarih_metin, "-") ~ "YYYY-AA-GG",
                   str_detect(tarih_metin, "/") ~ "GG/AA/YYYY",
                   !is.na(tarih_metin) ~ "GG.AA.YYYY")
cat("kayit_tarihi: biçim dağılımı ->", paste(names(table(bicim)), table(bicim), sep = ": ", collapse = ", "), "\n")
cat("              çözülemeyen ->", tarih_metin[!is.na(tarih_metin) & is.na(df$kayit_tarihi)], "\n")
cat("\nYeni sütun tipleri:\n")
print(sapply(df, function(s) class(s)[1]))

# --- 2.4 Mükerrer kayıtlar -------------------------------------------------------
alt_baslik("2.4 Mükerrer (tekrarlanan) kayıtlar")
cat("Ham veride birebir aynı satır      :", sum(duplicated(ham)), "\n")
cat("Standardizasyondan sonra           :", sum(duplicated(df)),
    " (yazım farkı yüzünden görünmeyen kopyalar ortaya çıktı)\n")
df <- distinct(df)

tekrar <- df |> group_by(musteri_id) |> filter(n() > 1) |> ungroup() |> arrange(musteri_id)
cat(sprintf("Silindikten sonra aynı musteri_id'ye sahip kayıt: %d (%d müşteri). Örnek:\n",
            nrow(tekrar), n_distinct(tekrar$musteri_id)))
print(as.data.frame(head(select(tekrar, musteri_id, ad_soyad, sehir, gelir_aylik, memnuniyet), 4)))

# Aynı müşterinin kayıtlarından EN EKSİKSİZ olanı tut ("hayatta kalma kuralı").
# Alternatifler: ilk kayıt (keyfi), en güncel kayıt (tarih damgası gerekir), alan alan
# birleştirme (çelişki kuralı gerekir). Kopyalar yalnızca eksiklikle ayrıştığı için
# en eksiksiz kayıt bilgi kaybı olmadan seçilir.
df <- df |>
  mutate(.eksik = rowSums(is.na(across(everything())))) |>   # satırdaki eksik hücre sayısı
  arrange(musteri_id, .eksik) |>                              # kararlı sıralama: eşitlerde sıra korunur
  distinct(musteri_id, .keep_all = TRUE) |>
  select(-.eksik)
cat(sprintf("Anahtar bazlı tekilleştirmeden sonra: %d satır, tekrarlanan musteri_id = %d\n",
            nrow(df), sum(duplicated(df$musteri_id))))

# --- 2.5 Geçersiz değerler (iş kuralları) ---------------------------------------
alt_baslik("2.5 Geçersiz / imkânsız değerler (alan bilgisine dayalı kurallar)")
# Pratik bir desen: kullanıcı adı @ alan adı . en az 2 harfli uzantı (tam standart RFC 5322
# çok daha karmaşıktır).
EPOSTA_DESENI <- "^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$"
# Her kural: açıklama = list(sütun, ihlal maskesi). Kuralları koddan ayrı bir liste olarak
# tutmak küçük bir "veri doğrulama şeması"dır: Yeni kural tek satır, alan uzmanı okuyabilir.
# "%in% TRUE" ve "& !is.na()" eksik değerin ihlal sayılmasını önler (NA %in% TRUE -> FALSE).
kurallar <- list(
  "yas 18-100 arasında olmalı"      = list("yas", !between(df$yas, 18, 100) %in% TRUE & !is.na(df$yas)),
  "gelir_aylik 0 < g < 1.000.000"   = list("gelir_aylik", !between(df$gelir_aylik, 1, 999999) & !is.na(df$gelir_aylik)),
  "gelir_yillik 0 < g < 12.000.000" = list("gelir_yillik", !between(df$gelir_yillik, 1, 11999999) & !is.na(df$gelir_yillik)),
  "memnuniyet 1-5 ölçeğinde olmalı" = list("memnuniyet", !(df$memnuniyet %in% 1:5) & !is.na(df$memnuniyet)),
  "kayit_tarihi gelecekte olamaz"   = list("kayit_tarihi", (df$kayit_tarihi > REFERANS_TARIH) %in% TRUE),
  "e_posta geçerli biçimde olmalı"  = list("e_posta", !str_detect(df$e_posta, EPOSTA_DESENI) %in% c(TRUE, NA))
)
kurallar_oncesi <- df
yazdir <- function(v) if (is.numeric(v)) format(v, scientific = FALSE, trim = TRUE) else as.character(v)
for (aciklama in names(kurallar)) {
  sutun <- kurallar[[aciklama]][[1]]
  ihlal <- kurallar[[aciklama]][[2]]
  cat(sprintf("%s: %d ihlal -> %s\n", sol(aciklama, 34), sum(ihlal),
              paste(yazdir(df[[sutun]][ihlal]), collapse = ", ")))
  df[[sutun]][ihlal] <- NA   # geçersiz değer = bilinmeyen değer; 5. adımda ele alınacak
}

set.seed(0)
gecersiz_grafik <- function(sutun, etiket, baslik_metni, olcek) {
  d <- tibble(deger = kurallar_oncesi[[sutun]], hatali = is.na(df[[sutun]])) |>
    filter(!is.na(deger)) |>
    mutate(x = 1 + runif(n(), -0.18, 0.18), durum = if_else(hatali, "Kural ihlali", "Geçerli"),
           kayma = if_else(cumsum(hatali) %% 2 == 0, 1.2, -0.6))   # yakın etiketler çakışmasın
  ggplot(d, aes(1, deger)) +
    geom_boxplot(width = 0.5, outlier.shape = NA, colour = GRI, fill = NA) +
    geom_point(data = filter(d, !hatali), aes(x, deger, colour = durum), alpha = 0.5, size = 1.4) +
    geom_point(data = filter(d, hatali), aes(x, deger, colour = durum), size = 3) +
    geom_text(data = filter(d, hatali), aes(x, deger, label = nokta(deger), vjust = kayma),
              colour = KIRMIZI, hjust = -0.25, size = 3) +
    scale_colour_manual(values = c("Geçerli" = MAVI, "Kural ihlali" = KIRMIZI), name = NULL) +
    scale_y_continuous(labels = olcek) +
    labs(title = baslik_metni, x = NULL, y = etiket) +
    theme(axis.text.x = element_blank(), panel.grid.major.x = element_blank(),
          legend.position = "inside", legend.position.inside = c(0.2, 0.92))
}
kaydet(gecersiz_grafik("yas", "Yaş", "Yaş: 250, 0, -4 ve 7 imkânsız", waiver()) +
         gecersiz_grafik("gelir_aylik", "Aylık gelir (TL)",
                         "Gelir: tek bir hatalı değer (3.500.000)\ntüm ölçeği eziyor",
                         scales::label_number(scale = 1e-6, suffix = " M", accuracy = 0.1)),
       "03_gecersiz_degerler.png", 11, 5.5)

# =============================================================================
# 3. VERİ BÜTÜNLEŞTİRME
# =============================================================================
baslik("3. VERİ BÜTÜNLEŞTİRME (sipariş sistemi ile birleştirme)")
sip <- read_csv(file.path(VERI, "siparisler.csv"), show_col_types = FALSE)
cat("siparisler.csv:", nrow(sip), "satır. İlk satırlar:\n")
print(as.data.frame(head(sip, 4)))

# Sıralama: mükerrerler ve para birimi TOPLULAŞTIRMADAN ÖNCE düzeltilmeli; toplamdan sonra
# iki kez sayılmış bir tutar ayırt edilemez, TL ile USD'yi toplamak da anlamsızdır.
alt_baslik("3.1 Sipariş verisindeki mükerrer kayıtlar")
cat("Aynı siparis_no ile iki kez aktarılmış sipariş:", sum(duplicated(sip$siparis_no)), "\n")
sip <- distinct(sip, siparis_no, .keep_all = TRUE)

alt_baslik("3.2 Değer çakışması: farklı para birimleri")
print(table(sip$para_birimi))
# Sabit kur bir basitleştirmedir; gerçek projede her sipariş, sipariş tarihindeki kurla çevrilir.
sip <- sip |> mutate(tutar_tl = if_else(para_birimi == "USD", tutar * USD_TL, tutar))
cat("USD tutarlar 1 USD =", USD_TL, "TL kabulüyle TL'ye çevrildi.\n")

alt_baslik("3.3 Varlık tanımlama: 'C-1001' (sipariş sistemi) = 1001 (CRM)")
sip <- sip |> mutate(musteri_id = as.numeric(str_remove(cust_id, "C-")))
# Ayrıntı düzeyini eşitle: sipariş başına satır -> müşteri başına satır. Toplulaştırmasaydık
# birleştirmeden sonra her müşteri sipariş sayısı kadar tekrarlanırdı.
ozet <- sip |>
  group_by(musteri_id) |>
  summarise(siparis_sayisi = n(), toplam_harcama_tl = round(sum(tutar_tl), 2))
cat("Sipariş satırları müşteri düzeyine toplulaştırıldı (aggregation):\n")
print(as.data.frame(head(ozet, 4)))

alt_baslik("3.4 Birleştirme (left join) ve eşleşmeyen kayıtlar")
yetim <- anti_join(ozet, df, by = "musteri_id")     # siparişte var, CRM'de yok
cat("CRM'de karşılığı olmayan (yetim) sipariş müşterisi:", nrow(yetim), "->", yetim$musteri_id, "\n")
# Neden left join? Analiz birimi CRM müşterisi ve hedef değişken yalnızca CRM'de var.
# inner join siparişsiz müşterileri kaybederdi; full join demografisi ve hedefi olmayan
# yetimleri getirirdi. Yetimleri tabloya almıyor, yalnızca raporluyoruz.
df <- left_join(df, ozet, by = "musteri_id")
cat("Hiç siparişi olmayan CRM müşterisi              :", sum(is.na(df$siparis_sayisi)), "\n")
df <- df |> mutate(siparis_sayisi = replace_na(siparis_sayisi, 0L),
                   toplam_harcama_tl = replace_na(toplam_harcama_tl, 0))
cat("Bu müşterilerin eksik değeri 'bilinmiyor' değil 'sıfır sipariş' demektir -> 0 ile dolduruldu.\n")

alt_baslik("3.5 Fazlalık analizi: Pearson korelasyonu")
sayisal <- c("yas", "gelir_aylik", "gelir_yillik", "memnuniyet", "siparis_sayisi", "toplam_harcama_tl")
# Pearson r = cov(X, Y) / (s_X · s_Y), -1 ile +1 arası, birimden bağımsız. Eksikler çift
# bazında atlanır. |r| ≈ 1 ise bir sütun diğerinin doğrusal fonksiyonudur (fazlalık).
# Not: r yalnızca DOĞRUSAL ilişkiyi ölçer; r ≈ 0 ilişkisizlik kanıtı değildir.
kor <- cor(df[sayisal], use = "pairwise.complete.obs")
print(round(kor, 3))
for (i in seq_along(sayisal)) for (j in seq_along(sayisal)) {
  if (i < j && abs(kor[i, j]) > 0.95)
    cat(sprintf("|r| > 0.95: %s ~ %s (r = %.3f) -> biri diğerinden türetilebilir\n",
                sayisal[i], sayisal[j], kor[i, j]))
}
cat("gelir_yillik / gelir_aylik oranı her satırda:",
    unique(na.omit(df$gelir_yillik / df$gelir_aylik)), "-> gelir_yillik sütunu silindi.\n")

kor_uzun <- as.data.frame(as.table(kor)) |>
  mutate(Var1 = factor(Var1, levels = rev(sayisal)), Var2 = factor(Var2, levels = sayisal))
g <- ggplot(kor_uzun, aes(Var2, Var1, fill = Freq)) +
  geom_tile(colour = "white") +
  geom_text(aes(label = sprintf("%.2f", Freq), colour = abs(Freq) > 0.6), size = 3.5) +
  scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = KOYU), guide = "none") +
  scale_fill_distiller(palette = "RdBu", limits = c(-1, 1), name = "Pearson r") +
  labs(title = "Korelasyon matrisi: gelir_aylik ve gelir_yillik r = 1", x = NULL, y = NULL) +
  theme(axis.text.x = element_text(angle = 40, hjust = 1), panel.grid = element_blank())
kaydet(g, "04_korelasyon.png", 7.5, 6)
df <- select(df, -gelir_yillik)

alt_baslik("3.6 Kategorik nitelikler arasında ilişki: ki-kare (χ²) testi")
for (nitelik in c("uyelik_tipi", "sehir")) {
  # Gözlenen frekansları "bağımsız olsalardı" beklenenlerle karşılaştırır:
  # χ² = Σ (G - B)² / B, sd = (satır - 1)(sütun - 1); beklenen tablo test$expected içindedir.
  # p < 0.05 -> bağımsızlık reddedilir. χ² ilişkinin VARLIĞINI söyler, gücünü değil.
  test <- chisq.test(table(df[[nitelik]], df$kampanya_yanit))
  cat(sprintf("%s x kampanya_yanit: χ² = %.2f, sd = %d, p = %.4f -> %s\n", nitelik,
              test$statistic, test$parameter, test$p.value,
              if (test$p.value < 0.05) "ilişki VAR (p < 0.05)" else "anlamlı ilişki yok"))
}
print(round(prop.table(table(df$uyelik_tipi, df$kampanya_yanit), 1), 2))

# =============================================================================
# 4. AYKIRI DEĞERLER
# =============================================================================
baslik("4. AYKIRI DEĞERLER")

# Tukey kuralı: [Q1 - 1.5·IQR, Q3 + 1.5·IQR]. 1.5 katsayısı normal dağılımda yaklaşık ±2.7σ'ya
# denk gelir (verinin ~%0.7'si dışarıda kalır). Çeyrekliklere dayandığı için sağlamdır (robust).
iqr_sinirlari <- function(x) {
  q <- quantile(x, c(0.25, 0.75), na.rm = TRUE)
  c(alt = q[[1]] - 1.5 * (q[[2]] - q[[1]]), ust = q[[2]] + 1.5 * (q[[2]] - q[[1]]), q1 = q[[1]], q3 = q[[2]])
}

for (sutun in c("gelir_aylik", "toplam_harcama_tl")) {
  x <- na.omit(df[[sutun]])
  s <- iqr_sinirlari(x)
  z <- (x - mean(x)) / sd(x)
  cat(sprintf("\n%s: Q1 = %s  Q3 = %s  IQR = %s  sınırlar = [%s ; %s]\n", sutun,
              nokta(s["q1"]), nokta(s["q3"]), nokta(s["q3"] - s["q1"]), nokta(s["alt"]), nokta(s["ust"])))
  iqr_aykiri <- x[x < s["alt"] | x > s["ust"]]
  cat(sprintf("  IQR yöntemi  : %d aykırı -> %s\n", length(iqr_aykiri),
              paste(head(sort(round(iqr_aykiri), decreasing = TRUE), 10), collapse = ", ")))
  cat(sprintf("  z-skor |z|>3 : %d aykırı -> %s\n", sum(abs(z) > 3),
              paste(sort(round(x[abs(z) > 3]), decreasing = TRUE), collapse = ", ")))
}

x_hatali <- na.omit(kurallar_oncesi$gelir_aylik)
z_hatali <- (x_hatali - mean(x_hatali)) / sd(x_hatali)
cat(sprintf("\nMaskeleme etkisi: 3.500.000 TL'lik hatalı değer silinmeseydi z-skor yalnızca %d aykırı bulurdu (ortalama %s, std %s şişerdi).\n",
            sum(abs(z_hatali) > 3), nokta(mean(x_hatali)), nokta(sd(x_hatali))))

alt_baslik("Karar")
cat("gelir_aylik      : Değerler gerçek (yüksek gelirli müşteriler), silmek bilgi kaybı olur.\n")
cat("                   IQR sınırlarına baskılandı (winsorizing / capping).\n")
cat("toplam_harcama_tl: Sağa çarpık, doğal bir dağılım -> 6. adımda log dönüşümü uygulanacak.\n")
gelir_once <- df$gelir_aylik
sinir <- iqr_sinirlari(df$gelir_aylik)
# pmax alttan, pmin üstten keser; aradakilere ve NA'lere dokunmaz. Tespitte kullandığımız
# sınırın aynısı (ör. %1-%99 yüzdelik değil): "aykırı" = "baskılanan".
# Alt sınır negatif olduğundan pratikte yalnızca üstten baskılanır.
df$gelir_aylik <-pmin(pmax(df$gelir_aylik, sinir["alt"]), sinir["ust"])
cat("Baskılanan değer sayısı:", sum(gelir_once != df$gelir_aylik, na.rm = TRUE), "\n")

aykiri_d <- bind_rows(tibble(gelir = gelir_once, panel = "Önce"),
                      tibble(gelir = df$gelir_aylik, panel = "Sonra (baskılama)")) |>
  filter(!is.na(gelir)) |>
  mutate(durum = if_else(gelir > sinir["ust"] + 1e-9, "IQR sınırı dışında", "Sınırlar içinde"),
         panel = factor(panel, levels = c("Önce", "Sonra (baskılama)")))
g <- ggplot(aykiri_d, aes(gelir, fill = durum)) +
  geom_histogram(breaks = seq(0, 260000, 5000), colour = "white", linewidth = 0.3) +
  geom_vline(xintercept = sinir["ust"], linetype = "dashed", colour = KOYU) +
  annotate("text", x = sinir["ust"] + 3000, y = Inf, vjust = 1.5, hjust = 0, size = 3,
           label = paste0("Q3 + 1.5·IQR\n= ", nokta(sinir["ust"]), " TL")) +
  facet_wrap(~panel) +
  scale_fill_manual(values = c("Sınırlar içinde" = MAVI, "IQR sınırı dışında" = KIRMIZI), name = NULL) +
  scale_x_continuous(labels = bin_tl) +
  labs(x = "Aylık gelir (TL)", y = "Müşteri sayısı",
       title = "Aykırı gelir değerlerinin IQR sınırına baskılanması") +
  theme(plot.title = element_text(size = 14), strip.text = element_text(face = "bold", size = 12),
        legend.position = "inside", legend.position.inside = c(0.35, 0.6))
kaydet(g, "05_aykiri_degerler.png", 13, 4.8)

# =============================================================================
# 5. EKSİK DEĞERLER
# =============================================================================
baslik("5. EKSİK DEĞERLER")
cat("Şu anki eksik değer sayıları:\n")
eksikler <- colSums(is.na(df))
print(eksikler[eksikler > 0])

alt_baslik("5.1 Çoğunlukla boş sütunları silme (eşik %60)")
# colMeans(is.na()): TRUE = 1 olduğundan ortalama doğrudan eksik ORANIDIR.
# Önce sütun, sonra satır: %85'i boş sütun kalsaydı her satırın eksik oranını yapay olarak
# artırır, gereksiz satır silinmesine yol açardı. Eşikler (%60, %50) pratik seçimlerdir.
oranlar <- colMeans(is.na(df))
silinecek <- names(oranlar)[oranlar > 0.60]
cat("Silinen sütun(lar):", silinecek, "(eksik oranı:", paste0("%", round(100 * oranlar[silinecek])), ")\n")
df <- select(df, -all_of(silinecek))

alt_baslik("5.2 Çoğunlukla boş satırları silme (eşik %50)")
satir_oran <- rowMeans(is.na(df))
cat("Değerlerinin yarısından fazlası eksik satır:", sum(satir_oran > 0.5), "->",
    df$musteri_id[satir_oran > 0.5], "\n")
df <- df[satir_oran <= 0.5, ]

alt_baslik("5.3 Hedef değişkeni (kampanya_yanit) eksik satırları silme")
cat("Hedefi eksik satır:", sum(is.na(df$kampanya_yanit)),
    "(hedefi tahmin etmeyiz, öğrenmek için kullanırız)\n")
df <- filter(df, !is.na(kampanya_yanit))

alt_baslik("5.4 Eksiklik rastgele mi? (gelir_aylik)")
EGITIM_SIRA <- c("İlkokul" = 0, "Lise" = 1, "Lisans" = 2, "Yüksek Lisans" = 3, "Doktora" = 4)
UYELIK_SIRA <- c("Standart" = 0, "Gold" = 1, "Platin" = 2)
# Eksiklik tamamen rastgele (MCAR) olsaydı geliri eksik olanların eğitim dağılımı tüm
# verininkine benzerdi; belirgin fark, eksikliğin eğitime bağlı (MAR) olduğunu gösterir.
egitim_f <- factor(df$egitim, levels = names(EGITIM_SIRA))
print(round(cbind(geliri_eksik = prop.table(table(egitim_f[is.na(df$gelir_aylik)])),
                  tum_veri = prop.table(table(egitim_f))), 2))
grup_medyan <- tapply(df$gelir_aylik, df$egitim, median, na.rm = TRUE)
beklenen <- mean(grup_medyan[df$egitim[is.na(df$gelir_aylik)]], na.rm = TRUE)
cat("Geliri eksik olanların eğitim dağılımı tüm veriden farklı: eksiklik eğitime bağlı (MAR).\n")
cat(sprintf("Eğitim gruplarına göre beklenen gelirleri ort. %s TL, genel ortalama ise %s TL.\n",
            nokta(beklenen), nokta(mean(df$gelir_aylik, na.rm = TRUE))))
cat("Genel ortalamayla doldurmak bu kişilerin gelirini olduğundan yüksek gösterir.\n")

alt_baslik("5.5 Kategorik sütunlar: mod (en sık değer) ile doldurma")
# Nominal nitelikte ortalama/medyan tanımsızdır, mod tek seçenektir. R'da hazır bir mod
# fonksiyonu yok: frekans tablosunun en büyük elemanının adını alıyoruz.
mod_bul <- function(x) names(which.max(table(x)))
for (s in c("cinsiyet", "sehir", "egitim")) {
  m <- mod_bul(df[[s]])
  cat(sprintf("%s: %d eksik -> '%s'\n", sol(s, 10), sum(is.na(df[[s]])), m))
  df[[s]] <- replace_na(df[[s]], m)
}

alt_baslik("5.6 gelir_aylik için doldurma yöntemlerinin karşılaştırılması")
eksik_gelir <- is.na(df$gelir_aylik)
# Dört yöntem aynı eksik veriden ayrı ayrı hesaplanır, tabloya henüz yazılmaz; adil
# karşılaştırmadan sonra seçilen yöntem tek satırla uygulanır (aşağıda).
# group_by + mutate tabloyu küçültmez (summarise'ın aksine): her satıra kendi grubunun
# medyanını yazar.
yontemler <- list(
  "Ortalama" = replace_na(df$gelir_aylik, mean(df$gelir_aylik, na.rm = TRUE)),
  "Medyan" = replace_na(df$gelir_aylik, median(df$gelir_aylik, na.rm = TRUE)),
  "Eğitim grubunun medyanı" = df |> group_by(egitim) |>
    mutate(g = replace_na(gelir_aylik, median(gelir_aylik, na.rm = TRUE))) |> pull(g)
)
# k-NN: benzer müşterilerin (yaş, eğitim, üyelik, harcama) gelir ortalaması.
# VIM::kNN, Gower uzaklığı kullandığı için ölçeklemeyi kendisi yapar.
knn_girdi <- data.frame(yas = df$yas, egitim = unname(EGITIM_SIRA[df$egitim]),
                        uyelik = unname(UYELIK_SIRA[df$uyelik_tipi]),
                        harcama = df$toplam_harcama_tl, gelir = df$gelir_aylik)
invisible(capture.output(   # VIM::kNN konsola min/maks tablosu basar; susturuyoruz
  knn <- VIM::kNN(knn_girdi, variable = "gelir", k = 5, dist_var = c("yas", "egitim", "uyelik", "harcama"),
                  numFun = mean, imp_var = FALSE)))
yontemler[["k-NN (k = 5)"]] <- knn$gelir

cat("Eksik gelir sayısı:", sum(eksik_gelir), "\n")
cat(sprintf("%s %10s %10s %28s\n", sol("Yöntem", 26), "ortalama", "std", "doldurulan değerlerin ort."))
cat(sprintf("%s %10s %10s\n", sol("(Gözlenen değerler)", 26), nokta(mean(df$gelir_aylik, na.rm = TRUE)),
            nokta(sd(df$gelir_aylik, na.rm = TRUE))))
for (ad in names(yontemler)) {
  v <- yontemler[[ad]]
  cat(sprintf("%s %10s %10s %28s\n", sol(ad, 26), nokta(mean(v)), nokta(sd(v)), nokta(mean(v[eksik_gelir]))))
}
cat("Ortalama/medyan ile doldurma tüm eksiklere AYNI değeri verir: varyans yapay olarak düşer.\n")
cat("Seçilen yöntem: eğitim grubunun medyanı (sınıf bazında doldurma).\n")
# Neden? MAR yapısını hesaba katar, basit ve açıklanabilirdir. Hepsi "tekli atama"dır:
# doldurulan değerin belirsizliğini gizler; ileri yöntem çoklu atamadır (ör. mice paketi).

doldurma_d <- bind_rows(lapply(names(yontemler), function(ad)
  tibble(gelir = yontemler[[ad]], yontem = sprintf("%s  (std = %s)", ad, nokta(sd(yontemler[[ad]]))),
         durum = if_else(eksik_gelir, "Doldurulan", "Gözlenen")))) |>
  mutate(yontem = factor(yontem, levels = unique(yontem)),
         durum = factor(durum, levels = c("Doldurulan", "Gözlenen")))
g <- ggplot(doldurma_d, aes(gelir, fill = durum)) +
  geom_histogram(breaks = seq(0, 80000, 2500), colour = "white", linewidth = 0.3, position = "stack") +
  facet_wrap(~yontem, ncol = 2) +
  scale_fill_manual(values = c("Gözlenen" = MAVI, "Doldurulan" = TURUNCU), breaks = c("Gözlenen", "Doldurulan"),
                    name = NULL) +
  scale_x_continuous(labels = bin_tl) +
  labs(title = "Eksik gelir değerlerini doldurma yöntemleri", x = "Aylık gelir (TL)", y = "Müşteri sayısı") +
  theme(plot.title = element_text(size = 14), strip.text = element_text(face = "bold", size = 12),
        legend.position = "top")
kaydet(g, "06_eksik_doldurma.png", 13, 7.5)

df$gelir_aylik <- yontemler[["Eğitim grubunun medyanı"]]

alt_baslik("5.7 Diğer sayısal sütunlar")
cat(sprintf("yas         : %d eksik -> medyan = %.0f\n", sum(is.na(df$yas)), median(df$yas, na.rm = TRUE)))
df$yas <- replace_na(df$yas, median(df$yas, na.rm = TRUE))
cat(sprintf("memnuniyet  : %d eksik -> medyan = %.0f (sıralı ölçek: ortalama 3.6 gibi ara değer anlamsız)\n",
            sum(is.na(df$memnuniyet)), median(df$memnuniyet, na.rm = TRUE)))
df$memnuniyet <- replace_na(df$memnuniyet, median(df$memnuniyet, na.rm = TRUE))
medyan_tarih <- as.Date(floor(as.numeric(median(df$kayit_tarihi, na.rm = TRUE))))
cat(sprintf("kayit_tarihi: %d eksik -> medyan tarih = %s\n", sum(is.na(df$kayit_tarihi)), medyan_tarih))
df$kayit_tarihi <- replace_na(df$kayit_tarihi, medyan_tarih)
cat(sprintf("e_posta     : %d eksik -> DOLDURULMADI (iletişim bilgisi tahmin edilemez, modelde kullanılmayacak)\n",
            sum(is.na(df$e_posta))))

alt_baslik("Kalan eksik değerler")
eksikler <- colSums(is.na(df))
print(eksikler[eksikler > 0])

# =============================================================================
# 6. VERİ DÖNÜŞTÜRME
# =============================================================================
baslik("6. VERİ DÖNÜŞTÜRME")
temiz <- df     # okunabilir, temizlenmiş tablo (kodlanmamış hâli) ayrıca kaydedilecek

alt_baslik("6.1 Özellik türetme (feature construction)")
# İki tarihin farkı gün cinsinden bir süredir; 365.25: artık yılların ortalaması.
# Sıfıra bölme: 0/0 = NaN, x/0 = Inf; siparişi olmayanlara doğrudan 0 yazıyoruz.
# Bu türetilmiş nitelikler pazarlamadaki RFM (Recency, Frequency, Monetary) fikrine dayanır.
df <- df |> mutate(
  uyelik_suresi_yil = round(as.numeric(REFERANS_TARIH - kayit_tarihi) / 365.25, 2),
  ort_siparis_tl = if_else(siparis_sayisi > 0, round(toplam_harcama_tl / pmax(siparis_sayisi, 1), 2), 0)
)
print(as.data.frame(head(select(df, musteri_id, kayit_tarihi, uyelik_suresi_yil, siparis_sayisi,
                                toplam_harcama_tl, ort_siparis_tl), 5)))

# Çarpıklık: 3. standart moment. 0 simetrik, > 0 sağa çarpık; |g| > 1 güçlü çarpık.
carpiklik <- function(x)mean((x - mean(x))^3) / mean((x - mean(x))^2)^1.5

alt_baslik("6.2 Log dönüşümü (sağa çarpık dağılımlar için)")
# Log çarpımsal farkları toplamsala çevirir (1.000 -> 10.000 ile 10.000 -> 100.000 aynı uzaklık).
# Alternatifler: karekök (daha hafif), Box-Cox / Yeo-Johnson (üssü veriden tahmin eder).
df$log_harcama <- round(log1p(df$toplam_harcama_tl), 4)       # log(1 + x): sıfırlar için güvenli
pozitif <- df$toplam_harcama_tl > 0
cark_once <- carpiklik(df$toplam_harcama_tl[pozitif])
cark_sonra <- carpiklik(df$log_harcama[pozitif])
cat(sprintf("Siparişi olan müşterilerde çarpıklık: %.2f -> log1p sonrası %.2f\n", cark_once, cark_sonra))
cat(sprintf("Dikkat: %d müşterinin harcaması 0; log1p(0) = 0 olduğu için bunlar ayrı bir\n", sum(!pozitif)))
cat("yığın oluşturur. Çarpıklık ölçüsü bu yığından çok etkilenir, bu yüzden pozitifler üzerinden raporlandı.\n")

g1 <- ggplot(df, aes(toplam_harcama_tl)) +
  geom_histogram(bins = 30, fill = MAVI, colour = "white") +
  scale_x_continuous(labels = bin_tl) +
  labs(title = sprintf("Ham harcama (çarpıklık* = %.2f)", cark_once), x = "Toplam harcama (TL)",
       y = "Müşteri sayısı")
g2 <- ggplot(df, aes(log_harcama)) +
  geom_histogram(bins = 30, fill = YESIL, colour = "white") +
  annotate("text", x = 1.5, y = sum(!pozitif) + 12, hjust = 0, size = 3,
           label = "Hiç siparişi olmayanlar\n(log(1 + 0) = 0)") +
  annotate("segment", x = 1.5, xend = 0.3, y = sum(!pozitif) + 10, yend = sum(!pozitif),
           colour = GRI, arrow = arrow(length = unit(0.15, "cm"))) +
  labs(title = sprintf("log(1 + harcama) (çarpıklık* = %.2f)", cark_sonra),
       x = "log(1 + toplam harcama)", y = NULL)
kaydet(g1 + g2 + ana_baslik("Log dönüşümü sağa çarpık dağılımı simetrikleştirir") +
         plot_annotation(caption = "* Çarpıklık yalnızca siparişi olan müşteriler üzerinden hesaplandı."),
       "07_log_donusumu.png", 13, 4.8)

alt_baslik("6.3 Normalizasyon: min-maks ve z-skor")
# İkisi de dağılımın BİÇİMİNİ değiştirmez, yalnızca ekseni kaydırıp gerer.
# min-maks: [0, 1], sınırlı aralık gerektiğinde; tek bir uç değer herkesi sıkıştırır.
# z-skor (scale): ort. 0, std 1; PCA, doğrusal modeller, kümeleme için standart seçim.
min_maks <- function(x) (x - min(x)) / (max(x) - min(x))
ornek <- tibble(ham_yas = df$yas, ham_gelir_aylik = df$gelir_aylik,
                minmaks_yas = min_maks(df$yas), minmaks_gelir_aylik = min_maks(df$gelir_aylik),
                z_yas = as.numeric(scale(df$yas)), z_gelir_aylik = as.numeric(scale(df$gelir_aylik)))
print(as.data.frame(mutate(head(ornek, 5), across(starts_with(c("minmaks", "z_")), ~ round(.x, 3)))))
cat(sprintf("min-maks aralığı: [%.0f, %.0f]   z-skor: ortalama ≈ %.0f, std = %.0f\n",
            min(ornek$minmaks_yas), max(ornek$minmaks_gelir_aylik), abs(mean(ornek$z_yas)), sd(ornek$z_yas)))

olcek_d <- bind_rows(
  tibble(panel = "Ham değerler", nitelik = "yas", deger = ornek$ham_yas),
  tibble(panel = "Ham değerler", nitelik = "gelir_aylik", deger = ornek$ham_gelir_aylik),
  tibble(panel = "Min-maks [0, 1]", nitelik = "yas", deger = ornek$minmaks_yas),
  tibble(panel = "Min-maks [0, 1]", nitelik = "gelir_aylik", deger = ornek$minmaks_gelir_aylik),
  tibble(panel = "z-skor (ort. 0, std 1)", nitelik = "yas", deger = ornek$z_yas),
  tibble(panel = "z-skor (ort. 0, std 1)", nitelik = "gelir_aylik", deger = ornek$z_gelir_aylik)
) |> mutate(nitelik = factor(nitelik, levels = c("yas", "gelir_aylik")),
            panel = factor(panel, levels = unique(panel)))
g <- ggplot(olcek_d, aes(nitelik, deger)) +
  geom_boxplot(width = 0.55, fill = "#dbe8f8", colour = MAVI, outlier.colour = TURUNCU) +
  facet_wrap(~panel, scales = "free_y") +
  labs(title = "Ölçekleme: farklı birimlerdeki nitelikleri karşılaştırılabilir kılar", x = NULL, y = NULL) +
  theme(plot.title = element_text(size = 14), strip.text = element_text(face = "bold", size = 12),
        panel.grid.major.x = element_blank())
kaydet(g, "08_olcekleme.png", 14, 4.5)

alt_baslik("6.4 Ayrıklaştırma: yaşı aralıklara bölme")
df <- df |> mutate(
  yas_esit_genislik = cut(yas, breaks = 4),                       # min-maks arası 4 eşit uzunlukta aralık
  yas_esit_frekans = cut(yas, breaks = quantile(yas, probs = seq(0, 1, 0.25)),
                         include.lowest = TRUE),                  # çeyrekliklerde böl: kovalarda benzer sayı
  # Alan bilgisiyle: aralıklar (17, 29] biçimindedir (sol açık, sağ kapalı); 18'in "Genç"e
  # girmesi için ilk sınır 17.
  yas_grubu =cut(yas, breaks = c(17, 29, 49, 100), labels = c("Genç", "Orta yaş", "Olgun"))
)
for (s in c("yas_esit_genislik", "yas_esit_frekans", "yas_grubu")) {
  cat(s, ":\n", sep = "")
  print(table(df[[s]]))
  cat("\n")
}
medyan_yas <- median(df$yas)
cat(sprintf("Eşit frekansta kovalar tam eşit değil: %d müşterinin yaşı tam %.0f (çoğu medyanla doldurulanlar); aynı değer iki kovaya bölünemez.\n",
            sum(df$yas == medyan_yas), medyan_yas))

kova_grafik <- function(s, baslik_metni, renk) {
  ggplot(as.data.frame(table(df[[s]])), aes(Var1, Freq)) +
    geom_col(fill = renk, width = 0.7) +
    geom_text(aes(label = Freq), vjust = -0.4, size = 3.5) +
    labs(title = baslik_metni, x = "Yaş aralığı", y = "Müşteri sayısı") +
    theme(panel.grid.major.x = element_blank())
}
kaydet(kova_grafik("yas_esit_genislik", "Eşit genişlik: aralıklar aynı boyda", MAVI) +
         kova_grafik("yas_esit_frekans", "Eşit frekans: kovalarda benzer sayıda kayıt", YESIL) +
         plot_layout(axes = "collect") + ana_baslik("Ayrıklaştırma: yaş niteliğini 4 kovaya bölme"),
       "09_ayriklastirma.png", 13, 4.4)

alt_baslik("6.5 Kategorik nitelikleri kodlama")
df <- df |> mutate(
  egitim_kod = unname(EGITIM_SIRA[egitim]),          # sıralı (ordinal) kodlama
  uyelik_kod = unname(UYELIK_SIRA[uyelik_tipi]),     # sıralı: Standart < Gold < Platin
  cinsiyet_K = as.integer(cinsiyet == "K"),          # ikili (binary) kodlama
  kampanya_yanit = as.integer(kampanya_yanit == "Evet")
)
# Şehre sıralı kod verilseydi model "İstanbul = 4 × Ankara" gibi anlamsız bir sıra öğrenirdi.
# Altı sütunun toplamı her satırda 1'dir (kukla değişken tuzağı); doğrusal modellerde bir
# sütun atılır. Okunabilirlik için hepsini tutuyoruz.
sehir_duzeyleri <- sort(unique(df$sehir), method = "radix")   # Python ile aynı sıra (Unicode)
for (d in sehir_duzeyleri) df[[paste0("sehir_", d)]] <- as.integer(df$sehir == d)   # one-hot (nominal)
sehir_sutunlari <- paste0("sehir_", sehir_duzeyleri)
cat("egitim  ->", paste(names(EGITIM_SIRA), EGITIM_SIRA, sep = ": ", collapse = ", "), "\n")
cat("uyelik  ->", paste(names(UYELIK_SIRA), UYELIK_SIRA, sep = ": ", collapse = ", "), "\n")
cat("One-hot kodlanmış şehir sütunları:", sehir_sutunlari, "\n")
print(as.data.frame(head(df[c("sehir", sehir_sutunlari)], 4)))

# =============================================================================
# 7. VERİ İNDİRGEME
# =============================================================================
baslik("7. VERİ İNDİRGEME")

alt_baslik("7.1 Bilgi taşımayan sütunlar")
# Tek değerli sütun hiçbir kaydı diğerinden ayıramaz (varyans = entropi = 0). Sütun adı
# yazmak yerine kural tanımladığımız için yeni bir sabit sütun da kendiliğinden yakalanır.
sabit <- names(df)[sapply(df, n_distinct) == 1]
cat("Tek bir değer alan (sabit) sütunlar:", sabit, "-> silindi\n")
df <- select(df, -all_of(sabit))
cat("Kimlik/iletişim sütunları (musteri_id, ad_soyad, e_posta) model matrisine alınmaz.\n")

alt_baslik("7.2 Model için hazır tablo")
OZELLIKLER <- c("yas", "gelir_aylik", "memnuniyet", "uyelik_suresi_yil", "siparis_sayisi", "log_harcama")
model <- df |>
  transmute(musteri_id, across(all_of(OZELLIKLER), ~ round(as.numeric(scale(.x)), 4)),
            egitim_kod, uyelik_kod, cinsiyet_K, across(all_of(sehir_sutunlari)), kampanya_yanit)
cat(nrow(model), "satır,", ncol(model), "sütun\n")
print(as.data.frame(head(model, 3)))

alt_baslik("7.3 Temel Bileşenler Analizi (PCA)")
# prcomp TÜM bileşenleri hesaplar; önce hepsini görüp sonra karar veririz. Bileşenler,
# varyansın en büyük ve birbirine dik yönleridir (kovaryans matrisinin özvektörleri). Girdi
# z-skorla ölçeklendi (7.2); yoksa varyansı milyonlarca olan gelir PC1'i tek başına ele geçirirdi.
pca <- prcomp(model[OZELLIKLER])        # nitelikler zaten standartlaştırıldı
aciklanan <- pca$sdev^2 / sum(pca$sdev^2)      # özdeğer = sdev²; her özdeğer / toplam
kumulatif <- cumsum(aciklanan)
for (i in seq_along(aciklanan))
  cat(sprintf("PC%d: açıklanan varyans %%%5.1f   kümülatif %%%5.1f\n", i, 100 * aciklanan[i], 100 * kumulatif[i]))
gerekli <- which(kumulatif >= 0.90)[1]
cat(sprintf("Varyansın %%90'ı için %d bileşen gerekiyor (%d nitelik -> %d bileşen).\n",
            gerekli, length(OZELLIKLER), gerekli))
cat("Nitelikler birbiriyle zayıf ilişkili olduğundan PCA burada boyutu fazla azaltamıyor;\n")
cat("PCA, güçlü korelasyonlu nitelikler (ör. siparis_sayisi ~ log_harcama) olduğunda daha etkilidir.\n")
cat("PC1 ve PC2 yükleri (işaretler yazılıma göre ters çıkabilir):\n")
print(round(pca$rotation[, 1:2], 3))

scree <- tibble(pc = factor(paste0("PC", seq_along(aciklanan)), levels = paste0("PC", seq_along(aciklanan))),
                tek = 100 * aciklanan, kum = 100 * kumulatif)
g1 <- ggplot(scree, aes(pc)) +
  geom_col(aes(y = tek, fill = "Bileşen başına"), width = 0.6) +
  geom_line(aes(y = kum, group = 1, colour = "Kümülatif"), linewidth = 1) +
  geom_point(aes(y = kum, colour = "Kümülatif"), size = 3) +
  geom_hline(yintercept = 90, linetype = "dashed", colour = GRI) +
  annotate("text", x = 0.6, y = 92.5, label = "%90", colour = GRI, size = 3, hjust = 0) +
  scale_fill_manual(values = MAVI, name = NULL) +
  scale_colour_manual(values = TURUNCU, name = NULL) +
  coord_cartesian(ylim = c(0, 102)) +
  labs(title = "Açıklanan varyans (scree grafiği)", x = NULL, y = "Açıklanan varyans (%)") +
  theme(legend.position = "inside", legend.position.inside = c(0.8, 0.45),
        panel.grid.major.x = element_blank())
skor <- tibble(PC1 = pca$x[, 1], PC2 = pca$x[, 2],
               yanit = factor(if_else(model$kampanya_yanit == 1, "Kampanyaya yanıt: Evet", "Kampanyaya yanıt: Hayır"),
                              levels = c("Kampanyaya yanıt: Hayır", "Kampanyaya yanıt: Evet")))
g2 <- ggplot(skor, aes(PC1, PC2, colour = yanit)) +
  geom_point(size = 1.8, alpha = 0.75) +
  scale_colour_manual(values = c(MAVI, TURUNCU), name = NULL) +
  labs(title = "Müşteriler ilk iki bileşen düzleminde",
       x = sprintf("PC1 (%%%.1f)", 100 * aciklanan[1]), y = sprintf("PC2 (%%%.1f)", 100 * aciklanan[2])) +
  theme(legend.position = "bottom")
kaydet(g1 + g2 + ana_baslik(sprintf("PCA: %d sayısal nitelik", length(OZELLIKLER))), "10_pca.png", 13, 5)

alt_baslik("7.4 Örnekleme: basit rastgele ve tabakalı (%30)")
# Tek bir örnek şanslı/şanssız çıkabilir; 1000 tekrar, yöntemin örnekleme dağılımını gösterir.
# set.seed (tohum) "rastgele" örneği tekrar üretilebilir kılar.
# Tabakalı: group_by(hedef) ile her sınıftan AYRI AYRI %30 çekilir, sınıf oranı korunur.
set.seed(1)
basit_oranlar <- replicate(1000, mean(slice_sample(model, prop = 0.30)$kampanya_yanit))
tabakali <- model |> group_by(kampanya_yanit) |> slice_sample(prop = 0.30) |> ungroup()
cat(sprintf("Tüm verideki 'Evet' oranı      : %.3f\n", mean(model$kampanya_yanit)))
cat(sprintf("Tabakalı örnek (n = %d)        : %.3f\n", nrow(tabakali), mean(tabakali$kampanya_yanit)))
cat(sprintf("1000 basit rastgele örnek (n = %d): en düşük %.3f, en yüksek %.3f, std %.3f\n",
            floor(0.3 * nrow(model)), min(basit_oranlar), max(basit_oranlar), sd(basit_oranlar)))
cat("Tabakalı örnekleme sınıf oranını her seferinde korur; basit örnekte oran şansa bağlı oynar.\n")

# =============================================================================
# 8. KAYDETME VE KALİTE RAPORU
# =============================================================================
baslik("8. KAYDETME VE KALİTE RAPORU")
temiz <- temiz |> select(-any_of("ulke")) |> mutate(gelir_aylik = round(gelir_aylik, 2))
write_csv(temiz, file.path(CIKTI, "musteriler_temiz.csv"), na = "")
write_csv(model, file.path(CIKTI, "musteriler_model.csv"), na = "")
cat("Kaydedildi: ciktilar/r/musteriler_temiz.csv (okunabilir, temizlenmiş tablo)\n")
cat("Kaydedildi: ciktilar/r/musteriler_model.csv (kodlanmış + ölçeklenmiş, modele hazır)\n\n")

rapor <- data.frame(
  `Ham veri` = c(nrow(ham), ncol(ham), sum(is.na(ham)) + sum(gizli), sum(duplicated(ham)),
                 sum(duplicated(ham$musteri_id)), n_distinct(na.omit(ham$sehir))),
  `Temiz veri` = c(nrow(temiz), ncol(temiz), sum(is.na(temiz)), sum(duplicated(temiz)),
                   sum(duplicated(temiz$musteri_id)), n_distinct(temiz$sehir)),
  row.names = c("Satır", "Sütun", "Eksik hücre (gizli eksikler dahil)", "Birebir mükerrer satır",
                "Tekrarlanan musteri_id", "Farklı şehir yazımı"),
  check.names = FALSE
)
print(rapor)
cat("Temiz veride kalan eksikler yalnızca e_posta sütunundadır (bilinçli olarak doldurulmadı).\n")
