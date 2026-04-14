"""
test_integration.py — Tests d'intégration NexusGame
=====================================================
Tests de bout en bout sur l'API GameStore avec un serveur réel.
Ces tests valident le comportement complet, pas seulement la logique unitaire.

Lancement :
    pytest tests/test_integration.py -v -m integration
    pytest tests/test_integration.py -v --html=reports/integration.html
"""
import subprocess
from datetime import datetime
import pytest
import requests
import time
import sys
import os

from flask import request_started

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ════════════════════════════════════════════════════════════════════════════════
# FIXTURE — Serveur GameStore en processus réel
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def api_url():
    """
    TODO — Démarrer l'API GameStore en sous-processus réel,
    attendre qu'elle soit prête, puis la stopper après les tests.

    Indice : subprocess.Popen · time.sleep · proc.terminate()
    """
    # À compléter
    # Note : tant que la fixture n'est pas implémentée,
    # l'API doit tourner manuellement avant de lancer ces tests.
    proc = subprocess.Popen(["python", "app_gamestore.py"])
    time.sleep(3)
    proc.terminate()
    yield "http://localhost:5000"


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Scénarios de bout en bout
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestScenariosCatalogueComplet:
    """
    Scénarios E2E sur le catalogue de jeux.
    Ces tests utilisent requests (HTTP réel) — pas le client Flask.
    """

    def test_catalogue_initial_non_vide(self, api_url):
        """
        TODO — GET /games retourne 200 et une liste non vide.
        Utiliser requests.get(), pas client.get().
        """
        response = requests.get(f"{api_url}/games")
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_cycle_complet_creation_lecture_suppression(self, api_url):
        """
        TODO — Scénario complet :
        1. POST /games → créer un jeu, récupérer son id
        2. GET /games/{id} → vérifier qu'il existe
        3. DELETE /games/{id} → supprimer
        4. GET /games/{id} → vérifier 404

        """
        post_response = requests.post(f"{api_url}/games", json={"title": f"title-{datetime.now().timestamp()}", "price": 10, "rating": 5, "stock": 10, "genre": "RPG"})
        game_id = post_response.json().get("id")
        print(post_response.json())
        assert post_response.status_code == 201
        assert requests.get(f"{api_url}/games/{game_id}").status_code == 200
        assert requests.delete(f"{api_url}/games/{game_id}").status_code == 204
        assert requests.get(f"{api_url}/games/{game_id}").status_code == 404

    def test_mise_a_jour_stock(self, api_url):
        """
        TODO — Créer un jeu avec stock=10, PUT pour passer à stock=0,
        vérifier que la valeur est bien persistée en base.
        """
        game_id = requests.post(f"{api_url}/games", json={"title": f"title-{datetime.now().timestamp()}", "price": 10, "rating": 5, "stock": 10, "genre": "RPG"}).json().get("id")
        requests.put(f"{api_url}/games/{game_id}", json={"stock": 0})

        response = requests.get(f"{api_url}/games/{game_id}")
        assert response.status_code == 200
        assert response.json().get("stock") == 0
        assert requests.delete(f"{api_url}/games/{game_id}").status_code == 204


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Tests de robustesse
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRobustesse:
    """
    Ces tests valident le comportement de l'API sous des conditions inhabituelles.
    """

    def test_requetes_concurrentes(self, api_url):
        """
        TODO — Envoyer 10 requêtes GET /games en parallèle avec threading.
        Vérifier que toutes retournent 200.

        Indice :
            import threading
            results = []
            def call(): results.append(requests.get(f"{api_url}/games").status_code)
            threads = [threading.Thread(target=call) for _ in range(10)]
            ...
        """
        import threading
        results = []

        def call(): results.append(requests.get(f"{api_url}/games").status_code)

        threads = [threading.Thread(target=call) for _ in range(10)]

        for res in results:
            assert res == 200

    def test_payload_json_malforme(self, api_url):
        """
        TODO — POST /games avec un body non-JSON (texte brut).
        L'API doit retourner 400 sans crasher.
        """
        response = requests.post(f"{api_url}/games", json="test")
        assert response.status_code == 400


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Choix libres (à justifier dans le README)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestChoixLibresIntegration:
    """
    Ajoutez ici les scénarios d'intégration que VOUS jugez critiques.

    Pensez aux questions suivantes :
    - Quels enchaînements d'appels représentent un vrai usage de l'API ?
    - Qu'est-ce qui ne peut être testé qu'avec un serveur réel (pas un client Flask) ?
    - Y a-t-il des conditions de bord qui ne se voient qu'en intégration ?

    Documentez vos choix dans le README.
    """
    pass
