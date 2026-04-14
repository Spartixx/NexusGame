"""
pages/home_page.py — Page Object : page d'accueil GameStore
=============================================================
Centralise tous les sélecteurs et actions de la page principale.
Les tests ne doivent JAMAIS écrire de sélecteur directement —
tout passe par cette classe.
"""
from playwright.sync_api import Page

BASE_URL = "http://localhost:5000"


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # TODO — Définir les locators pour chaque élément interactif.
        # Utiliser les data-testid définis dans l'API GameStore.
        #
        # self.game_list  = page.locator("...")
        # self.game_count = page.locator("...")
        # self.add_btn    = page.locator("...")
        # self.search_inp = page.locator("...")
        # self.genre_sel  = page.locator("...")

    def navigate(self):
        """Naviguer vers la page d'accueil."""
        # TODO
        pass

    def get_game_cards(self):
        """Retourner le locator de toutes les cartes de jeux."""
        # TODO
        pass

    def open_add_form(self):
        """Cliquer sur le bouton Ajouter un jeu."""
        # TODO
        pass

    def search(self, query: str):
        """Taper une requête dans la barre de recherche."""
        # TODO
        pass

    def filter_genre(self, genre: str):
        """Sélectionner un genre dans le filtre déroulant."""
        # TODO
        pass
