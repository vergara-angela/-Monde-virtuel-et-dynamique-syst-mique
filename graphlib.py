# graphlib.py
# à installer : pip3 install pandas matplotlib
# dans le terminal graphlib.py
import pandas as pd
import matplotlib.pyplot as plt

def afficher_tous():

    # --- Arbres (col 0 = temps, col 1 = proportion) ---
    df_arbre = pd.read_csv("arbre.csv", header=None, names=["temps", "proportion", "p_fire", "climat"])
    plt.figure()
    plt.plot(df_arbre["temps"], df_arbre["proportion"], color="green", label="Arbres (%)")
    plt.plot(df_arbre["temps"], df_arbre["p_fire"], color="red", label="p_fire (%)")
    plt.plot(df_arbre["temps"], df_arbre["climat"], color="orange", label="climat (°C) / 45")
    plt.title("Évolution des arbres")
    plt.xlabel("Temps")
    plt.ylabel("Proportion")
    plt.legend()
    plt.savefig("arbres.png")

    # --- Agents total (col 0 = temps, col 1 = ch_total, col 2 = h_total) ---
    df_agents = pd.read_csv("agents.csv", header=None, names=["temps", "ch_total", "h_total"])
    plt.figure()
    plt.plot(df_agents["temps"], df_agents["ch_total"], color="blue",  label="Chicken")
    plt.plot(df_agents["temps"], df_agents["h_total"],  color="yellow", label="Humains")
    plt.title("Population totale")
    plt.xlabel("Temps")
    plt.ylabel("Nombre d'agents")
    plt.legend()
    plt.savefig("agents.png")

    # --- SIR Chicken (col 0 = temps, col 1 = total, col 2 = sain, col 3 = inf, col 4 = rec) ---
    df_ch = pd.read_csv("ch.csv", header=None, names=["temps", "total", "sain", "inf", "rec"])
    plt.figure()
    plt.plot(df_ch["temps"], df_ch["sain"],  color="green",  label="Sain")
    plt.plot(df_ch["temps"], df_ch["inf"],   color="blue",   label="Infecté")
    plt.plot(df_ch["temps"], df_ch["rec"],   color="purple", label="Rétabli")
    plt.title("SIR Chicken")
    plt.xlabel("Temps")
    plt.ylabel("Nombre d'agents")
    plt.legend()
    plt.savefig("sir_chicken.png")

    # --- SIR Humains (col 0 = temps, col 1 = total, col 2 = sain, col 3 = inf, col 4 = rec) ---
    df_h = pd.read_csv("h.csv", header=None, names=["temps", "total", "sain", "inf", "rec"])
    plt.figure()
    plt.plot(df_h["temps"], df_h["sain"],  color="yellow", label="Sain")
    plt.plot(df_h["temps"], df_h["inf"],   color="red",    label="Infecté")
    plt.plot(df_h["temps"], df_h["rec"],   color="orange", label="Rétabli")
    plt.title("SIR Humains")
    plt.xlabel("Temps")
    plt.ylabel("Nombre d'agents")
    plt.legend()
    plt.savefig("sir_humains.png")

    # --- SURFACE de l'eau de montagne ---
    df_h = pd.read_csv("eau.csv", header=None, names=["temps", "nb_water_mont", "nb_neige", "temperature", "jour/nuit"])
    plt.figure()
    plt.plot(df_h["temps"], df_h["nb_water_mont"],  color="yellow", label="eau de montagne")
    plt.plot(df_h["temps"], df_h["nb_neige"],   color="red",    label="neige de montagne")
    plt.plot(df_h["temps"], df_h["temperature"],   color="orange", label="Temperature (°C) / 45")
    plt.plot(df_h["temps"], df_h["jour/nuit"],   color="blue",    label="jour (1) / nuit (0)")
    plt.title("eau de montagne")
    plt.xlabel("Temps")
    plt.ylabel("Proportion")
    plt.legend()
    plt.savefig("eu_de_montagne.png")

    plt.show()

if __name__ == "__main__":
    afficher_tous()