# NexusGame — Suite de Tests

> Projet final 2TES3 — Tests Avancés & Automatisation

## Présentation du projet

<!-- Décrivez le contexte du projet et l'API GameStore. -->

---

## Structure du repo

```
NexusGame/
├── app_gamestore.py
├── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── test_unit.py
│   ├── test_integration.py
│   ├── test_ui.py
│   ├── gamestore_collection.json
│   ├── locust_gamestore.py
│   └── pages/
│       ├── home_page.py
│       └── add_game_modal.py
└── .github/
    └── workflows/
        └── tests.yml
```

---

## Lancer les tests

```bash
# Installation
pip install -r requirements.txt
playwright install chromium
npm install -g newman newman-reporter-htmlextra
pip install locust

# Démarrer l'API
python app_gamestore.py

# Tests unitaires
pytest tests/test_unit.py -v --cov=app_gamestore --cov-report=html

# Tests d'intégration
pytest tests/test_integration.py -v -m integration

# Tests UI
pytest tests/test_ui.py -v --headed

# Collection Newman
newman run tests/gamestore_collection.json --env-var "base_url=http://localhost:5000" --reporters cli,htmlextra

# Tests de charge
locust -f tests/locust_gamestore.py --host=http://localhost:5000 --headless -u 20 -r 2 --run-time 30s
```

---

## Mes choix techniques

### Pyramide de tests adoptée

<!-- Quelle pyramide avez-vous choisie et pourquoi ? -->

### Pipeline CI vs local

<!-- Qu'est-ce qui tourne en CI, qu'est-ce qui reste en local, et pourquoi ? -->

### Mes choix libres

<!-- Pour chaque test libre : ce qu'il teste et pourquoi vous l'avez choisi. -->

---

## Investigation de l'API

<!-- Ce que vous avez observé en testant l'API.
     Comportements inattendus, hypothèses, ce que vos tests révèlent. -->

---

## Pipeline CI/CD

<!-- État de votre pipeline sur GitHub Actions. -->

---

## Ce que j'ai appris

<!-- Optionnel. -->
