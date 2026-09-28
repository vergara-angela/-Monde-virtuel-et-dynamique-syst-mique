#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simulator loop:
# 1. agents move
# 2. cellular automata is updated (ie. future states are computed)
# 3. future states become current state
# 4. go to 1

# last update: 2026-01-22_17h20

import random
import math
import pygame
import numpy as np
import pygame.surfarray as surfarray
import time

# template class for agents

class Agent:
    _next_id = 0  # class-level counter
    def __init__(self, x: float, y: float, type: str, params):
        self.params = params
        self.x = x
        self.y = y
        self.id = Agent._next_id
        self.type = type
        self.running = True
        self.dx = params["dx"]
        self.dy = params["dy"]
        Agent._next_id += 1
    def move(self, grid, agents):
        pass
    
# build lookup table for color (faster)
def build_color_lut(colors: dict) -> np.ndarray:
    lut = np.zeros((max(colors.keys()) + 1, 3), dtype=np.uint8)
    for k, v in colors.items():
        lut[k] = v
    return lut

# render CA and agents (if any)
def draw_grid(
    screen: pygame.Surface,
    grid,
    dx: int,
    dy: int,
    win_w: int,
    win_h: int,
    zoom: float,
    cx: float,
    cy: float,
    agents,
    color_ca_lut: np.ndarray,
    color_agents_lut: np.ndarray,
    #Modification pour les images
    images_loaded=None,
    images_agents_loaded=None
) -> None:
    base_cell_size = min(win_w / dx, win_h / dy)
    cell_size = base_cell_size * zoom

    vis_w = win_w / cell_size
    vis_h = win_h / cell_size

    x0 = cx - vis_w / 2.0
    y0 = cy - vis_h / 2.0

    x0 = max(0.0, min(x0, dx - vis_w))
    y0 = max(0.0, min(y0, dy - vis_h))

    ix0 = max(0, int(math.floor(x0)))
    iy0 = max(0, int(math.floor(y0)))
    ix1 = min(dx, int(math.ceil(x0 + vis_w)))
    iy1 = min(dy, int(math.ceil(y0 + vis_h)))

    ix1 = min(dx, ix1 + 1)
    iy1 = min(dy, iy1 + 1)

    arena_w_px = dx * cell_size
    arena_h_px = dy * cell_size

    if arena_w_px <= win_w and arena_h_px <= win_h:
        off_x = int((win_w - arena_w_px) / 2)
        off_y = int((win_h - arena_h_px) / 2)
        x0 = 0.0
        y0 = 0.0
        ix0, iy0, ix1, iy1 = 0, 0, dx, dy
    else:
        off_x = 0
        off_y = 0

    sub = grid[ix0:ix1, iy0:iy1]
    w_px = max(1, int((ix1 - ix0) * cell_size))
    h_px = max(1, int((iy1 - iy0) * cell_size))

    if cell_size < 1.0:
        sx = max(1, int(round((ix1 - ix0) / w_px)))
        sy = max(1, int(round((iy1 - iy0) / h_px)))
        sub_small = sub[::sx, ::sy]
    else:
        sub_small = sub

    # --- DESSIN SOL (herbe, mer, feu, etc.) ---
    rgb = color_ca_lut[sub_small]  # couleur du sol
    surf = surfarray.make_surface(rgb)
    if surf.get_width() != w_px or surf.get_height() != h_px:
        surf = pygame.transform.scale(surf, (w_px, h_px))
    screen.blit(surf, (off_x, off_y))

    r = max(1, int(cell_size / 2))
    for a in agents:
        if not a.running:
            continue
        ax, ay = a.x, a.y
        if not (0 <= ax < dx and 0 <= ay < dy):
            continue
        px = off_x + int((ax - x0) * cell_size)
        py = off_y + int((ay - y0) * cell_size)

        if images_agents_loaded and a.type in images_agents_loaded:
            img_scaled = pygame.transform.scale(images_agents_loaded[a.type], (int(cell_size), int(cell_size)))
            screen.blit(img_scaled, (px, py))
        else:
            pygame.draw.circle(screen, tuple(color_agents_lut[a.type]), 
                            (px + int(cell_size/2), py + int(cell_size/2)), r)
            
    # --- DESSIN OBJETS (arbres, rochers, etc.) ---
    if images_loaded:
        for x in range(ix0, ix1):
            for y in range(iy0, iy1):
                cell_type = grid[x, y]
                if cell_type in images_loaded:  # toutes les images sont des objets
                    px = off_x + round((x - ix0) * cell_size)
                    py = off_y + round((y - iy0) * cell_size)
                    size = round(cell_size)
                    img_scaled = pygame.transform.scale(images_loaded[cell_type], (size, size))
                    screen.blit(img_scaled, (px, py))
            
            
            
# manage zoom when rendering
def clamp_camera(cx, cy, dx, dy, win_w, win_h, zoom):
    base_cell_size = min(win_w / dx, win_h / dy)
    cell_size = base_cell_size * zoom
    vis_w = win_w / cell_size
    vis_h = win_h / cell_size

    if vis_w >= dx and vis_h >= dy:
        return (dx - 1) / 2.0, (dy - 1) / 2.0

    half_w = vis_w / 2.0
    half_h = vis_h / 2.0
    cx = max(half_w, min(cx, dx - half_w))
    cy = max(half_h, min(cy, dy - half_h))
    return cx, cy


# entry point for user to launch the simulation
def run(
    *,
    params: dict,
    init_simulation,  # defined by user: (params) -> (grid, newgrid)
    ca_step,          # defined by user: (grid, newgrid, densite, ...) -> None
    colors_ca: dict,
    colors_agents: dict,
    image_ca: dict=None, # Modification : pour mettre des images
    image_agents :dict=None,
    make_agents=None, # defined by user: (params) -> list[agent]
    dx: int = 80, # default value
    dy: int = 80, # default value
    display_dx: int = 800, # default value
    display_dy: int = 800, # default value
    title: str = "no name", # default value
    verbose: bool = False,
    fps: int = 60,
    max_simulation_steps: int = -1, # max simulation steps, default is -1, i.e., infinite
) -> None:

    sps_last_t = time.perf_counter() # sps: steps per seconds (can be lower or equal to fps -- used for monitoring)
    sps_count = 0
    sps_value = 0.0

    max_simulation_steps = -1
    it = 0

    render_periods = (1, 60, 6000) # simulation speed (changes with "d" key during simulation)
    render_idx = 0
    render_every = render_periods[render_idx]

    color_ca_lut = build_color_lut(colors_ca)
    if colors_agents != None:
        color_agents_lut = build_color_lut(colors_agents)
    else:
        color_agents_lut = None

    params["dx"] = dx
    params["dy"] = dy 

    current_world_state, future_world_state, first_world_state, it_grid = init_simulation(params)

    agents = make_agents(params,current_world_state) if make_agents is not None else []

    zoom = 1.0
    move_span_init = max(dx, dy) / 10
    move_span = move_span_init

    cx, cy = (dx - 1) / 2.0, (dy - 1) / 2.0

    pygame.init()

    # créer l'écran AVANT de charger les images
    screen = pygame.display.set_mode((display_dx, display_dy))
    pygame.display.set_caption(title)

    # --- CHARGEMENT DES IMAGES ---
    images_loaded = {}
    if image_ca is not None:
        for cell_type, filename in image_ca.items():
            try:
                img = pygame.image.load(filename).convert_alpha()
                images_loaded[cell_type] = img
            except Exception as e:
                print(f"WARNING: Could not load {filename} ({e})")

    images_agents_loaded = {}
    if image_agents is not None:
        for agent_type, filename in image_agents.items():
            try:
                img = pygame.image.load(filename).convert_alpha()
                images_agents_loaded[agent_type] = img
            except Exception as e:
                print(f"WARNING: Could not load {filename} ({e})")

    clock = pygame.time.Clock()
    SHOW_FPS = True
    MAX_FPS = fps
    font = pygame.font.SysFont(None, 24)
    font_hud = pygame.font.SysFont("monospace", 28, bold=True)

    running = True

    while running and it != max_simulation_steps:

        if it % 10 == 0 and verbose:
            print(str(it))

        pygame.event.pump()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
                return

            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                shift = bool(mods & pygame.KMOD_SHIFT)

                if event.key == pygame.K_z:
                    zoom = zoom * 1.1 if shift else zoom / 1.1
                    if zoom < 1.0:
                        zoom = 1.0
                    move_span = move_span_init / zoom

                elif event.key == pygame.K_d:
                    render_idx = (render_idx - 1) % len(render_periods) if shift else (render_idx + 1) % len(render_periods)
                    render_every = render_periods[render_idx]
                    print("render every", render_every, "frames")

                elif event.key == pygame.K_r:
                    if shift:
                        current_world_state, future_world_state, first_world_state = init_simulation(params)
                        agents = make_agents(params, current_world_state) if make_agents is not None else []
                    else:
                        zoom = 1.0
                        cx, cy = (dx - 1) / 2.0, (dy - 1) / 2.0

                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                    if event.key == pygame.K_LEFT:
                        cx = max(0, cx - move_span)
                    elif event.key == pygame.K_RIGHT:
                        cx = min(dx - 1, cx + move_span)
                    elif event.key == pygame.K_UP:
                        cy = max(0, cy - move_span)
                    elif event.key == pygame.K_DOWN:
                        cy = min(dy - 1, cy + move_span)

                elif event.key == pygame.K_f:
                    arbres = np.argwhere(current_world_state == params["tree"])
                    if len(arbres) > 0:
                        feu = random.choice(arbres)
                        current_world_state[feu[0], feu[1]] = params["firetree"]
                        print("Incendie déclenché")


                elif event.key == pygame.K_s:
                    if params["saison"] == 1: #si c'est la saison sèche
                        params["mois"] = 9 #le mois devient octobre et on bascule en saison de pluie
                    else:                         #si c'est la saison de pluie
                        params["mois"] = 1 #le mois devient juin et on bascule en saison sèche


                #elif event.key == pygame.K_s:



        if not running:
            break

        keys = pygame.key.get_pressed()
        shift_held = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        if shift_held:
            if keys[pygame.K_LEFT]:
                cx = max(0, cx - move_span)
            if keys[pygame.K_RIGHT]:
                cx = min(dx - 1, cx + move_span)
            if keys[pygame.K_UP]:
                cy = max(0, cy - move_span)
            if keys[pygame.K_DOWN]:
                cy = min(dy - 1, cy + move_span)

        cx, cy = clamp_camera(cx, cy, dx, dy, display_dx, display_dy, zoom)

        do_draw = (it % render_every == 0)
        if do_draw:
            screen.fill((0, 0, 0))
            draw_grid(screen, current_world_state, dx, dy, display_dx, display_dy, zoom, cx, cy, agents, color_ca_lut, color_agents_lut, images_loaded, images_agents_loaded)

            if params["jour/nuit"] == 0:  # NUIT
                night_overlay = pygame.Surface((display_dx, display_dy)) #creer une surface vierge
                night_overlay.set_alpha(120)  # 0 = transparent, 255 = opaque
                night_overlay.fill((0, 0, 30))  # recouvre toute la surface en bleu nuit 
                screen.blit(night_overlay, (0, 0)) #on met la surface night_overlay, (0,0) le coin le plus haut commence à recouvrir à part

            if SHOW_FPS:
                SHOW_FPS_COLORS = [(128, 0, 0), (0, 128, 0), (0, 0, 128)]
                text_surf = font.render(f"{clock.get_fps():.1f} FPS, {sps_value:.0f} SPS", True, SHOW_FPS_COLORS[random.randint(0,2)])
                screen.blit(text_surf, (10, 10))

            texte = params["affichage"]
            lignes = texte.split("\n")

            y = 70

            for ligne in lignes:
                text_surf = font.render(ligne, True, (255, 255, 255))
                screen.blit(text_surf, (20, y))
                y += 20

            pygame.display.flip()
            clock.tick(MAX_FPS)

        for a in agents:
            a.move(current_world_state,agents, it_grid)

        ca_step(current_world_state, future_world_state, first_world_state, it_grid, agents)

        current_world_state, future_world_state, first_world_state = future_world_state, current_world_state, first_world_state

        it += 1
        sps_count += 1
        now = time.perf_counter()
        dt = now - sps_last_t
        if dt >= 1.0:
            sps_value = sps_count / dt
            sps_count = 0
            sps_last_t = now

    pygame.quit()
