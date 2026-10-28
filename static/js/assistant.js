(function () {
    'use strict';

    var racine = document.getElementById('assistant');
    if (!racine) { return; }

    var bouton = document.getElementById('assistant-bouton');
    var panneau = document.getElementById('assistant-panneau');
    var fermer = document.getElementById('assistant-fermer');
    var journal = document.getElementById('assistant-journal');
    var statut = document.getElementById('assistant-statut');
    var formulaire = document.getElementById('assistant-formulaire');
    var champ = document.getElementById('assistant-texte');
    var info = document.getElementById('assistant-info');
    var infoOk = document.getElementById('assistant-info-ok');
    var suggestions = document.getElementById('assistant-suggestions');

    var csrf = racine.dataset.csrf;
    var urlMessage = racine.dataset.urlMessage;
    var urlVoix = racine.dataset.urlVoix;
    var Reconnaissance = window.SpeechRecognition || window.webkitSpeechRecognition;

    var reco = null;
    var audio = null;
    var finParole = null;
    var occupe = false;
    var generation = 0;
    var historique = [];

    /* ---------- Mémoire de la conversation (gardée d'une page à l'autre) ---------- */
    try {
        historique = JSON.parse(sessionStorage.getItem('assistant_historique') || '[]');
        if (!Array.isArray(historique)) { historique = []; }
    } catch (e) { historique = []; }

    function sauvegarder() {
        try { sessionStorage.setItem('assistant_historique', JSON.stringify(historique.slice(-8))); } catch (e) {}
    }

    function infoAcceptee() {
        try { return localStorage.getItem('assistant_info_ok') === '1'; } catch (e) { return true; }
    }

    /* ---------- Affichage ---------- */
    function etat(nom, texte) {
        racine.dataset.etat = nom;
        statut.textContent = texte || '';
    }

    function ajouterMessage(role, texte) {
        var bulle = document.createElement('div');
        bulle.className = 'assistant-msg assistant-msg-' + role;
        bulle.textContent = texte;
        journal.appendChild(bulle);
        while (journal.children.length > 12) { journal.removeChild(journal.firstChild); }
        journal.scrollTop = journal.scrollHeight;
        suggestions.hidden = true;
    }

    function majPanier(quantite) {
        var liens = document.querySelectorAll('.menu-droite a');
        for (var i = 0; i < liens.length; i++) {
            if (liens[i].getAttribute('href') === '/panier/') {
                liens[i].textContent = 'Panier (' + quantite + ')';
            }
        }
    }

    function ouvrirPanneau() {
        panneau.hidden = false;
        try { sessionStorage.setItem('assistant_ouvert', '1'); } catch (e) {}
        info.hidden = infoAcceptee();
    }

    function fermerPanneau() {
        generation++;
        occupe = false;
        arreterEcoute();
        arreterParole();
        panneau.hidden = true;
        try { sessionStorage.removeItem('assistant_ouvert'); } catch (e) {}
        etat('repos', '');
    }

    /* ---------- Voix de l'assistant (Edge TTS, avec la voix du navigateur en secours) ---------- */
    function arreterParole() {
        if (audio) { audio.pause(); audio = null; }
        if (window.speechSynthesis) { window.speechSynthesis.cancel(); }
        if (finParole) { var f = finParole; finParole = null; f(); }
    }

    function parlerNavigateur(texte, fin) {
        if (!window.speechSynthesis) { fin(); return; }
        var enonce = new SpeechSynthesisUtterance(texte);
        enonce.lang = 'fr-FR';
        enonce.onend = fin;
        enonce.onerror = fin;
        window.speechSynthesis.speak(enonce);
    }

    function parler(texte) {
        return new Promise(function (resolve) {
            var termine = false;
            function fin() {
                if (termine) { return; }
                termine = true;
                finParole = null;
                resolve();
            }
            finParole = fin;
            etat('parole', 'Je parle…');

            fetch(urlVoix, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify({ texte: texte })
            }).then(function (reponse) {
                if (!reponse.ok) { throw new Error('voix'); }
                return reponse.blob();
            }).then(function (blob) {
                if (termine) { return; }
                var adresse = URL.createObjectURL(blob);
                var lecteur = new Audio(adresse);
                audio = lecteur;
                lecteur.onended = function () { URL.revokeObjectURL(adresse); fin(); };
                lecteur.onerror = function () { URL.revokeObjectURL(adresse); parlerNavigateur(texte, fin); };
                return lecteur.play();
            }).catch(function () {
                if (!termine) { parlerNavigateur(texte, fin); }
            });
        });
    }

    /* ---------- Échange avec Django (puis Grok) ---------- */
    function appliquerActions(actions) {
        var adresse = null;
        actions.forEach(function (action) {
            if (action.type === 'panier') { majPanier(action.quantite); }
            // Seules les adresses relatives du site sont acceptées
            if (action.type === 'naviguer' && typeof action.url === 'string' && /^\/(?!\/)/.test(action.url)) {
                adresse = action.url;
            }
        });
        return adresse;
    }

    function envoyer(texte) {
        texte = (texte || '').trim();
        if (!texte || occupe) { return; }
        if (!infoAcceptee()) { info.hidden = false; return; }

        occupe = true;
        var tour = ++generation;
        ajouterMessage('user', texte);
        etat('reflexion', 'Je réfléchis…');

        fetch(urlMessage, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({
                message: texte,
                historique: historique.slice(-6),
                page: window.location.pathname
            })
        }).then(function (reponse) {
            return reponse.json().catch(function () {
                return { reponse: "Je n'ai pas pu répondre. Réessayez dans un instant.", actions: [], erreur: true };
            });
        }).then(function (donnees) {
            if (tour !== generation) { return; }
            var reponse = donnees.reponse || "Je n'ai pas pu répondre.";
            ajouterMessage('assistant', reponse);
            if (!donnees.erreur) {
                historique.push({ role: 'user', content: texte });
                historique.push({ role: 'assistant', content: reponse });
                sauvegarder();
            }
            var adresse = appliquerActions(donnees.actions || []);
            return parler(reponse).then(function () {
                if (tour === generation && adresse) {
                    try { sessionStorage.setItem('assistant_ouvert', '1'); } catch (e) {}
                    window.location.href = adresse;
                }
            });
        }).catch(function () {
            if (tour === generation) {
                ajouterMessage('assistant', "La connexion a échoué. Réessayez dans un instant.");
            }
        }).then(function () {
            if (tour === generation) { occupe = false; etat('repos', ''); }
        });
    }

    /* ---------- Écoute (Web Speech API) ---------- */
    function arreterEcoute() {
        if (reco) {
            reco.onend = null;
            try { reco.abort(); } catch (e) {}
            reco = null;
        }
    }

    function demarrerEcoute() {
        if (occupe) { return; }
        arreterParole();
        if (!Reconnaissance) {
            etat('repos', "Votre navigateur ne gère pas la reconnaissance vocale : utilisez Chrome ou Edge, ou écrivez votre message.");
            champ.focus();
            return;
        }
        arreterEcoute();

        var texteFinal = '';
        var erreur = false;
        var r = new Reconnaissance();
        reco = r;
        r.lang = 'fr-FR';
        r.interimResults = true;
        r.continuous = false;
        r.maxAlternatives = 1;

        r.onstart = function () { etat('ecoute', 'Je vous écoute…'); };
        r.onresult = function (e) {
            var provisoire = '';
            for (var i = e.resultIndex; i < e.results.length; i++) {
                var morceau = e.results[i][0].transcript;
                if (e.results[i].isFinal) { texteFinal += morceau; } else { provisoire += morceau; }
            }
            if (provisoire) { statut.textContent = '« ' + provisoire + ' »'; }
        };
        r.onerror = function (e) {
            erreur = true;
            var messages = {
                'not-allowed': "Le micro est bloqué : autorisez-le dans votre navigateur.",
                'service-not-allowed': "Le micro est bloqué : autorisez-le dans votre navigateur.",
                'audio-capture': "Aucun micro détecté.",
                'no-speech': "Je n'ai rien entendu. Touchez le micro pour réessayer.",
                'network': "La reconnaissance vocale est injoignable : vérifiez votre connexion."
            };
            etat('repos', messages[e.error] || "La reconnaissance vocale a échoué. Vous pouvez écrire votre message.");
        };
        r.onend = function () {
            if (reco === r) { reco = null; }
            if (erreur) { return; }
            texteFinal = texteFinal.trim();
            if (texteFinal) {
                envoyer(texteFinal);
            } else {
                etat('repos', "Je n'ai rien entendu. Touchez le micro pour réessayer.");
            }
        };
        try { r.start(); } catch (e) { etat('repos', "Impossible de démarrer le micro."); }
    }

    /* ---------- Commandes ---------- */
    function interrompre() {
        generation++;
        occupe = false;
        arreterEcoute();
        arreterParole();
    }

    bouton.addEventListener('click', function () {
        if (panneau.hidden) {
            ouvrirPanneau();
            if (infoAcceptee()) { demarrerEcoute(); }
            return;
        }
        var courant = racine.dataset.etat;
        if (courant === 'ecoute') { if (reco) { reco.stop(); } return; }
        if (courant === 'reflexion') { return; }
        if (courant === 'parole') { interrompre(); }
        if (infoAcceptee()) { demarrerEcoute(); } else { info.hidden = false; }
    });

    fermer.addEventListener('click', fermerPanneau);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !panneau.hidden) { fermerPanneau(); }
    });

    infoOk.addEventListener('click', function () {
        try { localStorage.setItem('assistant_info_ok', '1'); } catch (e) {}
        info.hidden = true;
        demarrerEcoute();
    });

    formulaire.addEventListener('submit', function (e) {
        e.preventDefault();
        var texte = champ.value;
        champ.value = '';
        interrompre();
        envoyer(texte);
    });

    suggestions.addEventListener('click', function (e) {
        var cible = e.target.closest('button[data-texte]');
        if (cible) { envoyer(cible.dataset.texte); }
    });

    window.addEventListener('pagehide', function () {
        arreterEcoute();
        if (window.speechSynthesis) { window.speechSynthesis.cancel(); }
    });

    /* ---------- Reprise après un changement de page ---------- */
    try {
        if (sessionStorage.getItem('assistant_ouvert') === '1') {
            ouvrirPanneau();
            historique.slice(-4).forEach(function (element) {
                ajouterMessage(element.role === 'user' ? 'user' : 'assistant', element.content);
            });
        }
    } catch (e) {}
})();