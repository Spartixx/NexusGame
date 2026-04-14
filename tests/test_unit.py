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
import sys, os

from flask.testing import FlaskClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Union, Any, Optional
from app_gamestore import app, init_db, get_db


# Fixtures
@pytest.fixture
def client():
    """
    Crée un client de test Flask avec une Base de données SQLite en mémoire.
    Teardown automatique avec un DELETE de toutes les parties.
    """
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'

    with app.test_client() as client:
        with app.app_context():
            init_db()
            db = get_db()
            db.execute("DELETE FROM games;")
            db.commit()
        yield client

@pytest.fixture
def game_body(genre: str = "RPG", game_id: int = 0):
    """Body pour la création d'un jeu"""
    return {
        'title':  f"title-{genre}-test-{game_id}",
        'genre':  genre,
        'price':  10,
        'rating': 4,
        'stock':  50,
    }

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Health & endpoints de base
# ════════════════════════════════════════════════════════════════════════════════


class TestingService:
    def _test_status_ok(self, client: FlaskClient, url: str, status_code: int = 200):
        """
        Assert a status code is ok and return response body.
        """
        response = client.get(url)
        assert response.status_code == status_code
        return response.json

    def _verify_fields(self, game: Dict, fields: Union[List[str], List[Dict[str, Any]]]):
        """
        verify fields existence in a game, and optionaly verify its value
        """
        for field in fields:
            if type(field) == str:
                assert field in game
            elif type(field) == dict:
                for key, value in field:
                    assert key in game
                    assert game[key] == value

    def _add_game(
        self,
        client: FlaskClient,
        title: Optional[str] = None,
        gender: Optional[str] = "RPG",
        price: Optional[float] = 10,
        rating: Optional[float] = 4,
        stock: Optional[float] = 10,
    ) -> Dict:
        return client.post(
            "/games",
            json={
                "title": f"{title if title is not None else f'title-{gender}-{price}-{stock}'}", # To get a unique title
                "genre": gender,
                "price": price,
                "rating": rating,
                "stock": stock,
            }
        ).json



class TestHealth(TestingService):
    def test_health_retourne_200(self, client):
        """
            Vérifier que GET /health retourne 200 et {"status": "ok"}.
        """
        self._test_status_ok(client, "/health")

    def test_health_contient_service(self, client):
        """
            Vérifier que la réponse contient la clé "service".
        """
        assert "service" in client.get("/health").json

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Liste des jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestListGames(TestingService):
    def test_liste_retourne_200(self, client):
        """
            GET /games retourne 200 et une liste non vide.
        """
        self._add_game(client)
        data = self._test_status_ok(client, "/games")
        assert type(data) is list
        assert len(data) > 0

    def test_liste_contient_les_champs_attendus(self, client):
        for game in client.get("/games").json:
            self._verify_fields(game, ["id", "title", "genre", "price", "rating"])

    def test_filtre_par_genre(self, client):
        """
        Vérifier que tous les éléments ont genre == "RPG".
        """
        for game in client.get("/games").json:
            self._verify_fields(game, [{"genre": "RPG"}])

    def test_tri_par_prix_croissant(self, client):
        """
        GET /games?sort=price&order=asc retourne les jeux triés par prix croissant.
        """
        self._add_game(client, price=10)
        self._add_game(client, price=20)
        games = self._test_status_ok(client, "/games?sort=price&order=asc")

        assert len(games) > 1
        old_price = games[0]

        for game in games[1:]:
            assert game["price"] > old_price["price"]
            old_price = game



# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Création de jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestCreateGame(TestingService):
    def test_creation_valide_retourne_201(self, client, game_body):
        """
        POST /games avec titre, genre, prix valides → 201 + id dans la réponse.
        """
        assert client.post('/games', json=game_body).status_code == 201

    def test_creation_sans_titre_retourne_400(self, client, game_body):
        """
        POST /games sans "title" → 400.
        """
        del game_body["title"]
        assert client.post('/games', json=game_body).status_code == 400

    def test_creation_prix_negatif_retourne_400(self, client, game_body):
        """
        POST /games avec price = -5 → 400.
        """
        game_body['price'] = -5
        assert client.post('/games', json=game_body).status_code == 400

    def test_creation_titre_duplique_retourne_409(self, client, game_body):
        """
        Créer le même jeu deux fois → second appel retourne 409.
        """
        assert client.post('/games', json=game_body).status_code == 201
        assert client.post('/games', json=game_body).status_code == 409

    @pytest.mark.parametrize("title,genre,price,expected_status,rating,stock", [
        ("Mario", "Adventure", "string", 400, 1, 10), # Test price is a string
        ("", "Adventure", 30, 400, -2, 10), # Test rating is negative
        ("Mario", "Adventure", 5.0, 400, 2, -1), # Test stock is negative
        ("", "Adventure", 30, 400, 4, 5), # Test Title is empty
        ("Mario", "Adventure", -5.0, 400, 5, 6), # Test Price is None
        (None, "Adventure", 30, 400, 6, 7), # Test Title is None
        ("Mario", "Adventure", 59.99, 201, 3, 4), # Test it works
    ])
    def test_create_game_validation(self, client, title, genre, price, expected_status, rating, stock):
        r = client.post("/games",
                        json={"title": title, "genre": genre, "price": price, "rating": rating, "stock": stock})
        assert r.status_code == expected_status


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Récupération, mise à jour, suppression
# ════════════════════════════════════════════════════════════════════════════════

class TestGameCRUD(TestingService):
    def test_get_jeu_existant(self, client):
        """
        Créer un jeu, récupérer son id, GET /games/{id} → 200.
        """
        game_id = self._add_game(client).get("id")
        assert game_id is not None
        self._test_status_ok(client, f"/games/{game_id}")

    def test_get_jeu_inexistant_retourne_404(self, client):
        """
        GET /games/99999 → 404.
        """
        self._test_status_ok(client, f"/games/{99999}", 404)

    def test_update_prix(self, client):
        """
        Créer un jeu, PUT /games/{id} avec nouveau prix, vérifier la mise à jour.
        """
        # À compléter
        game = self._add_game(client)
        client.put(
            f"/games/{game.get('id')}",
            json={"price": 9.98}
        )
        assert client.get(f"/games/{game.get('id')}").json["price"] == 9.98

    def test_delete_jeu(self, client):
        """
        Créer un jeu, DELETE /games/{id} → 204, puis GET → 404.
        """
        game_id = self._add_game(client).get("id")
        assert game_id is not None
        assert client.delete(f"/games/{game_id}").status_code == 204


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Choix libres (à justifier dans le README)
# ════════════════════════════════════════════════════════════════════════════════

class TestGameStats(TestingService):
    def test_game_stats_200(self, client):
        assert client.get('/games/stats').status_code == 200

    def test_game_stats_format(self, client, game_body):
        self._add_game(client)
        response = client.get('/games/stats')
        assert type(response.json) == dict
        assert 'total_games' in response.json
        assert 'genres' in response.json


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Endpoint /games/featured (NGS-108)
# ════════════════════════════════════════════════════════════════════════════════

class TestFeatured(TestingService):
    """
    Tests sur l'endpoint GET /games/featured.
    Consultez la documentation de l'endpoint dans app_gamestore.py.
    Si un test échoue alors que votre assertion est correcte,
    documentez ce que vous observez dans le README.
    """

    def test_featured_retourne_200(self, client):
        """GET /games/featured retourne 200."""
        self._test_status_ok(client, "/games/featured")

    def test_featured_retourne_liste(self, client):
        """La réponse contient une clé 'featured' qui est une liste."""
        response_json = client.get("/games/featured").json
        assert "featured"in response_json
        assert type(response_json.get("featured")) is list

    def test_featured_max_5_par_defaut(self, client):
        """Sans paramètre, au maximum 5 jeux sont retournés."""
        for i in range(6):
            self._add_game(client, f"title-{i}")

        response_json = client.get('/games/featured').json

        assert len(response_json['featured']) <= 5

    def test_featured_limit_param(self, client):
        """?limit=3 retourne au maximum 3 jeux."""
        for i in range(5):
            self._add_game(client, f"title-{i}")

        response_json = client.get('/games/featured?limit=3').json

        assert len(response_json['featured']) <= 3

    def test_featured_tries_par_rating_decroissant(self, client):
        """Les jeux sont triés par rating décroissant."""
        for i in range(2):
            self._add_game(client, title=f"title-{i}", rating=i, price=20, stock=10)

        games = self._test_status_ok(client, "/games/featured").get("featured")

        assert len(games) > 1
        old_rating = games[0]

        for game in games[1:]:
            assert game["rating"] > old_rating["rating"]
            old_rating = game

    def test_featured_sans_jeux_gratuits(self, client):
        """Les jeux gratuits ne doivent pas apparaître dans featured."""
        self._add_game(client, price=0)
        assert len(client.get('/games/featured').json.get("featured")) == 0

    def test_featured_sans_jeux_hors_stock(self, client):
        """Les jeux hors stock ne doivent pas apparaître dans featured."""
        self._add_game(client, stock=0)
        assert len(client.get('/games/featured').json.get("featured")) == 0
