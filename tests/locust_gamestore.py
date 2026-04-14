"""
locust_gamestore.py — Test de charge NexusGame
================================================
Scénario : simulation d'utilisateurs naviguant sur le catalogue GameStore.

Lancement :
    locust -f tests/locust_gamestore.py --host=http://localhost:5000
    # Interface web : http://localhost:8089

    # Sans interface (headless) :
    locust -f tests/locust_gamestore.py --host=http://localhost:5000 \
           --headless -u 50 -r 5 --run-time 60s

Prérequis :
    pip install locust
    # L'API GameStore doit tourner sur http://localhost:5000
"""
from locust import HttpUser, task, between
import random


class GameStoreUser(HttpUser):
    """Utilisateur simulé naviguant sur le catalogue GameStore."""
    wait_time = between(1, 3)

    @task(5)
    def consulter_catalogue(self):
        """Consulter la liste complète des jeux."""
        with self.client.get("/games", catch_response=True) as response:
            if response.status_code == 200:
                games = response.json()
                if len(games) == 0:
                    response.failure("Catalogue vide — inattendu")
            else:
                response.failure(f"Status inattendu : {response.status_code}")

    @task(3)
    def filtrer_par_genre(self):
        """Filtrer par genre."""
        genres = ["RPG", "Action", "Platformer", "Roguelike", "Sandbox", "FPS"]
        genre  = random.choice(genres)
        with self.client.get(
            f"/games?genre={genre}",
            name="/games?genre=[genre]",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Filtre genre échoué : {response.status_code}")

    @task(2)
    def consulter_jeu_individuel(self):
        """Consulter un jeu par son id."""
        game_id = random.randint(1, 20)
        with self.client.get(
            f"/games/{game_id}",
            name="/games/[id]",
            catch_response=True
        ) as response:
            if response.status_code not in (200, 404):
                response.failure(f"Status inattendu : {response.status_code}")
            else:
                response.success()


    @task(2)
    def health_check(self):
        """Health check."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                if response.json().get("status") != "ok":
                    response.failure("Health status != ok")
            else:
                response.failure(f"Health check échoué : {response.status_code}")

    @task(1)
    def consulter_stats(self):
        """Consulter les stats par genre — observez le temps de réponse."""
        with self.client.get("/games/stats", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Stats échouées : {response.status_code}")

    @task(1)
    def consulter_featured(self):
        """
        TODO — Tester /games/featured avec catch_response=True.
        Validez le status et le contenu de la réponse.
        Utilisez response.failure() si quelque chose ne correspond pas
        à ce que la documentation de l'endpoint promet.
        """
        with self.client.get("/games/featured", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Code d'echec : {response.status_code}")
            else:
                response.success()
        self.client.get("/games/featured", name="/games/featured")

    @task(1)
    def creer_puis_supprimer_jeu(self):
        """Scénario admin : créer un jeu puis le supprimer."""
        payload = {
            "title": f"Locust Test {random.randint(1000, 9999)}",
            "genre": "Action",
            "price": round(random.uniform(9.99, 69.99), 2),
            "stock": random.randint(10, 200),
        }
        with self.client.post("/games", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                game_id = response.json().get("id")
                if game_id:
                    self.client.delete(f"/games/{game_id}", name="/games/[id] DELETE")
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Création échouée : {response.status_code}")
