import customtkinter as ctk
from tkinter import filedialog, simpledialog, messagebox
import ammo_system as ms
import armor_system as tz
import copy

class DatabaseManager(ctk.CTkToplevel):
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.title("Database Manager (Advanced UI)")
        self.geometry("1200x800")
        self.callback = callback 

        # We work on a deep copy to allow canceling without saving
        self.temp_ammo = copy.deepcopy(ms.AMMO_DATABASE)
        self.temp_armor = copy.deepcopy(tz.TANK_TEMPLATES)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_ammo = self.tabview.add("Ammo Database")
        self.tab_armor = self.tabview.add("Armor Database")

        self.build_ammo_tab()
        self.build_armor_tab()

        # BOTTOM BUTTONS (SAVE / CANCEL)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Cancel & Close", fg_color="#b30000", hover_color="#800000", command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="SAVE ALL DATABASES", fg_color="#146c2e", hover_color="#0f5223", font=("Arial", 14, "bold"), command=self.save_all).pack(side="right", padx=5)

    # ==========================================
    # AMMO (MÜHİMMAT) SEKMESİ
    # ==========================================
    def build_ammo_tab(self):
        self.tab_ammo.grid_columnconfigure(0, weight=1)
        self.tab_ammo.grid_columnconfigure(1, weight=3)
        self.tab_ammo.grid_rowconfigure(0, weight=1)

        # LEFT: AMMO LIST
        left_panel = ctk.CTkFrame(self.tab_ammo, width=250)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(left_panel, text="Ammo Types", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.ammo_list_frame = ctk.CTkScrollableFrame(left_panel)
        self.ammo_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkButton(left_panel, text="+ Add New Ammo", fg_color="#3B8ED0", command=self.add_new_ammo).pack(fill="x", padx=5, pady=10)

        # RIGHT: EDITOR
        self.ammo_edit_frame = ctk.CTkScrollableFrame(self.tab_ammo)
        self.ammo_edit_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.ammo_edit_frame, text="Select or create an ammo to edit", text_color="gray").pack(pady=50)

        self.refresh_ammo_list()

    def refresh_ammo_list(self, select_name=None):
        for widget in self.ammo_list_frame.winfo_children():
            widget.destroy()
            
        for ammo_name in self.temp_ammo.keys():
            btn = ctk.CTkButton(self.ammo_list_frame, text=ammo_name, fg_color="gray30", anchor="w",
                                command=lambda n=ammo_name: self.load_ammo_editor(n))
            btn.pack(fill="x", pady=2)
            if ammo_name == select_name:
                self.load_ammo_editor(ammo_name)

    def add_new_ammo(self):
        new_name = simpledialog.askstring("New Ammo", "Enter Ammo Name:", parent=self)
        if new_name and new_name not in self.temp_ammo:
            self.temp_ammo[new_name] = {"type": "KE", "color": "gray", "guns": {}, "IMG": ""}
            self.refresh_ammo_list(select_name=new_name)

    def load_ammo_editor(self, ammo_name):
        for widget in self.ammo_edit_frame.winfo_children(): widget.destroy()
        data = self.temp_ammo[ammo_name]

        ctk.CTkLabel(self.ammo_edit_frame, text=f"Editing: {ammo_name}", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=10, anchor="w", padx=10)

        # BASIC INFO FRAME
        info_frame = ctk.CTkFrame(self.ammo_edit_frame)
        info_frame.pack(fill="x", pady=5, padx=10)
        
        # Type
        ctk.CTkLabel(info_frame, text="Damage Type:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        opt_type = ctk.CTkOptionMenu(info_frame, values=["KE", "CE"], command=lambda v, d=data: d.update({"type": v}))
        opt_type.set(data.get("type", "KE"))
        opt_type.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Image
        ctk.CTkLabel(info_frame, text="Image Path:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        e_img = ctk.CTkEntry(info_frame, width=300)
        e_img.insert(0, data.get("IMG", ""))
        e_img.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        e_img.bind("<KeyRelease>", lambda e, d=data, w=e_img: d.update({"IMG": w.get()}))
        
        btn_browse_ammo = ctk.CTkButton(info_frame, text="📂", width=30, command=lambda: self.browse_image(data, e_img))
        btn_browse_ammo.grid(row=1, column=2, padx=5, pady=5)
        
        # GUNS AND BALLISTIC POINTS
        ctk.CTkLabel(self.ammo_edit_frame, text="Guns & Ballistic Data", font=("Arial", 16, "bold")).pack(pady=(20,5), anchor="w", padx=10)
        
        for gun_name, points in data.get("guns", {}).items():
            gun_frame = ctk.CTkFrame(self.ammo_edit_frame, fg_color="gray20", border_width=1, border_color="gray40")
            gun_frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(gun_frame, text=f"Gun: {gun_name}", font=("Arial", 14, "bold"), text_color="orange").pack(pady=5, anchor="w", padx=10)
            
            # Table Headers
            header = ctk.CTkFrame(gun_frame, fg_color="transparent")
            header.pack(fill="x", padx=10)
            ctk.CTkLabel(header, text="Distance (m)", width=120, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(header, text="Penetration (mm)", width=120, anchor="w").pack(side="left", padx=5)

            # Rows (Points)
            for i, (dist, pen) in enumerate(points):
                row = ctk.CTkFrame(gun_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=2)
                
                e_dist = ctk.CTkEntry(row, width=120)
                e_dist.insert(0, str(dist))
                e_dist.pack(side="left", padx=5)
                
                e_pen = ctk.CTkEntry(row, width=120)
                e_pen.insert(0, str(pen))
                e_pen.pack(side="left", padx=5)
                
                btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="#800000", hover_color="#b30000", 
                                        command=lambda g=gun_name, idx=i: self.delete_ammo_point(ammo_name, g, idx))
                btn_del.pack(side="left", padx=5)
                
                # Update logic
                e_dist.bind("<KeyRelease>", lambda e, d=data, g=gun_name, idx=i, w=e_dist: self.update_ammo_point(d, g, idx, 0, w.get()))
                e_pen.bind("<KeyRelease>", lambda e, d=data, g=gun_name, idx=i, w=e_pen: self.update_ammo_point(d, g, idx, 1, w.get()))

            # + Add Point Button (Bottom of each gun table)
            ctk.CTkButton(gun_frame, text="+ Add Point", fg_color="#146c2e", width=100, height=24,
                          command=lambda g=gun_name: self.add_ammo_point(ammo_name, g)).pack(pady=10, anchor="w", padx=15)

        # + Add Gun Button
        ctk.CTkButton(self.ammo_edit_frame, text="+ Add New Gun", border_width=1, fg_color="transparent", 
                      command=lambda a=ammo_name: self.add_new_gun(a)).pack(pady=10, padx=10, anchor="w")

    def add_new_gun(self, ammo_name):
        gun_name = simpledialog.askstring("New Gun", "Enter Gun Name (e.g., 'L/55 Leopard'):", parent=self)
        if gun_name and gun_name not in self.temp_ammo[ammo_name]["guns"]:
            self.temp_ammo[ammo_name]["guns"][gun_name] = [(0, 0)] # Default starting point
            self.load_ammo_editor(ammo_name)

    def add_ammo_point(self, ammo_name, gun_name):
        self.temp_ammo[ammo_name]["guns"][gun_name].append((0, 0))
        self.load_ammo_editor(ammo_name)

    def delete_ammo_point(self, ammo_name, gun_name, index):
        if len(self.temp_ammo[ammo_name]["guns"][gun_name]) > 1:
            del self.temp_ammo[ammo_name]["guns"][gun_name][index]
            self.load_ammo_editor(ammo_name)
        else:
            messagebox.showwarning("Warning", "A gun must have at least one ballistic point.")

    def update_ammo_point(self, data, gun_name, index, coordinate, value):
        try:
            val = float(value)
            point = list(data["guns"][gun_name][index])
            point[coordinate] = val
            data["guns"][gun_name][index] = tuple(point)
        except ValueError:
            pass 

    # ==========================================
    # ARMOR (ZIRH) SEKMESİ
    # ==========================================
    def build_armor_tab(self):
        self.tab_armor.grid_columnconfigure(0, weight=1)
        self.tab_armor.grid_columnconfigure(1, weight=3)
        self.tab_armor.grid_rowconfigure(0, weight=1)

        # LEFT: TANK LIST
        left_panel = ctk.CTkFrame(self.tab_armor, width=250)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(left_panel, text="Tank Models", font=("Arial", 16, "bold")).pack(pady=10)

        self.armor_list_frame = ctk.CTkScrollableFrame(left_panel)
        self.armor_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkButton(left_panel, text="+ Add New Tank", fg_color="#3B8ED0", command=self.add_new_tank).pack(fill="x", padx=5, pady=10)

        # RIGHT: EDITOR
        self.armor_edit_frame = ctk.CTkScrollableFrame(self.tab_armor)
        self.armor_edit_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.armor_edit_frame, text="Select or create a tank to edit parts", text_color="gray").pack(pady=50)

        self.refresh_armor_list()

    def refresh_armor_list(self, select_name=None):
        for widget in self.armor_list_frame.winfo_children():
            widget.destroy()
            
        for tank_name in self.temp_armor.keys():
            btn = ctk.CTkButton(self.armor_list_frame, text=tank_name, fg_color="gray30", anchor="w",
                                command=lambda n=tank_name: self.load_armor_editor(n))
            btn.pack(fill="x", pady=2)
            if tank_name == select_name:
                self.load_armor_editor(tank_name)

    def add_new_tank(self):
        new_name = simpledialog.askstring("New Tank", "Enter Tank Name (e.g., 'Challenger 2'):", parent=self)
        if new_name and new_name not in self.temp_armor:
            self.temp_armor[new_name] = {}
            self.refresh_armor_list(select_name=new_name)

    def load_armor_editor(self, tank_name):
        for widget in self.armor_edit_frame.winfo_children(): widget.destroy()
        data = self.temp_armor[tank_name]

        ctk.CTkLabel(self.armor_edit_frame, text=f"{tank_name} - Armor Parts", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=10, anchor="w", padx=10)

        # Table Headers
        header = ctk.CTkFrame(self.armor_edit_frame, fg_color="gray30")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text="Part Name", width=180, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="KE (mm)", width=70, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="CE (mm)", width=70, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Image Path", width=150, anchor="w").pack(side="left", padx=5)

        for part_name, part_data in data.items():
            row = ctk.CTkFrame(self.armor_edit_frame, fg_color="gray20", border_width=1, border_color="gray40")
            row.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(row, text=part_name, width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5, pady=5)
            
            e_ke = ctk.CTkEntry(row, width=70)
            e_ke.insert(0, str(part_data.get("KE", 0)))
            e_ke.pack(side="left", padx=5)
            e_ke.bind("<KeyRelease>", lambda e, d=part_data, k="KE", w=e_ke: self.update_armor_val(d, k, w.get()))
            
            e_ce = ctk.CTkEntry(row, width=70)
            e_ce.insert(0, str(part_data.get("CE", 0)))
            e_ce.pack(side="left", padx=5)
            e_ce.bind("<KeyRelease>", lambda e, d=part_data, k="CE", w=e_ce: self.update_armor_val(d, k, w.get()))

            e_img = ctk.CTkEntry(row, width=200)
            e_img.insert(0, part_data.get("IMG", ""))
            e_img.pack(side="left", padx=5)
            e_img.bind("<KeyRelease>", lambda e, d=part_data, k="IMG", w=e_img: d.update({k: w.get()}))
            
            btn_browse = ctk.CTkButton(row, text="📂", width=30, command=lambda d=part_data, w=e_img: self.browse_image(d, w))
            btn_browse.pack(side="left", padx=5)

        # + Add Part Button
        ctk.CTkButton(self.armor_edit_frame, text="+ Add New Part", border_width=1, fg_color="transparent", 
                      command=lambda t=tank_name: self.add_new_part(t)).pack(pady=15, padx=10, anchor="w")

    def add_new_part(self, tank_name):
        part_name = simpledialog.askstring("New Part", f"Enter Part Name for {tank_name}\n(e.g., 'Challenger Turret Cheek'):", parent=self)
        if part_name and part_name not in self.temp_armor[tank_name]:
            self.temp_armor[tank_name][part_name] = {"KE": 0, "CE": 0, "IMG": ""}
            self.load_armor_editor(tank_name)

    def update_armor_val(self, part_dict, key, value):
        try:
            part_dict[key] = float(value)
        except ValueError:
            pass

    # ==========================================
    # COMMON FUNCTIONS
    # ==========================================
    def browse_image(self, target_dict, entry_widget):
        path = filedialog.askopenfilename(parent=self, filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            target_dict["IMG"] = path
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, path)

    def save_all(self):
        try:
            # Transfer temporary data to main modules and save to JSON
            ms.AMMO_DATABASE = self.temp_ammo
            ms.save_db(ms.AMMO_DATABASE)
            
            tz.TANK_TEMPLATES = self.temp_armor
            tz.save_db(tz.TANK_TEMPLATES)
            
            messagebox.showinfo("Success", "All databases saved successfully! The UI will now reload.")
            if self.callback: self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save databases:\n{e}")

if __name__ == "__main__":
    app = ctk.CTk()
    db = DatabaseManager(app)
    app.mainloop()