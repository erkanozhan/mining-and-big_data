// Web sürümünün (index.html) ve yazdırma sayfasının (yazdir.html) ortak docsify ayarları.
// yazdir.html bu dosyadan önce window.NOT_YAZDIR = true tanımlar.
(function () {
  var YAZDIR = !!window.NOT_YAZDIR;
  var DEPO = 'https://github.com/erkanozhan/mining-and-big_data';

  // Bir not dosyasındaki göreli yolu (ör. "../images/x.svg") deponun kök klasörüne göre yola çevirir.
  function kokYolu(dosya, hedef) {
    var parcalar = [];
    ((dosya || '').replace(/[^\/]*$/, '') + hedef).split('/').forEach(function (p) {
      if (p === '..') parcalar.pop(); else if (p && p !== '.') parcalar.push(p);
    });
    return parcalar.join('/') + (/\/$/.test(hedef) ? '/' : '');
  }

  // Markdown bağlantı ve görsellerinin göreli hedeflerini sırayla işler.
  function goreliHedefler(md, islev) {
    return md.replace(/(!?)\[([^\]\n]*)\]\(([^)\s]+)\)/g, function (tum, resim, metin, hedef) {
      if (/^(https?:|mailto:|#|\/)/.test(hedef)) return tum;
      var yeni = islev(hedef, !!resim);
      return yeni == null ? tum : resim + '[' + metin + '](' + yeni + ')';
    });
  }

  // Kod, veri ve çıktı dosyalarına (.py, .csv, .txt ...) ya da klasörlere verilen bağlantılar sitede
  // bir not sayfası gibi açılamaz; bunlar GitHub'daki dosyaya veya klasöre yönlendirilir.
  function depoBaglantilari(md, dosya) {
    return goreliHedefler(md, function (hedef, resim) {
      if (resim) return null;
      if (/\.md(#|$)/.test(hedef)) {
        // docsify, ana sayfa dosyasının adını taşıyan bağlantıyı README'ye çevirir; bu yüzden kökten yazılır
        var capa = (hedef.match(/#.*$/) || [''])[0];
        return kokYolu(dosya, hedef.replace(/#.*$/, '')) === 'ders_notu.md' ? '/ders_notu.md' + capa : null;
      }
      var yol = kokYolu(dosya, hedef.replace(/#.*$/, ''));
      return DEPO + (/\/$/.test(yol) || yol === '' ? '/tree/main/' : '/blob/main/') + yol.replace(/\/$/, '');
    });
  }

  // GitHub, rakamla başlayan başlıklara "5-kurulum" biçiminde adres verir; docsify ise "_5-kurulum".
  // Not dosyalarındaki bu tür başlık bağlantıları sitede docsify'ın biçimine çevrilir.
  function capalar(md) {
    return md.replace(/\]\(([^)\s#]*)#(\d)/g, ']($1#_$2');
  }

  // GitHub'ın satır içi formül yazımı $`...`$ biçimindedir; sitede düz $...$ olarak çizilir.
  function githubFormulleri(md) {
    return md.replace(/\$`([^`\n]+?)`\$/g, function (_, formul) { return '$' + formul + '$'; });
  }

  // Bir not dosyasına sitede uygulanan tüm dönüşümler
  function notuDuzenle(md, dosya) {
    return githubFormulleri(capalar(depoBaglantilari(md, dosya)));
  }

  // Formül eklentisinden ÖNCE çalışması gerektiği için index.html bu eklentiyi, formül betiği
  // yüklendikten sonra listenin başına ekler. yazdir.html ise her bölüme notuDuzenle'yi kendisi uygular.
  function notDuzenleEklentisi(hook, vm) {
    hook.beforeEach(function (md) {
      return notuDuzenle(md, (vm.route && vm.route.file) || '');
    });
    // Sayfa içi başlık bağlantısı hâlâ bir başlığa denk gelmiyorsa (docsify başlık adresini GitHub'dan farklı
    // üretebilir: kesme işareti, büyük harf, "↔" gibi işaretler) harf ve rakamları bağlantıyla aynı olan başlık aranır.
    hook.doneEach(function () {
      // büyük/küçük harf, aksan ve ı/i farkı gözetilmez (GitHub "I" harfini "i" yapar)
      var sade = function (s) { return s.toLowerCase().normalize('NFD').replace(/[^\p{L}\p{N}]/gu, '').replace(/ı/g, 'i'); };
      var basliklar = Array.prototype.slice.call(document.querySelectorAll('.markdown-section h1, .markdown-section h2, .markdown-section h3, .markdown-section h4'))
        .map(function (h) { return { id: h.id, metin: sade(h.textContent) }; });
      Array.prototype.forEach.call(document.querySelectorAll('.markdown-section a[href*="?id="]'), function (a) {
        var m = a.getAttribute('href').match(/^(#\/[^?]*)\?id=(.*)$/);
        if (!m || m[1] !== '#' + vm.route.path) return; // yalnızca aynı sayfadaki bağlantılar
        var id = decodeURIComponent(m[2]);
        if (document.getElementById(id)) return;
        var aranan = sade(id);
        var bulunan = basliklar.filter(function (h) { return h.id && h.metin === aranan; })[0];
        if (bulunan) a.setAttribute('href', m[1] + '?id=' + encodeURIComponent(bulunan.id));
      });
      // Başka bir sayfadan başlık adresiyle gelindiyse ve docsify o başlığı bulamadıysa, metne göre bulup kaydır
      var istenen = vm.route.query && vm.route.query.id;
      if (istenen && !document.getElementById(istenen)) {
        var hedef = basliklar.filter(function (h) { return h.id && h.metin === sade(istenen); })[0];
        if (hedef) setTimeout(function () { document.getElementById(hedef.id).scrollIntoView(); }, 0);
      }
    });
  }

  // GitHub uyarı kutularını (> [!CAUTION] vb.) docsify'da da renkli göster
  function uyariKutulari(hook) {
    var basliklar = { NOTE: 'Not', TIP: 'İpucu', IMPORTANT: 'Önemli', WARNING: 'Uyarı', CAUTION: 'Dikkat' };
    hook.afterEach(function (html) {
      return html.replace(/<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(<br\s*\/?>)?/g, function (_, tur) {
        return '<blockquote class="uyari uyari-' + tur.toLowerCase() + '"><p><span class="uyari-baslik">' + basliklar[tur] + '</span>';
      });
    });
  }

  // yazdir.html de aynı dönüşümleri kullanır
  window.NOT_ARACLARI = {
    notuDuzenle: notuDuzenle,
    eklenti: notDuzenleEklentisi,
    // yazdırma sayfası kök klasörde çalışır: tüm göreli yollar köke göre yazılır
    kokeGore: function (md, dosya) {
      return goreliHedefler(md, function (hedef) { return kokYolu(dosya, hedef); });
    }
  };

  window.$docsify = {
    name: 'Veri Madenciliği ve Büyük Veri',
    repo: DEPO,
    homepage: 'ders_notu.md',
    loadSidebar: !YAZDIR,
    alias: { '/.*/_sidebar.md': '/_sidebar.md' },
    subMaxLevel: 2,
    relativePath: true,
    auto2top: true,
    executeScript: true,
    search: {
      paths: 'auto',
      depth: 3,
      placeholder: 'Notta ara',
      noData: 'Sonuç bulunamadı'
    },
    plugins: [uyariKutulari],
    markdown: {
      renderer: {
        code: function (code, lang) {
          // ```math blokları (GitHub'ın display formül biçimi) → KaTeX ile çiz
          if (lang === 'math' && window.katex) {
            return '<div class="math-blok">' +
              window.katex.renderToString(code, { displayMode: true, throwOnError: false }) +
              '</div>';
          }
          return this.origin.code.apply(this, arguments);
        }
      }
    }
  };
})();
