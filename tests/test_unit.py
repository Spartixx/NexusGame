"""
test_unit.py — Tests unitaires NexusGame
==========================================
Contexte : Suite de tests unitaires sur l'API GameStore.
Chaque test est isolé — BDD fraîche à chaque appel (fixture function scope).

Lancement :
    pytest tests/test_unit.py -v
    pytest tests/test_unit.py -v --cov=app_gamestore --cov-report=html
"""
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Health & endpoints de base
# ════════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_retourne_200(self, client):
        """
        TODO — Vérifier que GET /health retourne 200 et {"status": "ok"}.
        """
        # À compléter
        pass

    def test_health_contient_service(self, client):
        """
        TODO — Vérifier que la réponse contient la clé "service".
        """
        # À compléter
        pass


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Liste des jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestListGames:
    def test_liste_retourne_200(self, client):
        """
        TODO — GET /games retourne 200 et une liste non vide.
        """
        # À compléter
        pass

    def test_liste_contient_les_champs_attendus(self, client):
        """
        TODO — Chaque jeu retourné contient au moins : id, title, genre, price, rating.
        """
        # À compléter
        pass

    def test_filtre_par_genre(self, client):
        """
        TODO — GET /games?genre=RPG retourne uniquement des jeux RPG.
        Vérifier que tous les éléments ont genre == "RPG".
        """
        # À compléter
        pass

    def test_tri_par_prix_croissant(self, client):
        """
        TODO — GET /games?sort=price&order=asc retourne les jeux triés par prix croissant.
        """
        # À compléter
        pass


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Création de jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestCreateGame:
    def test_creation_valide_retourne_201(self, client):
        """
        TODO — POST /games avec titre, genre, prix valides → 201 + id dans la réponse.
        """
        # À compléter
        pass

    def test_creation_sans_titre_retourne_400(self, client):
        """
        TODO — POST /games sans "title" → 400.
        """
        # À compléter
        pass

    def test_creation_prix_negatif_retourne_400(self, client):
        """
        TODO — POST /games avec price = -5 → 400.
        """
        # À compléter
        pass

    def test_creation_titre_duplique_retourne_409(self, client):
        """
        TODO — Créer le même jeu deux fois → second appel retourne 409.
        """
        # À compléter
        pass

    @pytest.mark.parametrize("payload,expected_status", [
        # TODO — Ajouter vos cas de validation ici
    ])
    def test_validation_parametree(self, client, payload, expected_status):
        """TODO — POST /games avec le payload, vérifier le status code."""
        # À compléter
        pass


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Récupération, mise à jour, suppression
# ════════════════════════════════════════════════════════════════════════════════

class TestGameCRUD:
    def test_get_jeu_existant(self, client):
        """
        TODO — Créer un jeu, récupérer son id, GET /games/{id} → 200.
        """
        # À compléter
        pass

    def test_get_jeu_inexistant_retourne_404(self, client):
        """
        TODO — GET /games/99999 → 404.
        """
        # À compléter
        pass

    def test_update_prix(self, client):
        """
        TODO — Créer un jeu, PUT /games/{id} avec nouveau prix, vérifier la mise à jour.
        """
        # À compléter
        pass

    def test_delete_jeu(self, client):
        """
        TODO — Créer un jeu, DELETE /games/{id} → 204, puis GET → 404.
        """
        # À compléter
        pass


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Choix libres (à justifier dans le README)
# ════════════════════════════════════════════════════════════════════════════════

class TestChoixLibres:
    """
    Ajoutez ici les tests que vous jugez critiques.
    Documentez vos choix dans le README.
    """
    pass


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Endpoint /games/featured (NGS-108)
# ════════════════════════════════════════════════════════════════════════════════

class TestFeatured:
    """
    Tests sur l'endpoint GET /games/featured.
    Consultez la documentation de l'endpoint dans app_gamestore.py.
    Si un test échoue alors que votre assertion est correcte,
    documentez ce que vous observez dans le README.
    """

    def test_featured_retourne_200(self, client):
        """TODO — GET /games/featured retourne 200."""
        pass

    def test_featured_retourne_liste(self, client):
        """TODO — La réponse contient une clé 'featured' qui est une liste."""
        pass

    def test_featured_max_5_par_defaut(self, client):
        """TODO — Sans paramètre, au maximum 5 jeux sont retournés."""
        pass

    def test_featured_limit_param(self, client):
        """TODO — ?limit=3 retourne au maximum 3 jeux."""
        pass

    def test_featured_tries_par_rating_decroissant(self, client):
        """TODO — Les jeux sont triés par rating décroissant."""
        pass

    def test_featured_sans_jeux_gratuits(self, client):
        """TODO — Les jeux gratuits ne doivent pas apparaître dans featured."""
        pass

    def test_featured_sans_jeux_hors_stock(self, client):
        """TODO — Les jeux hors stock ne doivent pas apparaître dans featured."""
        pass
