(function () {
    'use strict';

    var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- Barre de chargement en haut de page ---------- */
    var barre = document.createElement('div');
    barre.className = 'barre-chargement';
    barre.setAttribute('aria-hidden', 'true');
    document.body.appendChild(barre);

    function demarrerBarre() {
        barre.classList.remove('demarre');
        void barre.offsetWidth; // relance la transition
        barre.classList.add('demarre');
    }

    /* ---------- Clic sur un lien interne ---------- */
    document.addEventListener('click', function (e) {
        if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var lien = e.target.closest('a[href]');
        if (!lien) return;
        if (lien.target && lien.target !== '_self') return;
        if (lien.hasAttribute('download')) return;

        var url;
        try { url = new URL(lien.href, window.location.href); } catch (err) { return; }
        if (url.origin !== window.location.origin) return;
        if (url.pathname === window.location.pathname && url.search === window.location.search) return;

        demarrerBarre();
        if (lien.classList.contains('bouton')) lien.classList.add('en-cours');

        // Filtres et pagination de la boutique : la grille s'estompe
        var grille = document.querySelector('.grille-produits');
        if (grille && lien.closest('.filtres, .pagination')) grille.classList.add('attente');
    });

    /* ---------- Envoi d'un formulaire ---------- */
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (e.defaultPrevented || !(form instanceof HTMLFormElement)) return;

        // Empêche le double envoi
        if (form.dataset.envoye === '1') {
            e.preventDefault();
            return;
        }
        form.dataset.envoye = '1';

        var bouton = e.submitter || form.querySelector('button[type="submit"], button:not([type])');
        if (bouton) {
            bouton.classList.add('en-cours');
            bouton.setAttribute('aria-busy', 'true');
        }
        demarrerBarre();
    });

    /* ---------- Retour arrière du navigateur : on remet tout à zéro ---------- */
    window.addEventListener('pageshow', function (e) {
        if (!e.persisted) return;
        barre.classList.remove('demarre');
        document.querySelectorAll('form[data-envoye]').forEach(function (f) { delete f.dataset.envoye; });
        document.querySelectorAll('.en-cours').forEach(function (b) {
            b.classList.remove('en-cours');
            b.removeAttribute('aria-busy');
        });
        document.querySelectorAll('.attente').forEach(function (g) { g.classList.remove('attente'); });
    });

    /* ---------- Photos : squelette puis fondu ---------- */
    document.querySelectorAll('.produit-visuel, .categorie .visuel, .detail-visuel').forEach(function (conteneur) {
        var img = conteneur.querySelector('img');
        if (!img) return;
        if (img.complete && img.naturalWidth > 0) {
            img.classList.add('charge');
            return;
        }
        conteneur.classList.add('chargement');
        function fini() {
            img.classList.add('charge');
            conteneur.classList.remove('chargement');
        }
        img.addEventListener('load', fini);
        img.addEventListener('error', fini);
    });

    /* ---------- Apparition au scroll ---------- */
    if (!reduit && 'IntersectionObserver' in window) {
        var cibles = document.querySelectorAll(
            '.section-titre, .categorie, .produit, .valeur, .histoire, .appel .conteneur, ' +
            '.detail-visuel, .detail-infos, .pied-grille > div'
        );
        var observateur = new IntersectionObserver(function (entrees) {
            entrees.forEach(function (entree) {
                if (!entree.isIntersecting) return;
                var el = entree.target;
                el.classList.add('visible');
                observateur.unobserve(el);
                setTimeout(function () { el.style.transitionDelay = ''; }, 1200);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

        cibles.forEach(function (el) {
            var rang = el.parentElement ? Array.prototype.indexOf.call(el.parentElement.children, el) : 0;
            el.style.transitionDelay = (rang % 4) * 90 + 'ms';
            el.classList.add('revele');
            observateur.observe(el);
        });
    }

    /* ---------- Messages : disparition automatique ---------- */
    document.querySelectorAll('.message').forEach(function (message) {
        setTimeout(function () {
            message.classList.add('masque');
            setTimeout(function () { message.remove(); }, 600);
        }, 8000);
    });
})();