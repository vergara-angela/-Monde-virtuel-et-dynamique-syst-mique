"""import opensimplex
import random
import numpy as np

#Alternative à pnoise2
gen = opensimplex.OpenSimplex(seed=70) 
def pnoise2(x, y, octaves=1, persistence=0.5, lacunarity=2.0, **kwargs):
    value = 0
    amplitude = 1
    frequency = 1
    max_value = 0  # Pour normaliser proprement
    
    for _ in range(octaves):
        value += gen.noise2(x * frequency, y * frequency) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= lacunarity
    
    # On divise par max_value pour être SUR que le résultat est entre -1 et 1
    # Ça évitera de générer des index comme 32 plus tard
    return value / max_value"""


import random
import numpy as np
from noise import pnoise2

try:
    from numba import njit
except ImportError:
    print ("[WARNING] Numba not available.")
    def njit(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper

import calipsolib
from calipsolib import Agent

# =-=-= simulation parameters

params = {
    "density": 0.60,
    "seed_value": 30,

    #Humain
    "density_humain" : 0.01,
    "p_mouv_infect_humain": 0.6,
    "p_repro_humain": 0.00018,
    "proba_malade_humain": 0.05,
    "maxguerison_humain": 6,
    "dureedevie_humain": 4,
    "maxfamine_humain":1,
    "contagion_humain": 0.03,

    #chicken
    "density_chicken" : 0.006,
    "p_mouv_infect_chicken":0.5,
    "p_repro_chicken": 0.0004,
    "proba_malade_chicken": 0.009,
    "maxguerison_chicken": 3,
    "dureedevie_chicken":2,
    "maxfamine_chicken":1,

    "nouveaux_nes": [],

    #Vitesse déplacement agents
    "vitesse_deplacement_mont": 0.05, 

    #Arbre
    "dict_coupe_bois": {},
    "planter_arbre": 0.07,
    "p_tree": 0.0001, #un arbre spawn si herbe

    #Systeme de temps:
    "mois" : 1, 
    "jour" : 1, 
    "secondes" : 1,
    "heure" : 20,
    "heure_world" : 1, 

    "jour/nuit" : 1, #1 = jour, 0 = nuit
    "saison" : 1, #1 = saison séche, 0 = saison de pluie

    "dict_mois" : { 1 : "octobre",
                   2 : "novembre",
                   3 : "decembre",
                   4 : "janvier",
                   5 : "fevrier",
                   6 : "mars",
                   7 : "avril",
                   8 : "mai",
                   9 : "juin",
                   10 : "juillet",
                   11 : "aout",
                   12 : "septembre"},

    "dict_jour" : { 1 : "Lundi",
                   2 : "Mardi",
                   3 : "Mercredi", 
                    4 : "Jeudi", 
                    5 : "Vendredi", 
                    6 : "Samedi",
                    7 : "Dimanche" },

    "temperature_base" : 0,
    "temperature" : 0,
    "tempnuit" : True,
    "tempjour" : False,

    "temperature_moy" : 0,
    "compteur_moy_temp" : 0,

    "affichage" :" ",

    #catastrophe naturelle
    "p_fonte" : 0.2,
    "p_ecoulement" : 0.5,
    "p_ecoulement_mouv": 0.5,
    "p_absorption" : 0.2,
    "p_meau_mouv" : 0.5,
    "p_fire" : 0,

    #régéneration 
    "regen_dry_grass" : {},
    "p_regen" : 0.3,

    "p_regen_mont" : 0.1,

    "tree":6,
    "firetree":9
}

# =-=-= Defining cell types

SEA = 0
SAND = 1
GRASS = 2
FIRE = 3
MONT1 = 4
MONT2 = 5

TREE = 6
FLOWER = 7
ROCK = 8

FIRETREE = 9
WATER = 10
TRONC = 11

PREY_TRAIL = 12
PREDATOR_TRAIL = 13

MONT2_WATER = 14

TEST = 15

MONT1LEV2 = 16
MONT1LEV3 = 17

DRY_GRASS = 18


colors_ca = {
    SEA: (0, 0, 139),
    SAND : (194, 178, 128),
    GRASS:  (40, 110, 35),
    DRY_GRASS: (120, 135, 70),

    MONT1: (128, 128, 128),
    MONT2: (230, 235, 245),
    MONT2_WATER : (255, 0, 0),
    TEST : (255, 165, 0),
    MONT1LEV2: (180, 180, 180),
    MONT1LEV3: (200, 200, 200),

    FIRETREE :  (40, 110, 35),
    TRONC: (40, 110, 35),
    WATER: (0, 0, 139),

    PREY_TRAIL: (224, 224, 255),
    PREDATOR_TRAIL:  (255, 224, 224),

    TREE:  (40, 110, 35), #herbe en dessous 
    FLOWER:  (40, 110, 35), 
    ROCK:  (40, 110, 35)
}

image_ca = {
    TREE : "image/Tree.png",
    FLOWER : "image/Flower.png",
    FIRETREE : "image/FireTree.png",
    TRONC : "image/Tronc.png",
    ROCK : "image/Rock.png"
}

# =-=-= user-defined cellular automata

def init_simulation(params):
    seed_value = params["seed_value"]
    random.seed(seed_value) 

    density = params["density"]
    dx = params["dx"]
    dy = params["dy"]

    grid = np.zeros((dx, dy), dtype=np.uint8)
    newgrid = np.empty((dx, dy), dtype=np.uint8)
    it_grid = np.zeros((dx, dy), dtype=np.uint8) #Grille qui compte le nb de fois où les agents marchent sur une case (pour l'herbre qui s'assèche)

    params["nouveaux_nes"] = []

    # Paramètres Perlin
    scale = 25.0       # zoom sur le bruit (plus grand = plus lisse, 1 = rond)
    octaves = 10        # nombre de couches de détails
    persistence = 0.5  # importance des petits détails
    lacunarity = 2.0   # vitesse d'augmentation des détails, frequence des details

    cx, cy = dx // 2, dy // 2 #coord centre
    max_dist = ((cx)**2 + (cy)**2) ** 0.5 #rayon

    for x in range(dx):
        for y in range(dy):
            # Distance au centre pour l'effet île
            dist = ((x - cx)**2 + (y - cy)**2) ** 0.5 #distance de la cellule acutel et le centre
            island_factor = max(0, 1- dist / max_dist) #dist positif, normaliser et inverser

            # Bruit Perlin
            nx = x / scale #les coordonnées avancent doucement, bruit changent peu entre chaque cellule (1 : 0, 1, 2, 100 : 0.1, 0.2, 0.3)
            ny = y / scale
            altitude = pnoise2(nx, ny, octaves=octaves, persistence=persistence,
                               lacunarity=lacunarity, repeatx=dx, repeaty=dy, base=seed_value) #nombre entre -1, +1
            altitude = (altitude + 1) / 2 #normalisation entre 0 et 1 (+1 : 0-2, //2 : 0-1)
            altitude *= island_factor

            # Définir type de cellule
            if altitude < 0.3:
                grid[x, y] = SEA        
            elif altitude < 0.31:
                grid[x, y] = SAND
            elif altitude < 0.4:
                grid[x, y] = GRASS
            elif altitude < 0.45:
                grid[x, y] = MONT1
            else :
                grid[x, y] = MONT2


    # Placer quelques arbres au centre et aléatoirement
    for x in range(dx):
        for y in range(dy):
            if grid[x, y] == GRASS:
                rnd = random.random()
                if rnd < 0.01:
                    grid[x, y] = ROCK
                elif rnd < 0.02:
                    grid[x, y] = FLOWER
                elif rnd < 0.3:
                    grid[x, y] = TREE
            
    sol = np.copy(grid) #jamais modifié
                #grid[x, y] = TREE

    return grid, newgrid, sol, it_grid

#@njit(cache=True)
def ca_step(grid, newgrid, sol, it_grid, agents):
    dx, dy = grid.shape

    #Systeme jour/nuit :
    if params["heure"] >= 14:
        params["jour/nuit"] = 0  # nuit à partir de 14h (heure jeu)
    if params["heure"] >= 24 or params["heure"] == 1:
        params["jour/nuit"] = 1  # jour le matin

    if (params["jour/nuit"] == 0):
        j_n = "NUIT"
    else :
        j_n = "JOUR"

    #Systeme de saison :
    if (params["dict_mois"][params["mois"]] == "juin"):
        params["saison"] = 0
    if (params["dict_mois"][params["mois"]] == "octobre"):
        params["saison"] = 1

    if (params["saison"] == 0):
        s ="Saison de pluie"
    else :
        s ="Saison de sèche"

    #Systeme Meteo
    if (params["jour/nuit"]) == 1 and  params["tempjour"] == True:
        if params["saison"] == 1:
            params["temperature"] = params["temperature_base"] + random.randint(30, 35)
        else : 
            params["temperature"] = params["temperature_base"] + random.randint(26, 31)
        params["tempjour"] = False
        params["tempnuit"] = True
    if (params["jour/nuit"]) == 0 and params["tempnuit"] == True:
        if params["saison"] == 1:
            params["temperature"] = params["temperature_base"] + random.randint(25, 28)
        else : 
            params["temperature"] = params["temperature_base"] + random.randint(23, 26)
        params["tempjour"] = True
        params["tempnuit"] = False

    #Moyenne température à chaque fois que ca change
    if (params["heure"] == 1  or params["heure"] == 14) and params["secondes"] == 2: 
        params["compteur_moy_temp"] += 1
        params["temperature_moy"] = params["temperature_moy"] + (params["temperature"] - params["temperature_moy"])/params["compteur_moy_temp"]

    #Systeme de temps du jeu
    params["secondes"] += 1

    if params["secondes"] >= 60:
        params["secondes"] = 1
        params["heure"] += 1

        if params["heure"] > 24:
            params["heure"] = 1
            params["jour"] += 1

            if params["jour"] > 30:
                params["jour"] = 1
                params["mois"] += 1

                if params["mois"] > 12:
                    params["mois"] = 1


    #Affichage :
    params["heure_world"] = (8 + params["heure"]) % 24 #9h du matin
    heure_aff = str(params["heure_world"]) + ":00"

    temp = params["temperature"]
    temp_aff = f"{temp:.1f} °C"

    params["affichage"] = f"{s} | {temp_aff} | {j_n} \n{params['dict_jour'][params['jour']%7+1]} {params['jour']} {params['dict_mois'][params['mois']]} | {heure_aff} "

    #proba augmente si temperature moyenne > 30 sinon diminue
    if (params["heure"] == 14 or params["heure"] == 24) and params["secondes"] == 1:
        if params["temperature_moy"] > 29:
            params["p_fire"] += 0.2   # monte doucement
        else:
            params["p_fire"] -= 0.2 
        params["p_fire"] = round(max(0, min(0.5, params["p_fire"])), 2)

    for x in range(dx):
        for y in range(dy):

            #Déforestation 
            if (grid[x,y] == TREE):
                #au bout de coupe_bois_itération alors feu de foret
                if (x, y) in params["dict_coupe_bois"]:
                    if params["dict_coupe_bois"][(x, y)] > 20 : 
                        newgrid[x, y] = FIRETREE
                elif random.random() < params["p_fire"]:
                    newgrid[x, y] = FIRETREE
                elif (grid[(x+1+dx)%dx,y] == FIRETREE):
                    newgrid[x,y] = FIRETREE
                elif (grid[x,(y+1+dy)%dy] == FIRETREE):
                    newgrid[x,y] = FIRETREE
                elif (grid[(x-1+dx)%dx,y] == FIRETREE):
                    newgrid[x,y] = FIRETREE
                elif (grid[x,(y-1+dy)%dy] == FIRETREE):
                    newgrid[x,y] = FIRETREE
                else:
                    newgrid[x,y] = TREE



            elif (grid[x,y] == FIRETREE):
                newgrid[x,y] = TRONC
            
            elif (grid[x,y] == TRONC):
                newgrid[x,y] = GRASS
                if (params["heure"] % 2 == 0 and params["secondes"] == 2) :
                    params["temperature_base"] = min(3, params["temperature_base"] + 0.05)

            #Fontes des glaces : 
            elif grid[x, y] == MONT2:
                p_fonte = random.random()
                #fond quand il fait jour, la température est basse + probalité
                if (params["temperature"] > 30) and p_fonte < params["p_fonte"] and params["jour/nuit"] == 1 and params["saison"]==1 and params["heure"] % 2 == 0 and params["secondes"] == 1:
                        newgrid[x, y] = MONT2_WATER
                else:
                    newgrid[x, y] = MONT2
            
            elif grid[x, y] == MONT2_WATER:
                #géle quand il fait nuit et que la température est basse et que en altitude haute
                if  params["jour/nuit"] == 0 and params["temperature"] < 35 and sol[x, y] == MONT2:
                    newgrid[x, y] = MONT2 

                #aborbation (faut regler l'absorbation)
                elif sol[x, y] == GRASS or sol[x, y] == SAND:
                    p_absorption = random.random()
                    if p_absorption < params["p_absorption"]:
                        newgrid[x, y] = sol[x, y]  # absorbée lentement
                    else:
                        newgrid[x, y] = MONT2_WATER  # coule encore

                #évaporation tous les 3 heures
                elif (params["heure"] % 3 == 0 and params["secondes"] == 1 and params["temperature"] > 32):
                    if sol[x,y] == MONT2:
                        newgrid[x,y] = GRASS #altitude élévé c'est de la neige donc imaginons que sous la neige c du grass
                    else :
                        newgrid[x, y] = sol[x,y] 
                else:
                    newgrid[x, y] = MONT2_WATER

            elif grid[x, y] == SEA:
                #aborbation (faut regler l'absorbation)
                if sol[x, y] == GRASS or sol[x, y] == SAND:
                    p_absorption = random.random()
                    if p_absorption < params["p_absorption"]:
                        newgrid[x, y] = sol[x, y]  # absorbée lentement
                    else:
                        newgrid[x, y] = SEA  # coule encore

                #évaporation tous les 3 heures
                elif (params["heure"] % 3 == 0 and params["secondes"] == 1 and params["temperature"] > 32):
                        newgrid[x, y] = sol[x,y] 
                else:
                    newgrid[x, y] = SEA

            #Regéneration :
            elif grid[x, y] == DRY_GRASS :
                if (x, y) not in params["regen_dry_grass"]:
                    params["regen_dry_grass"][(x, y)] = 0
                #au bout de deux jours
                if (sol[x, y] == GRASS or sol[x, y] == FLOWER) and params["regen_dry_grass"][(x, y)] == 2 :
                    if (params["saison"] == 0) : 
                        newgrid[x, y] = sol[x, y]
                        it_grid[x,y] = 0 
                        params["regen_dry_grass"][(x, y)] = 0
                    else : 
                        if random.random() < params["p_regen"]:
                            newgrid[x, y] = sol[x, y]
                            it_grid[x,y] = 0 
                            params["regen_dry_grass"][(x, y)] = 0
                elif params["heure"] % 2 and params["secondes"] == 1: 
                    params["regen_dry_grass"][(x, y)] +=1
                    newgrid[x, y] = DRY_GRASS
                else : 
                    newgrid[x, y] = DRY_GRASS

            else : 
                newgrid[x, y] = grid[x, y]

    #Ecoulement d'eau par jour/nuit, chaque 3 heures, saison de séche
    if params["heure"] % 3 == 0 and params["secondes"] == 1 and params["saison"] == 1: 
        for x in range(dx):
            for y in range(dy):
                    p_ecoulement = random.random()
                    if p_ecoulement < params["p_ecoulement"]:
                        p_ecoulement_mouv = random.random() #proba regarde 1 chance sur deux sur la (x+1, y+1) ou (x-1, y-1)
                        if p_ecoulement_mouv < params["p_ecoulement_mouv"]:
                            if (grid[(x+1+dx)%dx,y] == MONT2_WATER):
                                newgrid[x,y] = MONT2_WATER
                            elif (grid[x,(y+1+dy)%dy] == MONT2_WATER):
                                newgrid[x,y] = MONT2_WATER
                        else: 
                            if (grid[(x-1+dx)%dx,y] == MONT2_WATER):
                                newgrid[x,y] = MONT2_WATER
                            elif (grid[x,(y-1+dy)%dy] == MONT2_WATER):
                                newgrid[x,y] = MONT2_WATER 

    #Montée d'eau chaque 3 heures, saison de pluie
    if params["heure"] % 2 == 0 and params["secondes"] == 1 and params["temperature_moy"] > 25 and params["saison"] == 0: 
        for x in range(dx):
            for y in range(dy):
                    p_ecoulement = random.random()
                    if p_ecoulement < params["p_ecoulement"]:
                        p_meau_mouv = random.random() #proba regarde 1 chance sur deux sur la (x+1, y+1) ou (x-1, y-1)
                        if p_meau_mouv < params["p_meau_mouv"]:
                            if (grid[(x+1+dx)%dx,y] == SEA) :
                                newgrid[x,y] = SEA
                            elif (grid[x,(y+1+dy)%dy] == SEA) :
                                newgrid[x,y] = SEA
                        else: 
                            if (grid[(x-1+dx)%dx,y] == SEA) :
                                newgrid[x,y] = SEA
                            elif (grid[x,(y-1+dy)%dy] == SEA) :
                                newgrid[x,y] = SEA 
    
    #Regeneration des montagne : 
    if params["heure"] % 24 == 0 and params["secondes"] % 10 == 0 :
        for x in range(dx):
            for y in range(dy):
                if random.random() < params["p_regen_mont"] and (sol[x,y] == MONT2 or sol[x,y] == MONT1): 
                    newgrid[x,y] = sol[x,y]

    #Ecriture du graphique:
    base_de_donnees(grid, params, agents)

    agents.extend(params["nouveaux_nes"])
    params["nouveaux_nes"] = []
    import numpy as np
    grid[:] = np.clip(grid, 0, 18)
    newgrid[:] = np.clip(newgrid, 0, 18)


# =-=-= Defining agent types

HUMAIN_SANE = 0
HUMAIN_INFECTED = 1
HUMAIN_RECOVER = 2

CHICKEN_SANE = 3
CHICKEN_INFECTED = 4
CHICKEN_RECOVER = 5


colors_agents = {
    #Couleurs au hasard pour l'instant
    HUMAIN_SANE: (255, 255, 0), #JAUNE
    HUMAIN_INFECTED: (255, 0, 0), #ROUGE
    HUMAIN_RECOVER: (255, 165, 0), #ORANGE

    CHICKEN_SANE: (0, 255, 0), #VERT
    CHICKEN_INFECTED: (0, 0, 255), #BLEU
    CHICKEN_RECOVER: (128, 0, 128) #VIOLET
    
    
}

image_agents = {
    HUMAIN_SANE: "image/IMG_2935.png",
    HUMAIN_INFECTED: "image/IMG_2936.png",
    HUMAIN_RECOVER: "image/IMG_2934.png",

    CHICKEN_SANE:  "image/IMG_2932.png",
    CHICKEN_INFECTED:  "image/IMG_2931.png",
    CHICKEN_RECOVER:  "image/IMG_2933.png"
    
}
# =-=-= user-defined agents


def peut_marcher(nx, ny, grid):
    dx, dy = grid.shape
    if not (0 <= nx < dx and 0 <= ny < dy):
        return False
    if grid[nx, ny] == SEA:
        return False
    return True

class Chicken(Agent):
    def __init__(self, x: float, y: float, params):
        super().__init__(x, y,"Chicken",params)
        self.type = CHICKEN_SANE
        self.running = True
        self.couleur = 0
        self.age = 0
        self.guerison = 0
        self.famine = 0
        self.chaleur = False
    def move(self, grid, agents, it_grid):
        if not self.running: return
        vision = 3
        cible = None

        proba = 1.0

        #Les chicken se réveillent un peu après le lever du Soleil
        heure = self.params["heure_world"]
        if heure >= 22 or heure < 10:
            proba = 0

        #Condition déplacement pour malades
        if self.type == CHICKEN_INFECTED:
            proba = proba * self.params["p_mouv_infect_chicken"]

        #Vitesse déplacement en montagne
        sol = grid[self.x, self.y]
        if sol == MONT1:
            proba = proba * self.params["vitesse_deplacement_mont"]

        bouge = True
        if random.random() > proba:
            bouge = False

        #Déplacement
        if bouge:
            cible = None
            vx, vy = grid.shape
            xmin = max(0, self.x - vision)
            xmax = min(vx, self.x + vision + 1)
            ymin = max(0, self.y - vision)
            ymax = min(vy, self.y + vision + 1)
            
            for a in agents:
                if a.type in [HUMAIN_SANE, HUMAIN_INFECTED, HUMAIN_RECOVER] and a.running:
                    if xmin <= a.x < xmax and ymin <= a.y < ymax:
                        x = abs(self.x - a.x)
                        y = abs(self.y - a.y)
                        if (x == 0 or y == 0) and (x + y <= vision):
                            cible = a
                            break
                    
            dx, dy = 0, 0
            if cible:
                if cible.x != self.x:
                    if cible.x > self.x:
                        dx = 1
                    else:
                        dx = -1
                elif cible.y != self.y:
                    if cible.y > self.y:
                        dy = 1
                    else:
                        dy = -1
            else:
                dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            
            prochain_x = self.x + dx
            prochain_y = self.y + dy
            if 0 <= prochain_x < vx and 0 <= prochain_y < vy:
                if peut_marcher(self.x + dx, self.y + dy, grid):
                    self.x = self.x + dx
                    self.y = self.y + dy
                elif peut_marcher(prochain_x, self.y, grid):
                    self.x = prochain_x
                elif peut_marcher(self.x, prochain_y, grid):
                    self.y = prochain_y

                if grid[self.x, self.y] == FIRETREE or grid[self.x, self.y] == MONT2_WATER or grid[self.x, self.y] == SEA: # Meurt s'il croise un arbre en feu ou de l'eau
                    self.running = False
                if grid[self.x, self.y] == GRASS or grid[self.x, self.y] == FLOWER:
                    it_grid[self.x, self.y] += 1
                    if it_grid[self.x, self.y] >= 5:
                        grid[self.x, self.y] = DRY_GRASS

        #Update vie
        if params["heure"] % 24 == 0 and params["secondes"] == 1:
            self.age = self.age + 1
            self.famine = self.famine + 1

        #Check si encore vivant
        if self.age > self.params["dureedevie_chicken"] or self.famine > self.params["maxfamine_chicken"]:
            self.running = False 
        
        #Nourriture
        for a in agents:
            if a.running and a.type in [HUMAIN_SANE, HUMAIN_INFECTED, HUMAIN_RECOVER]:
                if a.x == self.x and a.y == self.y:
                    if a.type == HUMAIN_INFECTED:
                        self.type = CHICKEN_INFECTED
                    a.running = False
                    self.famine = 0

        #Reproduction
        if self.type in [CHICKEN_SANE, CHICKEN_RECOVER]:
            if random.random() < self.params["p_repro_chicken"]:
                    p = Chicken(self.x, self.y, params=self.params)
                    agents.append(p)

        #Tomber malade
        if params["jour/nuit"] == 1:
            if random.random()<self.params["proba_malade_chicken"] and params["heure"] % 2 == 0 and params["secondes"] == 1:
                self.type = CHICKEN_INFECTED

        
        #Contagion maladie
        if self.type == CHICKEN_INFECTED:
            for a in agents:
                if a.type == CHICKEN_SANE and a.running:
                    if a.x == self.x and a.y == self.y:
                        a.type = CHICKEN_INFECTED

        #Progression de la maladie & guérison
        if self.type == CHICKEN_INFECTED:
            if params["heure"] % 2 == 0 and params["secondes"] == 1 :
                self.guerison += 1
            if self.guerison > self.params["maxguerison_chicken"]:
                self.type = CHICKEN_RECOVER
                self.guerison = 0

        #Vieillit plus vite en cas de forte chaleur
        if self.params["temperature"] > 35:
            if not self.chaleur:
                self.age += 1
                self.chaleur = True
        else:
            self.chaleur = False


class Humain(Agent):
    def __init__(self, x: float, y: float, params):
        super().__init__(x, y, "Humain", params)
        self.type = HUMAIN_SANE
        self.running = True
        self.couleur = 0
        self.age = 0
        self.guerison = 0
        self.famine = 0
        self.chaleur = False
    def move(self, grid, agents, it_grid):
        if not self.running: return

        vision  = 4
        danger = None

        proba = 1.0

        #Les humains dorment la nuit
        heure = self.params["heure_world"]
        if heure >= 22 or heure < 8:
            proba = 0

        #Condition déplacement pour malades
        if self.type == HUMAIN_INFECTED:
            proba = proba * self.params["p_mouv_infect_humain"]

        #Vitesse déplacement en montagne
        sol = grid[self.x, self.y]
        if sol == MONT1:
            proba = proba * self.params["vitesse_deplacement_mont"]

        bouge = True
        if random.random() > proba:
            bouge = False
        
        #Déplacement
        if bouge:
            danger = None
            manger = None
            vx, vy = grid.shape

            for a in agents:
                    if a.type in[CHICKEN_SANE, CHICKEN_INFECTED, CHICKEN_RECOVER] and a.running:
                        if max(abs(self.x - a.x), abs(self.y - a.y)) <= vision:
                            danger = a
                            break

            if not danger:
                xmin = max(0, self.x - vision)
                xmax = min(vx, self.x + vision + 1)
                ymin = max(0, self.y - vision)
                ymax = min(vy, self.y + vision + 1)

                for x in range (xmin, xmax):
                    for y in range (ymin, ymax):
                        if grid[x, y] in [MONT1, MONT1LEV2, MONT1LEV3, FLOWER, ROCK]:
                            manger = (x, y)
                            break
                    if manger:
                        break

            dx, dy = 0, 0
            if manger:
                if manger[0] > self.x:
                    dx = 1
                elif manger[0] < self.x:
                    dx = -1

                if manger[1] > self.y:
                    dy = 1
                elif manger[1] < self.y:
                    dy = -1

            elif danger:
                if danger.x > self.x:
                    dx = -1
                elif danger.x < self.x:
                    dx = 1

                if danger.y > self.y:
                    dy = -1
                elif danger.y < self.y:
                    dy = 1
            else:
                dx, dy = random.choice([(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)])

            prochain_x = self.x + dx
            prochain_y = self.y + dy
            
            if 0 <= prochain_x < vx and 0 <= prochain_y < vy:
                if peut_marcher(prochain_x, prochain_y, grid):
                    self.x = self.x + dx
                    self.y = self.y + dy
                elif peut_marcher(prochain_x, self.y, grid):
                    self.x = self.x + dx
                elif peut_marcher(self.x, prochain_y, grid):
                    self.y = self.y + dy
                
                if grid[self.x, self.y] == SEA:
                    self.running = False 
                
                if grid[self.x, self.y] == GRASS:
                    it_grid[self.x, self.y] += 1
                    if it_grid[self.x, self.y] >= 5:
                        grid[self.x, self.y] = DRY_GRASS
        
      
        #Update vie
        if params["heure"] % 24 == 0 and params["secondes"] == 1:
            self.age = self.age + 1
            self.famine = self.famine + 1

        #Check si encore vivant
        if self.age > self.params["dureedevie_humain"] or self.famine > self.params["maxfamine_humain"]:
            self.running = False 
        
        #Nourriture
        if grid[self.x, self.y] == MONT1 :
            self.famine = 0
            grid[self.x, self.y] = MONT1LEV2
        elif grid[self.x, self.y] == MONT1LEV2:
            self.famine = 0
            grid[self.x, self.y] = MONT1LEV3
        elif grid[self.x, self.y] == MONT1LEV3:
            self.famine = 0
            grid[self.x, self.y] = GRASS
        elif grid[self.x, self.y] == FLOWER:
            self.famine = 0
            grid[self.x, self.y] = GRASS
        elif grid[self.x, self.y] == ROCK:
            self.famine = 0
            grid[self.x, self.y] = GRASS

        #Reproduction (bébé malade si un des deux parents est malade)
        for a in agents:
            if (a.type == HUMAIN_SANE or a.type == HUMAIN_RECOVER) and a != self :
                if a.x == self.x and a.y == self.y and a.running == True :
                    if random.random() < self.params["p_repro_humain"]:
                        bebe = Humain(self.x, self.y, params=self.params)
                        if self.type == HUMAIN_INFECTED:
                            bebe.type = HUMAIN_INFECTED
                        params["nouveaux_nes"].append(bebe)
                        break
        
        #Tomber malade

        if params["jour/nuit"] == 1:
            if self.type == HUMAIN_SANE :
                if random.random() < self.params["proba_malade_humain"] and params["secondes"] % 20 == 0 :
                    self.type = HUMAIN_INFECTED


        #Contamination maladie
        if self.type == HUMAIN_SANE:
            for a in agents:
                if a.type == HUMAIN_INFECTED and a.x == self.x and a.y == self.y and a.running:
                        if random.random() < self.params["contagion_humain"]:
                            self.type = HUMAIN_INFECTED

        #Progression de la maladie & guérison
        if self.type == HUMAIN_INFECTED:
            if params["heure"] % 2 == 0 and params["secondes"] == 1 :
                self.guerison += 1
            maxguerison = self.params["maxguerison_humain"]
            if self.guerison > maxguerison :
                self.type = HUMAIN_RECOVER
                self.guerison = 0

        
        #Déclencher feu de forêt en coupant du bois
        if params["jour/nuit"] == 1 and grid[self.x, self.y] == TREE:
            if (self.x, self.y) not in params["dict_coupe_bois"]:
                params["dict_coupe_bois"][(self.x, self.y)] = 0
            params["dict_coupe_bois"][(self.x, self.y)] += 1

        #Planter un arbre, sinon déclenche un feu de forêt
        if params["jour/nuit"] == 1:
            case_origine = grid[self.x, self.y]

            if random.random() < self.params["planter_arbre"] and case_origine != TREE:
                grid[self.x, self.y] = TREE
                params["temperature_base"] = max(0, params["temperature_base"] - 0.02)
            
            elif case_origine == TREE:
                if (self.x, self.y) not in params["dict_coupe_bois"]:
                    params["dict_coupe_bois"][(self.x, self.y)] = 0
                params["dict_coupe_bois"][(self.x, self.y)] += 1

        # Vieillit plus vite en cas de forte chaleur
        if self.params["temperature"] > 35:
            if not self.chaleur:
                self.age += 1
                self.chaleur = True
        else:
            self.chaleur = False


def make_agents(params, grid):
    seed_value = params["seed_value"]
    random.seed(seed_value)

    dx = params["dx"]
    dy = params["dy"]
    agents = []

    for x in range(dx):
        for y in range(dy):
            if grid[x, y] != SEA and random.random()<params["density_humain"]:
                agents.append(Humain(x, y, params=params))

    for x in range(dx):
        for y in range(dy):
            if grid[x, y] != SEA and random.random()<params["density_chicken"]:
                agents.append(Chicken(x, y, params=params))
            
    return agents

#fonction pour les graphiques
list_arbre_sains = []
list_temperature = []
list_p_fire = []

liste_ch = []
liste_chsain = []
liste_chinf = []
liste_chrec = []

liste_h = []
liste_hsain = []
liste_hinf = []
liste_hrec = []

liste_f5 = []

def base_de_donnees(grid, params, agents):
    dx = params["dx"]
    dy = params["dy"]

    nb_arbre_sain = 0
    nb_neige = 0
    nb_water_mont = 0

    for x in range (dx):
        for y in range (dy):
            if grid[x, y] == TREE:
                nb_arbre_sain = nb_arbre_sain + 1
            elif grid[x,y] == MONT2:
                nb_neige += 1
            elif grid[x,y] == MONT2_WATER:
                nb_water_mont += 1

    nb_ch = 0
    nb_chsain = 0
    nb_chinf = 0
    nb_chrec = 0

    nb_h = 0
    nb_hsain = 0
    nb_hinf = 0
    nb_hrec = 0
    for a in agents:
        if a.running:
            if (a.type == CHICKEN_SANE or a.type == CHICKEN_INFECTED or a.type == CHICKEN_RECOVER):
                nb_ch += 1 
                if (a.type == CHICKEN_SANE):
                    nb_chsain += 1 
                elif (a.type == CHICKEN_INFECTED):
                    nb_chinf += 1 
                elif (a.type == CHICKEN_RECOVER):
                    nb_chrec += 1 

            if (a.type == HUMAIN_SANE or a.type == HUMAIN_INFECTED or a.type == HUMAIN_RECOVER):
                nb_h += 1 
                if (a.type == HUMAIN_SANE):
                    nb_hsain += 1 
                elif (a.type == HUMAIN_INFECTED):
                    nb_hinf += 1 
                elif (a.type == HUMAIN_RECOVER):
                    nb_hrec += 1 

    if params["heure"] % 2 == 0 and params["secondes"] == 2:
        list_arbre_sains.append(nb_arbre_sain)

        list_temperature.append(params["temperature_moy"])
        list_p_fire.append(params["p_fire"])

        liste_ch.append(nb_ch)
        liste_chsain.append(nb_chsain)
        liste_chinf.append(nb_chinf)
        liste_chrec.append(nb_chrec)

        liste_h.append(nb_h)
        liste_hsain.append(nb_hsain)
        liste_hinf.append(nb_hinf)
        liste_hrec.append(nb_hrec)

        #ecriture dans le fichier
        f1.write(str(len(list_arbre_sains)) + "," + str(nb_arbre_sain/list_arbre_sains[0]) + "," + str(params["p_fire"]) + "," + str(params["temperature_moy"]/45) + "\n")

        f2.write(str(len(liste_ch)) + "," + str(nb_ch) + "," + str(nb_h) + "\n")

        f3.write(str(len(liste_ch)) + "," + str(nb_ch) + "," + str(nb_chsain) + "," + str(nb_chinf) + "," + str(nb_chrec) + "\n")
    
        f4.write(str(len(liste_h)) + "," + str(nb_h) + "," + str(nb_hsain) + "," + str(nb_hinf) + "," + str(nb_hrec) + "\n")

        f5.write(str(len(liste_h)) + "," + str(nb_water_mont/100) + "," + str(nb_neige/100) + "," + str(params["temperature"]/45) + "," + str(params["jour/nuit"]) + "\n")

#taille de l'écran : 
import tkinter as tk #bibliothéque qui crée des interfaces graphiques

root = tk.Tk()
screen_width = root.winfo_screenwidth() # demande à Tkinter la largeur de l’écran en pixels.
screen_height = root.winfo_screenheight()
root.destroy()

# =-=-= run

if __name__ == "__main__":
    f1 = open("arbre.csv", "w")
    f2 = open("agents.csv", "w")

    f3 = open("ch.csv", "w")
    f4 = open("h.csv", "w")
    f5 = open("eau.csv", "w")

    calipsolib.run(
        params=params, # user-deed
        init_simulation=init_simulation, # user-defined
        ca_step=ca_step, # user-defined
        make_agents=make_agents, # user-defined
        colors_ca=colors_ca,
        colors_agents=colors_agents,
        image_ca=image_ca,
        image_agents=image_agents,
        dx=130, # CA width
        dy=80, # CA height
        display_dx=screen_width,
        display_dy=screen_height,
        title="Predator-Prey (template)", 
        verbose=False, # display stuff (can be used by user)
        fps=30 # steps per seconds (default: 60)
    )
