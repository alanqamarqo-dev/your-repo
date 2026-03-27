// AGL Security Tool — Language toggle (EN ↔ AR)
(function () {
  'use strict';

  var lang = localStorage.getItem('agl-lang') || 'en';
  var btn = document.getElementById('langToggle');

  function applyLang(l) {
    lang = l;
    localStorage.setItem('agl-lang', l);

    var isAr = l === 'ar';
    document.documentElement.lang = isAr ? 'ar' : 'en';
    document.documentElement.dir = isAr ? 'rtl' : 'ltr';
    document.body.classList.toggle('rtl', isAr);

    var attr = isAr ? 'data-ar' : 'data-en';
    var els = document.querySelectorAll('[data-en]');
    for (var i = 0; i < els.length; i++) {
      var val = els[i].getAttribute(attr);
      if (val) els[i].textContent = val;
    }

    btn.textContent = isAr ? 'English' : 'عربي';
  }

  btn.addEventListener('click', function () {
    applyLang(lang === 'en' ? 'ar' : 'en');
  });

  applyLang(lang);
})();
