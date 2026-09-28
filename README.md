# Le Royaume des Proies

Simulation d'un écosystème virtuel avec des agents (humains et poulets) évoluant dans un environnement dynamique : cycle jour/nuit, saisons, météo, propagation du feu, montée des eaux, maladies et reproduction.

Projet réalisé dans le cadre du cours **LU2IN013** (Sorbonne Université) par Angela Vergara et Maryam Leclerc.

## Installation

```bash
pip install pygame numpy noise
```

## Lancer la simulation

```bash
python le_royaume_des_proies.py
```

## Contrôles

| Touche | Action |
|---|---|
| S | Changer de saison |
| F | Mettre le feu à un arbre |
| Flèches | Déplacer la caméra |
| Z / Shift+Z | Zoomer / dézoomer |
| D | Changer la vitesse de simulation |
| R | Réinitialiser la caméra (Shift+R : relancer la simulation) |
| Échap | Quitter |

## Fonctionnalités

**Agents**
- Deux types : humains et poulets, avec vision (Moore / Von Neumann), déplacement, famine, âge, maladie et guérison
- Priorités comportementales : se nourrir, fuir un prédateur, sinon déplacement aléatoire
- Reproduction, prédation (poulets/humains) et abattage d'arbres par les humains

**Environnement**
- Génération procédurale du terrain (bruit de Perlin)
- Cycle temporel complet : secondes → heures → jours → mois, avec cycle jour/nuit et saisons (pluie/sèche)
- Température dynamique influencée par la déforestation et la reforestation
- Régénération de l'herbe, des arbres et des montagnes
- Feux de forêt avec propagation, fonte/gel de l'eau de montagne, montée des eaux en saison de pluie

**Visualisation**
- Rendu en temps réel avec Pygame
- Graphiques de suivi (évolution des arbres, climat, modèles SIR pour les maladies chez les humains et les poulets)

## Aperçu

Voir le dossier `RAPPORTS/` pour le rapport complet avec captures d'écran et graphiques d'évolution du système.

## Contribution

Projet de groupe (2 personnes). Ma contribution portait sur [à compléter : par exemple "la logique des agents et le système de maladie/guérison" ou "l'environnement et les aléas naturels"].

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
