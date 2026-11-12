/* ==========================================
   FICHE PRODUIT — Interactions
========================================== */
(function () {
    'use strict';

    // ─── Quantité (boutons + / -) ───
    const input = document.getElementById('quantite');
    const btnMoins = document.querySelector('[data-qte-moins]');
    const btnPlus = document.querySelector('[data-qte-plus]');

    if (input && btnMoins && btnPlus) {
        const getMin = () => parseInt(input.min, 10) || 1;
        const getMax = () => parseInt(input.max, 10) || 99;

        btnMoins.addEventListener('click', () => {
            const val = parseInt(input.value, 10) || 1;
            if (val > getMin()) input.value = val - 1;
        });

        btnPlus.addEventListener('click', () => {
            const val = parseInt(input.value, 10) || 1;
            if (val < getMax()) input.value = val + 1;
        });

        input.addEventListener('change', () => {
            let val = parseInt(input.value, 10);
            if (isNaN(val) || val < getMin()) val = getMin();
            if (val > getMax()) val = getMax();
            input.value = val;
        });
    }

    // ─── Scroll smooth vers la section avis ───
    document.querySelectorAll('a[href="#avis"]').forEach((link) => {
        link.addEventListener('click', (e) => {
            const target = document.getElementById('avis');
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
})();