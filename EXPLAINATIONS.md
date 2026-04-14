# Documentation de mises en place des tests.

## Tests unitaires : 

### Correctif : 
- Dans le get_db() de app_gamestore.py ajout du code ci dessous pour initialiser la DB si elle n'existe pas, et correctif de fonction : 
```py
if not os.path.exists(DATABASE):
    init_db()
```
- Lors d'un test pour la suppression, j'ai constaté que le retour de l'endpoint en delete était en 200, je l'ai remit en 204.

### Tests
- Ajout de la librairie python typing pour typer proprement mes méthodes et fonctions.
- Ajouts de la fixture client pour utiliser un client Flask pour les requête HTTP sur l'API. Ajout d'un teardown pour cette fixture qui supprime toutes les parties afin que les tests soit indépendants les uns des autres. Supprimer l'entièreté de la base de jeu, puisque par principe, les tests doivent être isolé, et cette suppression ne doit avoir aucune conséquence sur le travail en parrallèle de l'équipe. ( Faire tourner les tests sous containers ( Test Containers ), cela permet l'isolation total et un environnement proche de la production. Pareil dans le CI, les tests tournent dans des environnement isolés. Car ici aucun container n'est mit en place pour l'exécution de tests ).

- Ajout d'une fixture qui renvoie le body nécessaire à la création d'un jeu, pour gagner en temps.

- D'abord, je met en place une méthode protégée interne dans une classe `TestingService` dont héritera les autres classes de test. Elle test le status ok, souvent demandé et renvoie le body de réponse. Cela permet plus de clareté : `_test_status_ok(client, url)`, et en lisibilité.
- Je rajoute une autre méthode protégée interne dans la classe `TestingService` qui permet de vérifier l'existence d'une clé et optionnelement sa valeur dans un dictionnaire. Encore une fois, cela apporte clareté, lisibilité.
- J'ajoute encore une méthode protégée interne qui permet l'ajout d'un jeu.

### Nouveaux tests :
**Stats :**
Cet endpoint n'était pas du tout testé. J'ai également retiré la classe `TestChoixLibres` par `TestGameStats` pour un nom plus explicite. 

### Notes : 
- J'ai remarqué ceci dans app_gamestore.py : 
```py
rows = db.execute( 

    f'SELECT * FROM games WHERE genre = ? ORDER BY {sort} {order}', 

    (genre,) 

).fetchall() 
```
Mettre les variables sort et order comme ceci rend le code sensible aux injections SQL puisque les variables sort et order sont récupéré deppuis l'URL, et sont définies par l'utilisateurs lors de la requête.

## /games/featured

- AJout des tests unitaires
- COrrectif : Ne renvoie que les jeu dont le prix et le stock sont supérieurs à 0. Cela a été détecté suite à des tests unitaires pour récupérer uniquement les jeux gratuit ou avec un stock positif.

## Locust

### Observations : 
J'ai lancé les tests locust, avec un objectif de 10 000 utilisateurs sur l'application, avec une montée de 40 utilisateurs par secondes.
Je m'apperçois qu'à partir de 1150 utilisateurs, le P95 ( donc 95% des requêtes ) est à 3 100 ms. A partir de ce seuil, le temps de réponse ne fait qu'augmenter.
J'ai maintenu ce test de charge pendant quelques minutes et les temps de réponses se sont prolongés jusqu'à 135 000 ms pour 8 400 utilisateurs.
J'en conclu donc que l'API a une capacité maximum de 1150 utiisateurs simultannés avant de saturer.

La route /games/featured précédemment corrigée a donc les mêmes statistiques que les autres routes avec un poid de 1.

Je note aussi que les routes testé avec un poid plus important ( donc plus de requêtes ) on un P95 plus élevé. Partant du principe que ces endpoints sont les plus touchés, un cache comme Redis pourrait être intéressant à intégrer afn de limiter le nombre d'appel à la base de données et réduire le temps de chargement et ainsi augmenter le seuil de saturation pour cet endpoint.

## Postman

### Ajouts :
- Je décide de rajouter le fait de filtrer par un genre qui existe et qui n'existe pas. Il faut s'assurer que si tel est le cas, l'API ne crash pas. Un filtre sur une liste est beaucoup utilisé, la preuve en est que l'endpoint avec un filtre sur la liste avait un poid de 3 sur les tests locust.
- Ensuite puisque la liste est l'élément le plus utilisé encore, je test le tri par ordre croissant et décroissant.
- Je rajoute aussi un test sur le temps de réponse ( < 500 ms sur la liste des jeux ) : Encore une fois, car feature primordiale
- CI : J'ai ajouté l'upload d'artefacts ( le report newman.html ) qui fournit le rapport de tests.

