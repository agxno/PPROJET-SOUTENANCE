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
    document.querySelectorAll(
        '.produit-visuel, .categorie .visuel, .detail-visuel, .tuile, .editorial-visuel'
    ).forEach(function (conteneur) {
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
            '.detail-visuel, .detail-infos, .pied-grille > div, ' +
            '.tuile, .editorial-visuel, .editorial-texte'
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

    /* ---------- Carrousel de l'accueil ---------- */
    var carrousel = document.querySelector('.carrousel');
    if (carrousel) {
        var diapos = carrousel.querySelectorAll('.diapo');
        var points = carrousel.querySelectorAll('.point');

        if (diapos.length > 1) {
            var courant = 0;
            var minuteur = null;

            var afficher = function (i) {
                courant = (i + diapos.length) % diapos.length;
                diapos.forEach(function (d, n) {
                    var actif = n === courant;
                    d.classList.toggle('active', actif);
                    d.setAttribute('aria-hidden', actif ? 'false' : 'true');
                });
                points.forEach(function (p, n) { p.classList.toggle('actif', n === courant); });
            };
            var arreter = function () {
                if (minuteur) { clearInterval(minuteur); minuteur = null; }
            };
            var demarrer = function () {
                if (reduit) return;
                arreter();
                minuteur = setInterval(function () { afficher(courant + 1); }, 6500);
            };
            var aller = function (i) { afficher(i); demarrer(); };

            var prec = carrousel.querySelector('.fleche-prec');
            var suiv = carrousel.querySelector('.fleche-suiv');
            if (prec) prec.addEventListener('click', function () { aller(courant - 1); });
            if (suiv) suiv.addEventListener('click', function () { aller(courant + 1); });
            points.forEach(function (p, n) {
                p.addEventListener('click', function () { aller(n); });
            });

            // Pause au survol, au focus et quand l'onglet est caché
            carrousel.addEventListener('mouseenter', arreter);
            carrousel.addEventListener('mouseleave', demarrer);
            carrousel.addEventListener('focusin', arreter);
            carrousel.addEventListener('focusout', demarrer);
            document.addEventListener('visibilitychange', function () {
                if (document.hidden) { arreter(); } else { demarrer(); }
            });

            // Glissement tactile
            var departX = null;
            carrousel.addEventListener('touchstart', function (e) {
                departX = e.touches[0].clientX;
            }, { passive: true });
            carrousel.addEventListener('touchend', function (e) {
                if (departX === null) return;
                var ecart = e.changedTouches[0].clientX - departX;
                departX = null;
                if (Math.abs(ecart) > 45) aller(courant + (ecart < 0 ? 1 : -1));
            }, { passive: true });

            demarrer();
        }
    }

    /* ---------- Messages : disparition automatique ---------- */
    document.querySelectorAll('.message').forEach(function (message) {
        setTimeout(function () {
            message.classList.add('masque');
            setTimeout(function () { message.remove(); }, 600);
        }, 8000);
    });
})();