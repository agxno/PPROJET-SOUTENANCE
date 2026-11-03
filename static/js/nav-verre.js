(function () {
    'use strict';

    var nav = document.querySelector('[data-verre]');
    if (!nav) { return; }

    var bulle = nav.querySelector('.verre-bulle');
    var liens = Array.prototype.slice.call(nav.querySelectorAll('.verre-lien'));
    var actif = nav.querySelector('.verre-lien.actif');
    var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var minuteur = null;

    /* Place la bulle sous un lien (ou la cache s'il n'y en a pas) */
    function placer(lien, animer) {
        if (!lien) {
            bulle.classList.remove('pret');
            return;
        }
        // Première apparition : pas de glissement depuis le coin
        if (!bulle.classList.contains('pret')) { animer = false; }

        if (!animer) { bulle.style.transition = 'none'; }
        bulle.style.setProperty('--x', lien.offsetLeft + 'px');
        bulle.style.setProperty('--w', lien.offsetWidth + 'px');
        bulle.classList.add('pret');

        if (!animer) {
            void bulle.offsetWidth;
            bulle.style.transition = '';
        } else if (!reduit) {
            // La bulle s'étire un instant pendant le déplacement
            bulle.classList.add('etire');
            window.clearTimeout(minuteur);
            minuteur = window.setTimeout(function () { bulle.classList.remove('etire'); }, 380);
        }
    }

    /* Au chargement : la bulle part de l'ancien lien et glisse vers le nouveau */
    var index = liens.indexOf(actif);
    var precedent = -1;
    try {
        precedent = parseInt(sessionStorage.getItem('verre_precedent'), 10);
    } catch (e) { precedent = -1; }
    if (isNaN(precedent)) { precedent = -1; }

    if (actif && !reduit && precedent >= 0 && precedent < liens.length && precedent !== index) {
        placer(liens[precedent], false);
        window.requestAnimationFrame(function () {
            window.requestAnimationFrame(function () { placer(actif, true); });
        });
    } else {
        placer(actif, false);
    }
    try { sessionStorage.setItem('verre_precedent', String(index)); } catch (e) {}

    /* Survol et clavier : la bulle suit, puis revient sur la page courante */
    liens.forEach(function (lien) {
        lien.addEventListener('mouseenter', function () { placer(lien, true); });
        lien.addEventListener('focus', function () { placer(lien, true); });
    });
    nav.addEventListener('mouseleave', function () { placer(actif, true); });
    nav.addEventListener('focusout', function (e) {
        if (!nav.contains(e.relatedTarget)) { placer(actif, true); }
    });

    /* Remesure si la fenêtre change ou si les polices arrivent après coup */
    window.addEventListener('resize', function () { placer(actif, false); });
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(function () { placer(actif, false); });
    }
})();