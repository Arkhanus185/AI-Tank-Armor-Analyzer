import numpy as np
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os

DB_FILE = "ammo_db.json"

DEFAULT_AMMO = {
    "MKE 120mm MOD 290 (APFSDS-T)": {
        "type": "KE", "color": "turquoise",
        "guns": {
            "M60T Sabra / Leopard 2A4 (L/44)": [[0, 620], [2000, 500], [4000, 300]],
            "Altay (L/55)": [[0, 660], [2000, 550], [4000, 450]]
        },
        "IMG": r"ammo_images\120 mm MKE MOD 290 APFSDS-T.jpg"
    },
    "MKE 120mm MOD 310 (HEAT-MP-T)": {
        "type": "CE", "color": "red",
        "guns": {"Standard 120mm Gun": [[0, 600], [4000, 600]]},
        "IMG": r"ammo_images\120 mm MKE MOD 310 HEAT-MP-T.jpg"
    },
    "DM53 (German - Tungsten)": {
        "type": "KE", "color": "blue",
        "guns": {
            "L/44 (Leopard 2A4)": [[0, 760], [2000, 680], [4000, 600]],
            "L/55 (Leopard 2A6)": [[0, 820], [2000, 740], [4000, 660]]
        },
        "IMG": r"ammo_images\DM53-Tungsten.jpg"
    },
    "M829A4 (USA - DU)": {
        "type": "KE", "color": "green",
        "guns": {"M256 120mm (Abrams)": [[0, 880], [2000, 830], [4000, 780]]},
        "IMG": r"ammo_images\M829A4 UD.jpg"
    },
    "3BM60 Svinets-2 (Russian)": {
        "type": "KE", "color": "maroon",
        "guns": {"2A46M-5 (Modern T-90M)": [[0, 740], [2000, 650], [4000, 560]]},
        "IMG": r"ammo_images\3BM60 svinets-2.jpg"
    },
    "RPG-7 (PG-7VL Warhead)": {
        "type": "CE", "color": "orange",
        "guns": {"Shoulder Fired": [[0, 500], [4000, 500]]},
        "IMG": r"ammo_images\RPG7 PG-7VL.jpg"
    },
    "9M133 Kornet (ATGM)": {
        "type": "CE", "color": "purple",
        "guns": {"Launch Tube": [[0, 1200], [4000, 1200]]},
        "IMG": r"ammo_images\9M133 Kornet ATGM.jpg"
    }
}

def load_db():
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_AMMO)
        return DEFAULT_AMMO
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

AMMO_DATABASE = load_db()

def calculate_penetration(ammo_name, gun_name, distance):
    """Calculates penetration power based on ammo, gun, and distance using interpolation."""
    try:
        data_points = AMMO_DATABASE[ammo_name]["guns"][gun_name]
    except KeyError:
        return 0.0

    dists = [p[0] for p in data_points]
    pens = [p[1] for p in data_points]
    
    max_range = dists[-1]
    if distance > max_range:
        return 0.0

    result = np.interp(distance, dists, pens)
    return round(result, 2)

class GraphicWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ballistic Performance Graphs")
        self.geometry("900x600")
        
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.control_frame, text="Filters:", font=("Arial", 14, "bold")).pack(side="left", padx=10)

        self.var_ke = ctk.BooleanVar(value=True)
        self.var_ce = ctk.BooleanVar(value=True)

        self.chk_ke = ctk.CTkCheckBox(self.control_frame, text="Kinetic Energy (KE)", variable=self.var_ke, command=self.draw_graph, fg_color="blue")
        self.chk_ke.pack(side="left", padx=10)

        self.chk_ce = ctk.CTkCheckBox(self.control_frame, text="Chemical Energy (CE)", variable=self.var_ce, command=self.draw_graph, fg_color="red")
        self.chk_ce.pack(side="left", padx=10)

        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.draw_graph()

    def draw_graph(self):
        self.ax.clear()
        x_axis = np.linspace(0, 4000, 400)
        
        for ammo_name, data in AMMO_DATABASE.items():
            ammo_type = data["type"]
            if ammo_type == "KE" and not self.var_ke.get(): continue
            if ammo_type == "CE" and not self.var_ce.get(): continue

            for gun_name, points in data["guns"].items():
                dists = [p[0] for p in points]
                pens = [p[1] for p in points]
                y_values = np.interp(x_axis, dists, pens)
                
                max_dist = dists[-1]
                y_values[x_axis > max_dist] = np.nan 

                line_style = '-' if ammo_type == "KE" else '--'
                label_text = f"{ammo_name}"
                if len(data["guns"]) > 1:
                    label_text += f" ({gun_name})"

                self.ax.plot(x_axis, y_values, label=label_text, color=data.get("color", "gray"), linestyle=line_style, linewidth=2)

        self.ax.set_title("Distance vs Penetration (RHA)", fontsize=12)
        self.ax.set_xlabel("Distance (m)")
        self.ax.set_ylabel("Penetration (mm)")
        self.ax.grid(True, linestyle=":", alpha=0.6)
        self.ax.legend(fontsize=8, loc='upper right')
        self.canvas.draw()