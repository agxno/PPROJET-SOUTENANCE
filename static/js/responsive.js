/* ==========================================================================
   RESPONSIVE — petits comportements liés à l'affichage
     1. Hauteur réelle de l'en-tête (le contenu ne passe plus dessous)
     2. Bouton « afficher / masquer le mot de passe »
     3. Filtres de la boutique repliables sur tablette et mobile
   ========================================================================== */
(function () {
    'use strict';

    /* 1. Hauteur réelle de l'en-tête -> variable CSS --header-height */
    var entete = document.querySelector('.verre-entete');
    var petit = window.matchMedia('(max-width: 860px)');
    function mesurerEntete() {
        if (!entete) return;
        if (petit.matches) {
            document.documentElement.style.setProperty('--header-height', Math.ceil(entete.offsetHeight) + 'px');
        } else {
            document.documentElement.style.removeProperty('--header-height');
        }
    }
    mesurerEntete();
    window.addEventListener('load', mesurerEntete);
    window.addEventListener('resize', mesurerEntete);
    window.addEventListener('orientationchange', mesurerEntete);
    if (petit.addEventListener) { petit.addEventListener('change', mesurerEntete); }

    /* 2. Afficher / masquer le mot de passe */
    document.querySelectorAll('.auth-toggle-password').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
            var zone = bouton.closest('.auth-input-wrap') || bouton.parentNode;
            var champ = zone.querySelector('input');
            if (!champ) return;
            var visible = champ.type === 'password';
            champ.type = visible ? 'text' : 'password';
            bouton.setAttribute('aria-label', visible ? 'Masquer le mot de passe' : 'Afficher le mot de passe');
            bouton.setAttribute('aria-pressed', visible ? 'true' : 'false');
        });
    });

    /* 3. Filtres de la boutique repliables */
    var filtres = document.getElementById('filtres');
    if (filtres) {
        var tete = filtres.querySelector('.boutique-filtres-head');
        var bouton = document.createElement('button');
        bouton.type = 'button';
        bouton.className = 'boutique-filtres-toggle';
        bouton.textContent = 'Filtres';
        bouton.setAttribute('aria-expanded', 'false');
        bouton.setAttribute('aria-controls', 'filtres');
        filtres.insertBefore(bouton, tete || filtres.firstChild);
        bouton.addEventListener('click', function () {
            var ouvert = filtres.classList.toggle('ouvert');
            bouton.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
        });
        // Le lien « Recherche » de l'en-tête (#recherche) ouvre aussi les filtres
        if (location.hash === '#recherche') { filtres.classList.add('ouvert'); bouton.setAttribute('aria-expanded', 'true'); }
    }
})();
