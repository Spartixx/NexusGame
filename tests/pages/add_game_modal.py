"""
pages/add_game_modal.py — Page Object : modal d'ajout de jeu
==============================================================
Encapsule les interactions avec le formulaire d'ajout de jeu.
"""
from playwright.sync_api import Page


class AddGameModal:

    def __init__(self, page: Page):
        self.page = page

        # TODO — Définir les locators du formulaire.
        #
        # self.modal      = page.locator("...")
        # self.input_title  = page.locator("...")
        # self.input_genre  = page.locator("...")
        # self.input_price  = page.locator("...")
        # self.submit_btn   = page.locator("...")
        # self.cancel_btn   = page.locator("...")

    def fill_and_submit(self, title: str, genre: str, price: float):
        """
        TODO — Remplir le formulaire et soumettre.
        1. Remplir input_title avec title
        2. Remplir input_genre avec genre
        3. Remplir input_price avec str(price)
        4. Cliquer sur submit_btn
        """
        pass

    def cancel(self):
        """TODO — Cliquer sur le bouton Annuler."""
        pass

    def is_visible(self) -> bool:
        """TODO — Retourner True si le modal est visible."""
        pass
