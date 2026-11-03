
(function () {
    'use strict';

    const section = document.querySelector('.categories-interactives');

    if (!section) return;

    const categories = Array.from(
        section.querySelectorAll('.ci-categorie')
    );

    const images = Array.from(
        section.querySelectorAll('.ci-image')
    );

    if (!categories.length || categories.length !== images.length) {
        return;
    }

    const reducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;

    const hasGSAP = typeof window.gsap !== 'undefined';

    let activeIndex = 0;
    let animationId = 0;

    /**
     * Affiche la catégorie sélectionnée.
     */
    function afficher(index) {
        if (index < 0 || index >= categories.length) return;
        if (index === activeIndex) return;

        const previousImage = images[activeIndex];
        const nextImage = images[index];

        activeIndex = index;
        animationId++;

        const currentAnimation = animationId;

        // Mise à jour du menu
        categories.forEach(function (category, i) {
            const selected = i === index;

            category.classList.toggle('ci-active', selected);
            category.setAttribute('aria-pressed', selected ? 'true' : 'false');
        });

        // Mise à jour des images
        images.forEach(function (image, i) {
            const selected = i === index;

            image.classList.toggle('ci-image-active', selected);
            image.setAttribute('aria-hidden', selected ? 'false' : 'true');
        });

        // Respect de la préférence de réduction des animations
        if (reducedMotion) return;

        if (hasGSAP) {
            gsap.killTweensOf([previousImage, nextImage]);

            // Préparation de la nouvelle image
            gsap.set(nextImage, {
                autoAlpha: 1,
                scale: 1.06,
                zIndex: 2
            });

            gsap.set(previousImage, {
                zIndex: 1
            });

            // Transition
            gsap.fromTo(
                nextImage,
                {
                    clipPath: 'inset(0 0 0 10%)',
                    scale: 1.06
                },
                {
                    clipPath: 'inset(0 0 0 0%)',
                    scale: 1,
                    duration: 0.8,
                    ease: 'power3.out',
                    onComplete: function () {
                        // Évite qu'une ancienne animation
                        // modifie une sélection plus récente.
                        if (currentAnimation !== animationId) return;

                        gsap.set(previousImage, {
                            autoAlpha: 0,
                            zIndex: 0
                        });

                        gsap.set(nextImage, {
                            clearProps: 'clipPath,transform,zIndex,opacity,visibility'
                        });
                    }
                }
            );
        }
    }

    /**
     * Interaction avec les catégories.
     */
    categories.forEach(function (category, index) {

        // Ordinateur : survol
        category.addEventListener('mouseenter', function () {
            afficher(index);
        });

        // Clavier : navigation accessible
        category.addEventListener('focus', function () {
            afficher(index);
        });

        // Clic et écran tactile
        category.addEventListener('click', function () {
            afficher(index);
        });

    });

    /**
     * État initial.
     */
    categories.forEach(function (category, index) {
        const selected = index === 0;

        category.classList.toggle('ci-active', selected);
        category.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });

    images.forEach(function (image, index) {
        const selected = index === 0;

        image.classList.toggle('ci-image-active', selected);
        image.setAttribute('aria-hidden', selected ? 'false' : 'true');
    });

})();
