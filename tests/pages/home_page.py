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
        self.game_list = page.locator('[data-testid=game-list]')
        self.game_count = page.locator('[data-testid=game-count]')
        self.add_btn = page.locator('[data-testid=add-game-btn]')
        self.search_inp = page.locator('[data-testid=search-input]')
        self.genre_sel = page.locator('[data-testid=genre-filter]')

    def navigate(self):
        """Naviguer vers la page d'accueil."""
        self.page.goto(BASE_URL)

    def get_game_cards(self):
        """Retourner le locator de toutes les cartes de jeux."""
        return self.game_list.locator('[data-testid=game-card]')

    def open_add_form(self):
        """Cliquer sur le bouton Ajouter un jeu."""
        self.add_btn.click()

    def search(self, query: str):
        """Taper une requête dans la barre de recherche."""
        self.search_inp.fill(query)

    def filter_genre(self, genre: str):
        """Sélectionner un genre dans le filtre déroulant."""
        self.genre_sel.select_option(genre)
