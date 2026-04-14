#!/usr/bin/env python3
"""
API GameStore — NexusGame Studio
Flask + SQLite · Catalogue de jeux vidéo
"""

from flask import Flask, request, jsonify, g, render_template_string, abort, current_app
import sqlite3
import os

# ── Config ──────────────────────────────────────────────────────────────────
DATABASE = os.path.join(os.path.dirname(__file__), 'gamestore.db')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ── Base de données ──────────────────────────────────────────────────────────

def get_db():
    """Connexion SQLite partagée dans le contexte de la requête."""
    if not os.path.exists(DATABASE):
        init_db()

    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """Initialise le schéma et insère les données de démo."""
    target = db_path or DATABASE
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row

    db.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT    NOT NULL,
            genre     TEXT    NOT NULL,
            price     REAL    NOT NULL,
            rating    REAL    NOT NULL DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
            stock     INTEGER NOT NULL DEFAULT 0,
            publisher TEXT,
            year      INTEGER,
            CONSTRAINT unique_title UNIQUE (title)
        )
    ''')

    seed = [
        ('The Legend of Zelda: Tears of the Kingdom', 'RPG',        59.99, 4.9, 240, 'Nintendo',       2023),
        ('Elden Ring',                                 'RPG',        49.99, 4.8,  85, 'Bandai Namco',   2022),
        ('Cyberpunk 2077',                             'RPG',        39.99, 4.5, 130, 'CD Projekt Red', 2020),
        ('God of War Ragnarök',                        'Action',     59.99, 4.9,  60, 'Sony Santa Monica', 2022),
        ('Spider-Man 2',                               'Action',     69.99, 4.7,  50, 'Insomniac',      2023),
        ('Hollow Knight',                              'Platformer',  14.99, 4.9, 500, 'Team Cherry',   2017),
        ('Celeste',                                    'Platformer',  19.99, 4.8, 320, 'Maddy Thorson', 2018),
        ('Ori and the Will of the Wisps',              'Platformer',  24.99, 4.7, 180, 'Moon Studios',  2020),
        ('Hades',                                      'Roguelike',   24.99, 4.9, 420, 'Supergiant',    2020),
        ('Dead Cells',                                 'Roguelike',   19.99, 4.7, 350, 'Motion Twin',   2018),
        ('Stardew Valley',                             'Simulation',  13.99, 4.9, 800, 'ConcernedApe',  2016),
        ('Cities: Skylines II',                        'Simulation',  49.99, 3.8,  40, 'Colossal Order', 2023),
        ('Overwatch 2',                                'FPS',          0.00, 3.5, 999, 'Blizzard',      2022),
        ('Counter-Strike 2',                           'FPS',          0.00, 4.0, 999, 'Valve',         2023),
        ('Minecraft',                                  'Sandbox',     26.99, 4.8, 999, 'Mojang',        2011),
        ('Terraria',                                   'Sandbox',      9.99, 4.9, 600, 'Re-Logic',      2011),
        ('Among Us',                                   'Party',        5.00, 4.0, 400, 'Innersloth',    2018),
        ('Fall Guys',                                  'Party',        0.00, 4.1, 300, 'Mediatonic',    2020),
        ('FIFA 24',                                    'Sport',       69.99, 3.9,  75, 'EA Sports',     2023),
        ('NBA 2K24',                                   'Sport',       59.99, 3.7,  55, '2K Games',      2023),
    ]

    db.executemany(
        'INSERT OR IGNORE INTO games (title, genre, price, rating, stock, publisher, year) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        seed
    )
    db.commit()
    db.close()
    print(f'[GameStore] DB initialisée : {target}')


# ── Utilitaires ──────────────────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row) if row else None

def validate_game(data, partial=False):
    """Valide les champs d'un jeu. partial=True pour les PUT."""
    errors = []
    if not partial or 'title' in data:
        if not data.get('title'):
            errors.append('title est obligatoire et ne peut pas être vide')
    if not partial or 'genre' in data:
        if not data.get('genre') or not str(data['genre']).strip():
            errors.append('genre est obligatoire')
    if not partial or 'price' in data:
        try:
            price = float(data.get('price', -1))
            if price < 0:
                errors.append('price doit être >= 0')
        except (TypeError, ValueError):
            errors.append('price doit être un nombre')
    if 'rating' in data:
        try:
            rating = float(data['rating'])
            if not partial and not 0 <= rating <= 5:
                errors.append('rating doit être entre 0 et 5')
        except (TypeError, ValueError):
            errors.append('rating doit être un nombre entre 0 et 5')
    if 'stock' in data:
        try:
            stock = int(data['stock'])
            if not partial and stock < 0:
                errors.append('stock doit être >= 0')
        except (TypeError, ValueError):
            errors.append('stock doit être un entier >= 0')
    return errors


# ── Routes API ───────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    """Health check pour Locust et les tests de perf."""
    return jsonify({'status': 'ok', 'service': 'GameStore API'}), 200


@app.route('/games', methods=['GET'])
def list_games():
    """Liste tous les jeux. Filtre optionnel : ?genre=RPG&sort=price"""
    db = get_db()
    genre  = request.args.get('genre')
    sort   = request.args.get('sort', 'id')
    order  = request.args.get('order', 'asc').upper()

    allowed_sort  = {'id', 'title', 'price', 'rating', 'genre', 'year'}
    allowed_order = {'ASC', 'DESC'}
    if sort not in allowed_sort:
        sort = 'title'
    if order not in allowed_order:
        order = 'ASC'

    if genre:
        rows = db.execute(
            f'SELECT * FROM games WHERE genre = ? ORDER BY {sort} {order}',
            (genre,)
        ).fetchall()
    else:
        rows = db.execute(
            f'SELECT * FROM games ORDER BY {sort} {order}'
        ).fetchall()

    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route('/games', methods=['POST'])
def create_game():
    """Crée un nouveau jeu. Body JSON requis avec title, genre, price."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Body JSON requis'}), 400

    errors = validate_game(data)
    if errors:
        return jsonify({'error': 'Données invalides', 'details': errors}), 400

    db = get_db()
    try:
        stock_val = 999 if float(data['price']) == 0 else int(data.get('stock', 0))
        cursor = db.execute(
            'INSERT INTO games (title, genre, price, rating, stock, publisher, year) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                str(data['title']),
                str(data['genre']).strip(),
                float(data['price']),
                float(data.get('rating', 0)),
                stock_val,
                data.get('publisher'),
                data.get('year'),
            )
        )
        db.commit()
        new_id = cursor.lastrowid
        row = db.execute('SELECT * FROM games WHERE id = ?', (new_id,)).fetchone()
        return jsonify(row_to_dict(row)), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': f'Un jeu avec le titre "{data["title"]}" existe déjà'}), 409


@app.route('/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """
    Récupère un jeu par son ID.

    Retourne 200 avec les données du jeu, incluant un champ "rank".
    Retourne 404 si le jeu n'existe pas.
    """
    db = get_db()
    row = db.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    if row is None:
        return jsonify({'error': f'Jeu {game_id} introuvable'}), 404
    all_ids = [r['id'] for r in db.execute('SELECT id FROM games ORDER BY id ASC').fetchall()]
    game_data = row_to_dict(row)
    game_data['rank'] = game_id
    return jsonify(game_data), 200


@app.route('/games/<int:game_id>', methods=['PUT'])
def update_game(game_id):
    """Met à jour un jeu (modification partielle acceptée)."""
    db = get_db()
    row = db.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    if row is None:
        return jsonify({'error': f'Jeu {game_id} introuvable'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Body JSON requis'}), 400

    errors = validate_game(data, partial=True)
    if errors:
        return jsonify({'error': 'Données invalides', 'details': errors}), 400

    fields = {k: v for k, v in data.items()
              if k in ('title', 'genre', 'price', 'rating', 'stock', 'publisher', 'year')}
    if not fields:
        return jsonify({'error': 'Aucun champ modifiable fourni'}), 400

    set_clause = ', '.join(f'{k} = ?' for k in fields)
    values = list(fields.values()) + [game_id]
    try:
        db.execute(f'UPDATE games SET {set_clause} WHERE id = ?', values)
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': f'Un jeu avec ce titre existe déjà'}), 409

    updated = db.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    return jsonify(row_to_dict(updated)), 200


@app.route('/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    """
    Supprime un jeu par son ID.

    Retourne 204 No Content si la suppression a réussi.
    Retourne 404 si le jeu n'existe pas.
    """
    db = get_db()
    row = db.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    if row is None:
        return jsonify({'error': f'Jeu {game_id} introuvable'}), 404
    db.execute('DELETE FROM games WHERE id = ?', (game_id,))
    db.commit()
    return jsonify({'deleted': True, 'id': game_id}), 204


# ── Endpoints de statistiques et recherche ──────────────────────────────────

def _calculate_stats(games):
    """Calcule des statistiques par genre."""
    stats = {}
    for game in games:
        genre = game['genre']

        genre_games = [g for g in games if g['genre'] == genre]
        prices      = [g['price']  for g in genre_games]
        ratings     = [g['rating'] for g in genre_games]
        stocks      = [g['stock']  for g in genre_games]
        stats[genre] = {
            'count':       len(set(g['genre'] for g in genre_games)),
            'avg_price':   round(sum(prices)  / len(prices),  2),
            'avg_rating':  round(sum(ratings) / len(ratings), 2),
            'total_stock': sum(stocks),
            'min_price':   min(prices),
            'max_price':   max(prices),
        }
    return stats


@app.route('/games/stats')
def games_stats():
    """
    Statistiques agrégées par genre.

    Réponse : {
        "total_games": N,
        "genres": {
            "RPG": {
                "count": N,        # nombre de jeux dans ce genre
                "avg_price": X.XX,
                "avg_rating": X.XX,
                "total_stock": N,
                "min_price": X.XX,
                "max_price": X.XX
            }, ...
        }
    }
    """
    db = get_db()
    all_games = [dict(r) for r in db.execute('SELECT * FROM games').fetchall()]
    stats = _calculate_stats(all_games)

    return jsonify({
        'total_games': len(all_games),
        'genres':      stats,
    }), 200


@app.route('/games/search')
def search_games():
    """Recherche de jeux par titre et/ou genre.
    Paramètres : ?q=zelda  ou  ?genre=RPG  ou  ?q=zelda&genre=RPG
    """
    q     = request.args.get('q', '').strip()
    genre = request.args.get('genre', '').strip()

    db = get_db()
    all_games = [dict(r) for r in db.execute('SELECT * FROM games').fetchall()]
    results = all_games
    if q:
        results = [g for g in results if q in g['title']]
    if genre:
        results = [g for g in results if g['genre'].lower() == genre.lower()]

    return jsonify({'count': len(results), 'results': results}), 200


@app.route('/genres')
def list_genres():
    """Liste les genres disponibles (pour le filtre du front-end)."""
    db = get_db()
    rows = db.execute('SELECT DISTINCT genre FROM games ORDER BY genre').fetchall()
    return jsonify([r['genre'] for r in rows]), 200


# ── Interface HTML ────────────────────────────────────────────────────────────

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GameStore</title>
  <style>
    :root {
      --bg:       #0D1B2A;
      --surface:  #132F4C;
      --surface2: #1A3A5C;
      --blue:     #1E88E5;
      --blue-lt:  #64B5F6;
      --green:    #43A047;
      --red:      #E53935;
      --orange:   #F57C00;
      --text:     #E8F0FE;
      --muted:    #90A4AE;
      --radius:   8px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }

    /* ── Header ── */
    header {
      background: var(--surface);
      border-bottom: 2px solid var(--blue);
      padding: 0 2rem;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .logo {
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--blue-lt);
      letter-spacing: -0.5px;
    }
    .logo span { color: var(--orange); }
    #game-count {
      font-size: 0.85rem;
      color: var(--muted);
      background: var(--surface2);
      padding: 4px 12px;
      border-radius: 20px;
    }

    /* ── Layout ── */
    .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    /* ── Toolbar ── */
    .toolbar {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
      align-items: center;
    }
    .search-box {
      flex: 1;
      min-width: 200px;
      background: var(--surface);
      border: 1px solid var(--surface2);
      border-radius: var(--radius);
      padding: 0.5rem 1rem;
      color: var(--text);
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .search-box:focus { border-color: var(--blue); }
    .genre-filter {
      background: var(--surface);
      border: 1px solid var(--surface2);
      border-radius: var(--radius);
      padding: 0.5rem 0.75rem;
      color: var(--text);
      font-size: 0.9rem;
      cursor: pointer;
      outline: none;
    }
    .btn-add {
      background: var(--blue);
      color: white;
      border: none;
      border-radius: var(--radius);
      padding: 0.5rem 1.2rem;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
      white-space: nowrap;
    }
    .btn-add:hover { background: var(--blue-lt); color: var(--bg); }

    /* ── Game Grid ── */
    #game-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }
    .game-card {
      background: var(--surface);
      border: 1px solid var(--surface2);
      border-radius: var(--radius);
      padding: 1rem 1.1rem;
      transition: transform 0.15s, border-color 0.15s;
      position: relative;
    }
    .game-card:hover { transform: translateY(-2px); border-color: var(--blue); }
    .game-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: var(--text);
      line-height: 1.3;
    }
    .game-meta {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.75rem;
    }
    .badge {
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 20px;
      font-weight: 600;
    }
    .badge-genre  { background: #1E88E520; color: var(--blue-lt); border: 1px solid var(--blue); }
    .badge-year   { background: transparent; color: var(--muted); border: 1px solid var(--surface2); }
    .game-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.5rem;
    }
    .game-price {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--green);
    }
    .game-price.free { color: var(--blue-lt); }
    .rating {
      font-size: 0.8rem;
      color: var(--orange);
    }
    .stock-info {
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 0.25rem;
    }
    .btn-delete {
      position: absolute;
      top: 0.6rem;
      right: 0.6rem;
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 1.1rem;
      line-height: 1;
      padding: 2px 5px;
      border-radius: 4px;
      transition: color 0.15s, background 0.15s;
    }
    .btn-delete:hover { color: var(--red); background: #E5393515; }

    /* ── Add Form Modal ── */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: #00000088;
      z-index: 100;
      align-items: center;
      justify-content: center;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: var(--surface);
      border: 1px solid var(--blue);
      border-radius: 12px;
      padding: 1.75rem 2rem;
      width: 440px;
      max-width: 95vw;
    }
    .modal h2 {
      font-size: 1.2rem;
      margin-bottom: 1.25rem;
      color: var(--blue-lt);
    }
    .form-row {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 0.85rem;
      flex-wrap: wrap;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 120px;
    }
    .form-group label {
      font-size: 0.8rem;
      color: var(--muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .form-group input, .form-group select {
      background: var(--bg);
      border: 1px solid var(--surface2);
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      color: var(--text);
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
      width: 100%;
    }
    .form-group input:focus, .form-group select:focus { border-color: var(--blue); }
    .form-actions {
      display: flex;
      gap: 0.75rem;
      justify-content: flex-end;
      margin-top: 1rem;
    }
    .btn-cancel {
      background: transparent;
      border: 1px solid var(--muted);
      color: var(--muted);
      border-radius: var(--radius);
      padding: 0.5rem 1.1rem;
      cursor: pointer;
      font-size: 0.9rem;
    }
    .btn-submit {
      background: var(--green);
      color: white;
      border: none;
      border-radius: var(--radius);
      padding: 0.5rem 1.4rem;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    .btn-submit:hover { opacity: 0.85; }

    /* ── Toast ── */
    #toast {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: var(--surface);
      border: 1px solid var(--green);
      color: var(--text);
      padding: 0.75rem 1.25rem;
      border-radius: var(--radius);
      font-size: 0.9rem;
      opacity: 0;
      transform: translateY(12px);
      transition: opacity 0.25s, transform 0.25s;
      z-index: 200;
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.error { border-color: var(--red); }

    /* ── Empty state ── */
    .empty-state {
      grid-column: 1/-1;
      text-align: center;
      padding: 3rem 1rem;
      color: var(--muted);
    }
    .empty-state p { font-size: 1.1rem; margin-top: 0.5rem; }
  </style>
</head>
<body>

<header>
  <div class="logo">Game<span>Store</span></div>
  <div data-testid="game-count" id="game-count">Chargement…</div>
</header>

<div class="container">
  <div class="toolbar">
    <input
      class="search-box"
      type="text"
      placeholder="Rechercher un jeu…"
      data-testid="search-input"
      id="search-input"
      oninput="filterGames()"
    >
    <select
      class="genre-filter"
      data-testid="genre-filter"
      id="genre-filter"
      onchange="filterGames()"
    >
      <option value="">Tous les genres</option>
    </select>
    <button
      class="btn-add"
      data-testid="add-game-btn"
      onclick="openModal()"
    >+ Ajouter un jeu</button>
  </div>

  <div id="game-list" data-testid="game-list">
    <div class="empty-state"><p>Chargement des jeux…</p></div>
  </div>
</div>

<!-- Modal ajout jeu -->
<div class="modal-overlay" id="modal-overlay" data-testid="add-game-modal">
  <div class="modal">
    <h2>Ajouter un jeu</h2>
    <form data-testid="add-game-form" onsubmit="submitGame(event)">
      <div class="form-row">
        <div class="form-group" style="flex:2">
          <label>Titre *</label>
          <input
            type="text"
            id="f-title"
            data-testid="input-title"
            placeholder="Ex: Elden Ring"
            required
          >
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Genre *</label>
          <input
            type="text"
            id="f-genre"
            data-testid="input-genre"
            placeholder="RPG, Action…"
            required
          >
        </div>
        <div class="form-group">
          <label>Prix (€) *</label>
          <input
            type="number"
            id="f-price"
            data-testid="input-price"
            placeholder="29.99"
            min="0"
            step="0.01"
            required
          >
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Note (0-5)</label>
          <input
            type="number"
            id="f-rating"
            data-testid="input-rating"
            placeholder="4.5"
            min="0"
            max="5"
            step="0.1"
          >
        </div>
        <div class="form-group">
          <label>Stock</label>
          <input
            type="number"
            id="f-stock"
            data-testid="input-stock"
            placeholder="100"
            min="0"
          >
        </div>
        <div class="form-group">
          <label>Année</label>
          <input
            type="number"
            id="f-year"
            data-testid="input-year"
            placeholder="2024"
            min="1970"
            max="2030"
          >
        </div>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-cancel" onclick="closeModal()" data-testid="cancel-btn">Annuler</button>
        <button type="submit" class="btn-submit" data-testid="submit-btn">Ajouter</button>
      </div>
    </form>
  </div>
</div>

<div id="toast"></div>

<script>
  let allGames = [];

  // ── Chargement initial ──────────────────────────────────────────────
  async function loadGames() {
    try {
      const res  = await fetch('/games');
      allGames   = await res.json();
      renderGames(allGames);
      loadGenres();
    } catch (err) {
      showToast('Erreur de chargement des jeux', true);
    }
  }

  async function loadGenres() {
    try {
      const res    = await fetch('/genres');
      const genres = await res.json();
      const sel    = document.getElementById('genre-filter');
      genres.forEach(g => {
        const opt  = document.createElement('option');
        opt.value  = g;
        opt.textContent = g;
        sel.appendChild(opt);
      });
    } catch (_) {}
  }

  // ── Rendu ────────────────────────────────────────────────────────────
  function renderGames(games) {
    const container = document.getElementById('game-list');
    const counter   = document.getElementById('game-count');
    counter.textContent = `${games.length} jeu${games.length !== 1 ? 'x' : ''}`;

    if (games.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div style="font-size:2.5rem">🎮</div>
          <p>Aucun jeu trouvé</p>
        </div>`;
      return;
    }

    container.innerHTML = games.map(g => `
      <div class="game-card" data-testid="game-card" data-id="${g.id}">
        <button
          class="btn-delete"
          data-testid="delete-btn-${g.id}"
          onclick="deleteGame(${g.id}, this)"
          title="Supprimer"
        >✕</button>
        <div class="game-title" data-testid="game-title">${escHtml(g.title)}</div>
        <div class="game-meta">
          <span class="badge badge-genre" data-testid="game-genre">${escHtml(g.genre)}</span>
          ${g.year ? `<span class="badge badge-year">${g.year}</span>` : ''}
          ${g.publisher ? `<span class="badge badge-year">${escHtml(g.publisher)}</span>` : ''}
        </div>
        <div class="game-footer">
          <div>
            <div class="game-price ${g.price === 0 ? 'free' : ''}" data-testid="game-price">
              ${g.price === 0 ? 'Gratuit' : g.price.toFixed(2) + ' €'}
            </div>
            <div class="stock-info">Stock : ${g.stock}</div>
          </div>
          <div class="rating" data-testid="game-rating">
            ${'★'.repeat(Math.round(g.rating))}${'☆'.repeat(5 - Math.round(g.rating))}
            <span style="color:var(--muted);font-size:0.7rem"> ${g.rating}</span>
          </div>
        </div>
      </div>
    `).join('');
  }

  // ── Filtrage ─────────────────────────────────────────────────────────
  function filterGames() {
    const q     = document.getElementById('search-input').value.toLowerCase();
    const genre = document.getElementById('genre-filter').value;
    const filtered = allGames.filter(g =>
      (!q     || g.title.toLowerCase().includes(q)) &&
      (!genre || g.genre === genre)
    );
    renderGames(filtered);
  }

  // ── Ajout ─────────────────────────────────────────────────────────────
  function openModal()  { document.getElementById('modal-overlay').classList.add('open'); }
  function closeModal() {
    document.getElementById('modal-overlay').classList.remove('open');
    document.querySelector('[data-testid="add-game-form"]').reset();
  }

  async function submitGame(e) {
    e.preventDefault();
    const payload = {
      title:  document.getElementById('f-title').value.trim(),
      genre:  document.getElementById('f-genre').value.trim(),
      price:  parseFloat(document.getElementById('f-price').value),
    };
    const rating = document.getElementById('f-rating').value;
    const stock  = document.getElementById('f-stock').value;
    const year   = document.getElementById('f-year').value;
    if (rating) payload.rating = parseFloat(rating);
    if (stock)  payload.stock  = parseInt(stock);
    if (year)   payload.year   = parseInt(year);

    try {
      const res = await fetch('/games', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || 'Erreur lors de l\'ajout', true);
        return;
      }
      allGames.unshift(data);
      closeModal();
      filterGames();
      showToast(`"${data.title}" ajouté avec succès !`);
    } catch (err) {
      showToast('Erreur réseau', true);
    }
  }

  // ── Suppression ───────────────────────────────────────────────────────
  async function deleteGame(id, btn) {
    const card  = btn.closest('[data-testid="game-card"]');
    const title = card.querySelector('[data-testid="game-title"]').textContent;

    try {
      const res = await fetch(`/games/${id}`, { method: 'DELETE' });
      if (res.status === 204 || res.status === 200) {
        allGames   = allGames.filter(g => g.id !== id);
        card.style.opacity    = '0';
        card.style.transition = 'opacity 0.2s';
        setTimeout(() => { filterGames(); }, 200);
        showToast(`"${title}" supprimé`);
      } else {
        showToast('Erreur lors de la suppression', true);
      }
    } catch (err) {
      showToast('Erreur réseau', true);
    }
  }

  // ── Toast ──────────────────────────────────────────────────────────────
  let toastTimer;
  function showToast(msg, isError = false) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className   = 'show' + (isError ? ' error' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.className = ''; }, 3000);
  }

  // ── Utilitaire ─────────────────────────────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Fermer le modal en cliquant à côté ──────────────────────────────
  document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });

  loadGames();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)



# ── Endpoint featured ────────────────────────────────────────────────────────
@app.route('/games/featured')
def featured_games():
    """
    Retourne les N jeux mis en avant.

    Comportement attendu :
    - Triés par rating décroissant (le mieux noté en premier)
    - Uniquement les jeux en stock (stock > 0)
    - Uniquement les jeux payants (price > 0)
    - Paramètre optionnel : ?limit=N (défaut 5, max 10)

    Réponse : {"count": N, "featured": [...]}
    """
    db    = get_db()
    limit = request.args.get('limit', 5)
    try:
        limit = int(limit)
        if limit < 1:  limit = 5
        if limit > 10: limit = 10
    except (ValueError, TypeError):
        limit = 5

    rows  = db.execute('SELECT * FROM games WHERE stock > 0 AND price > 0 ORDER BY rating ASC').fetchall()
    games = [dict(r) for r in rows]
    featured = games[:limit]

    return jsonify({'count': len(featured), 'featured': featured}), 200

# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        print(f'[GameStore] DB existante : {DATABASE}')
    print('[GameStore] → http://localhost:5000')
    print('[GameStore] → http://localhost:5000/games (API JSON)')
    app.run(debug=True, host='0.0.0.0', port=5000)
