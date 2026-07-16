import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, Canvas
from PIL import Image, ImageTk
import numpy as np
import cv2
import os
import json
from ultralytics import YOLO
import google.generativeai as genai 
import warnings

# Kırmızı API eskidi uyarısını (FutureWarning) gizle
warnings.filterwarnings("ignore") 

# --- PROJE MODÜLLERİ ---
import ammo_system as ms 
import armor_system as tz    
import db_manager as dbm

# ======================================================================
# LLM API AYARLARI
# ======================================================================
GEMINI_API_KEY = "BURAYA_KENDİ_GİZLİ_API_ANAHTARINI_GİRMELİSİN"
genai.configure(api_key=GEMINI_API_KEY)

class ImageTooltip:
    def __init__(self, widget, image_path=None):
        self.widget = widget
        self.image_path = image_path
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def update_image(self, new_path):
        self.image_path = new_path

    def show_tooltip(self, event=None):
        if self.tooltip_window is not None: return
        if not self.image_path or not os.path.exists(self.image_path): return

        root = self.widget.winfo_toplevel()
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 20
        
        screen_height = root.winfo_screenheight()
        if y + 200 > screen_height:
            y = self.widget.winfo_rooty() - 200

        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) 
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes('-topmost', True)

        try:
            pil_img = Image.open(self.image_path)
            if pil_img.height > pil_img.width:
                pil_img = pil_img.rotate(90, expand=True)
            
            pil_img.thumbnail((220, 180)) 
            ctk_img = ctk.CTkImage(pil_img, size=pil_img.size)

            frame = ctk.CTkFrame(self.tooltip_window, fg_color="#202020", border_width=1, border_color="gray50")
            frame.pack()
            ctk.CTkLabel(frame, text="Visual Reference", font=("Arial", 9, "italic"), text_color="gray").pack(pady=(2,0))
            ctk.CTkLabel(frame, text="", image=ctk_img).pack(padx=5, pady=5)
        except Exception as e:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ZoomableImageCanvas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas = Canvas(self, bg="#101010", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.original_image = None
        self.shown_image = None
        self.scale = 1.0
        self.image_id = None
        self.canvas.bind("<ButtonPress-1>", self.on_move_start)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<MouseWheel>", self.on_zoom)     
        self.canvas.bind("<Button-4>", self.on_zoom)        
        self.canvas.bind("<Button-5>", self.on_zoom)        

    def set_image(self, img_path_or_array, is_array=False):
        if is_array:
            self.original_image = Image.fromarray(cv2.cvtColor(img_path_or_array, cv2.COLOR_BGR2RGB))
        else:
            self.original_image = Image.open(img_path_or_array)
        
        canvas_width = self.canvas.winfo_width() if self.canvas.winfo_width() > 100 else 800
        canvas_height = self.canvas.winfo_height() if self.canvas.winfo_height() > 100 else 600
        img_w, img_h = self.original_image.size
        ratio = min(canvas_width/img_w, canvas_height/img_h)
        self.scale = ratio * 0.9 
        self.redraw_image()
        self.canvas.scan_mark(0, 0)

    def redraw_image(self):
        if not self.original_image: return
        new_w = int(self.original_image.width * self.scale)
        new_h = int(self.original_image.height * self.scale)
        resample_mode = Image.Resampling.NEAREST if self.scale > 2.0 else Image.Resampling.LANCZOS
        resized_pil = self.original_image.resize((new_w, new_h), resample_mode)
        self.shown_image = ImageTk.PhotoImage(resized_pil)
        if self.image_id: self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(0, 0, image=self.shown_image, anchor="nw")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_zoom(self, event):
        if not self.original_image: return
        factor = 0.9 if (event.num == 5 or event.delta < 0) else 1.1
        new_scale = self.scale * factor
        if 0.1 < new_scale < 5.0: 
            self.scale = new_scale
            self.redraw_image()

    def on_move_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

class TankAnalysisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tank Armor Analysis System v7.5 (GitHub Ready & Dynamic DB)")
        self.geometry("1400x900")
        ctk.set_appearance_mode("Dark")
        
        self.loaded_image_path = None
        self.last_analysis_data = [] 
        self.is_sorted = False        

        # LLM Cache Variables
        self.last_llm_image_path = None
        self.last_llm_detected_tanks = set()
        self.last_llm_boxes = []

        # GÖRELİ (RELATIVE) YOLLAR: Sadece klasör isimleri var!
        self.yolo_models = {
            "YOLOv8s (Local - Fast)": "yolov8s-seg/weights/best.pt",
            "YOLO11s (Local - Balanced)": "yolo11s-seg/weights/best.pt",
            "YOLO26s (Local - Accurate)": "yolo26s-seg/weights/best.pt",
            "Gemini 2.5 (Cloud - Smart)": "LLM"
        }
        
        self.current_model = None
        # Uygulama açılışında ilk modeli (YOLOv8) otomatik yüklemeye çalış
        self.load_yolo_model(list(self.yolo_models.keys())[0])

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0) 
        self.grid_rowconfigure(0, weight=1)

        # 1. LEFT PANEL (SIDEBAR)
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="COMMAND PANEL", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=(20, 10))
        
        self.btn_load = ctk.CTkButton(self.sidebar, text="Load Image 📂", height=40, command=self.load_image)
        self.btn_load.pack(pady=5, padx=20, fill="x")

        # AI ENGINE SELECTION
        ctk.CTkLabel(self.sidebar, text="Select AI Engine:", anchor="w", text_color="orange").pack(fill="x", padx=20, pady=(10,0))
        self.opt_ai = ctk.CTkOptionMenu(self.sidebar, values=list(self.yolo_models.keys()), fg_color="gray30", command=self.load_yolo_model)
        self.opt_ai.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.sidebar, text="Select Ammunition:", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.ammo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.ammo_frame.pack(fill="x", padx=20, pady=5)
        
        self.opt_ammo = ctk.CTkOptionMenu(self.ammo_frame, values=list(ms.AMMO_DATABASE.keys()), command=self.update_guns)
        self.opt_ammo.pack(side="left", fill="x", expand=True)
        
        self.btn_ammo_info = ctk.CTkButton(self.ammo_frame, text="👁️", width=40, fg_color="#444444", hover_color="#666666")
        self.btn_ammo_info.pack(side="left", padx=(5,0))
        self.ammo_tooltip = ImageTooltip(self.btn_ammo_info) 

        ctk.CTkLabel(self.sidebar, text="Select Gun:", anchor="w").pack(fill="x", padx=20)
        self.opt_gun = ctk.CTkOptionMenu(self.sidebar, values=["Awaiting Selection"])
        self.opt_gun.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.sidebar, text="Distance:", anchor="w").pack(fill="x", padx=20)
        self.lbl_dist = ctk.CTkLabel(self.sidebar, text="500 m", font=("Arial", 14, "bold"))
        self.lbl_dist.pack()
        
        self.slider = ctk.CTkSlider(self.sidebar, from_=0, to=4000, number_of_steps=400, command=self.update_dist_text)
        self.slider.set(500)
        self.slider.pack(pady=5, padx=20, fill="x")

        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30").pack(fill="x", pady=15, padx=10)

        self.btn_run = ctk.CTkButton(self.sidebar, text="ANALYZE TARGET 🎯", fg_color="#b30000", hover_color="#800000", height=60, font=("Arial", 16, "bold"), command=self.run_analysis)
        self.btn_run.pack(pady=5, padx=20, fill="x")

        self.btn_graph = ctk.CTkButton(self.sidebar, text="BALLISTIC GRAPHS 📈", fg_color="#3B8ED0", command=self.open_graph_window)
        self.btn_graph.pack(pady=5, padx=20, fill="x")

        self.btn_db = ctk.CTkButton(self.sidebar, text="DATABASE MANAGER ⚙️", fg_color="gray40", command=self.open_db_manager)
        self.btn_db.pack(pady=5, padx=20, fill="x")

        # 2. CENTER PANEL (IMAGE VIEWER)
        self.image_viewer = ZoomableImageCanvas(self)
        self.image_viewer.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # 3. RIGHT PANEL (ARMOR REPORT)
        self.right_panel = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.right_panel.grid(row=0, column=2, sticky="nsew")

        ctk.CTkLabel(self.right_panel, text="ARMOR STATUS REPORT", font=("Arial", 18, "bold")).pack(pady=(20, 5))
        
        self.lbl_detected_tank = ctk.CTkLabel(self.right_panel, text="Awaiting Detection...", font=("Arial", 14, "italic"), text_color="orange")
        self.lbl_detected_tank.pack(pady=(0, 10))

        self.header_frame = ctk.CTkFrame(self.right_panel, height=40, fg_color="gray30")
        self.header_frame.pack(fill="x", padx=5)
        
        ctk.CTkLabel(self.header_frame, text="👁️", width=30).pack(side="left", padx=2)
        ctk.CTkLabel(self.header_frame, text="REGION", width=180, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="ARMOR", width=60, anchor="center").pack(side="left", padx=5)
        
        self.btn_sort = ctk.CTkButton(self.header_frame, text="⇩", width=30, fg_color="gray40", command=self.toggle_sort)
        self.btn_sort.pack(side="right", padx=5)

        self.table_frame = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.update_guns(self.opt_ammo.get())

    def load_yolo_model(self, selection):
        path = self.yolo_models[selection]
        if path == "LLM":
            self.current_model = None
            print("Switched to Gemini LLM Engine.")
            return

        try:
            # Geriye dönük uyumluluk: Eğer klasörde bulamazsa ana dizindeki best.pt'ye baksın
            if not os.path.exists(path):
                print(f"Warning: Model not found at '{path}'. Attempting to load default 'best.pt' from root directory.")
                path = 'best.pt'
                
            self.current_model = YOLO(path)
            print(f"Successfully loaded YOLO Model: {selection} (Path: {path})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YOLO model:\n{e}")

    def reload_databases(self):
        """Called when Database Manager updates the JSONs"""
        self.opt_ammo.configure(values=list(ms.AMMO_DATABASE.keys()))
        self.update_guns(self.opt_ammo.get())
        print("Databases reloaded into UI.")

    def open_db_manager(self):
        db_window = dbm.DatabaseManager(self, callback=self.reload_databases)
        db_window.grab_set()

    def update_dist_text(self, val):
        self.lbl_dist.configure(text=f"{int(val)} m")

    def update_guns(self, ammo_choice):
        guns = list(ms.AMMO_DATABASE[ammo_choice]["guns"].keys())
        self.opt_gun.configure(values=guns)
        self.opt_gun.set(guns[0])
        if "IMG" in ms.AMMO_DATABASE[ammo_choice]:
            self.ammo_tooltip.update_image(ms.AMMO_DATABASE[ammo_choice]["IMG"])
        else:
            self.ammo_tooltip.update_image(None)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
        if path:
            self.loaded_image_path = path
            self.image_viewer.set_image(path)
            for widget in self.table_frame.winfo_children(): widget.destroy()
            self.lbl_detected_tank.configure(text="Awaiting Detection...", text_color="orange")
            self.last_analysis_data = []

    def run_analysis(self):
        if not self.loaded_image_path:
            messagebox.showwarning("Warning", "Please load an image first!")
            return

        ai_engine = self.opt_ai.get()
        if "YOLO" in ai_engine:
            self.run_yolo_analysis()
        else:
            self.run_llm_analysis()

    def run_yolo_analysis(self):
        if not self.current_model: return

        ammo_name = self.opt_ammo.get()
        gun_name = self.opt_gun.get()
        dist = int(self.slider.get())
        penetration = ms.calculate_penetration(ammo_name, gun_name, dist)
        ammo_type = ms.AMMO_DATABASE[ammo_name]["type"]

        img_cv2 = cv2.imread(self.loaded_image_path)
        overlay = img_cv2.copy() 
        results = self.current_model(self.loaded_image_path, conf=0.5)
        
        detected_parts = set()
        detected_main_tanks = set()
        other_tank_boxes = []

        # Dinamik tank listesi kontrolü için
        tank_names = list(tz.TANK_TEMPLATES.keys())

        for result in results:
            for i, box in enumerate(result.boxes.xyxy):
                cls_name = result.names[int(result.boxes.cls[i])]
                # Eğer tespit edilen şey bir ana tank ise ve Abrams değilse (Spatial Filter mantığı için)
                if cls_name in tank_names and cls_name != "Abrams":
                    other_tank_boxes.append(box)

            for i, box in enumerate(result.boxes.xyxy):
                cls_name = result.names[int(result.boxes.cls[i])]
                x1, y1, x2, y2 = map(int, box)
                
                if cls_name in tank_names:
                    detected_main_tanks.add(cls_name)
                    cv2.rectangle(img_cv2, (x1, y1), (x2, y2), (0, 255, 255), 3) 
                    cv2.putText(img_cv2, f"{cls_name.upper()} (YOLO)", (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

            if result.masks:
                for i, mask in enumerate(result.masks.xy):
                    cls_name = result.names[int(result.boxes.cls[i])]
                    
                    # Dinamik veritabanındaki Abrams (veya parçalı tank) şablonunu kontrol et
                    if cls_name in tz.TANK_TEMPLATES.get("Abrams", {}):
                        part_box = result.boxes.xyxy[i]
                        px1, py1, px2, py2 = map(int, part_box)
                        center_x, center_y = (px1 + px2) / 2, (py1 + py2) / 2
                        
                        inside_other_tank = False
                        for l_box in other_tank_boxes:
                            lx1, ly1, lx2, ly2 = map(int, l_box)
                            if lx1 <= center_x <= lx2 and ly1 <= center_y <= ly2:
                                inside_other_tank = True
                                break
                        if inside_other_tank: continue 

                        detected_parts.add(cls_name)
                        armor_val = tz.TANK_TEMPLATES["Abrams"][cls_name][ammo_type]
                        color = (0, 255, 0) if penetration > armor_val else (0, 0, 255)
                        pts = np.array(mask, np.int32).reshape((-1, 1, 2))
                        cv2.fillPoly(overlay, [pts], color)

        final_img = cv2.addWeighted(overlay, 0.4, img_cv2, 0.6, 0)
        self.image_viewer.set_image(final_img, is_array=True)
        self.update_table_data(detected_main_tanks, detected_parts, penetration, ammo_type, is_yolo=True)

    def run_llm_analysis(self):
        if GEMINI_API_KEY == "BURAYA_KENDİ_GİZLİ_API_ANAHTARINI_GİRMELİSİN" or GEMINI_API_KEY == "":
            messagebox.showerror("Missing API Key", "Please provide a valid Google Gemini API Key at the top of the code.")
            return

        if self.loaded_image_path == self.last_llm_image_path and self.last_llm_boxes:
            self.lbl_detected_tank.configure(text="Loading from Cache...", text_color="yellow")
            self.update()
            
            img_cv2 = cv2.imread(self.loaded_image_path)
            
            for box_data in self.last_llm_boxes:
                detected_tank, (x1, y1, x2, y2) = box_data
                cv2.rectangle(img_cv2, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.putText(img_cv2, f"{detected_tank.upper()} (LLM-CACHE)", (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
            
            self.image_viewer.set_image(img_cv2, is_array=True)
            
            ammo_name = self.opt_ammo.get()
            gun_name = self.opt_gun.get()
            dist = int(self.slider.get())
            penetration = ms.calculate_penetration(ammo_name, gun_name, dist)
            ammo_type = ms.AMMO_DATABASE[ammo_name]["type"]
            
            self.update_table_data(self.last_llm_detected_tanks, set(), penetration, ammo_type, is_yolo=False)
            return 

        self.lbl_detected_tank.configure(text="LLM Inspecting (API)...", text_color="yellow")
        self.update()
        
        try:
            img_pil = Image.open(self.loaded_image_path)
            img_cv2 = cv2.imread(self.loaded_image_path)
            h_img, w_img, _ = img_cv2.shape
            
            # Dinamik olarak güncel tank listesini veritabanından çek
            tank_names = list(tz.TANK_TEMPLATES.keys())
            tank_names_str = ", ".join([f'"{name}"' for name in tank_names])
            
            llm_model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            You are a military AI expert. Identify which of these tanks are in the image: 
            {tank_names_str}.
            
            There might be multiple tanks.
            Return bounding box coordinates [ymin, xmin, ymax, xmax] scaled 0 to 1000.
            
            IMPORTANT: Return ONLY a valid JSON in this exact format. No markdown, no text:
            {{
              "detections": [
                {{"tank_name": "Tank Name Here", "box": [ymin, xmin, ymax, xmax]}}
              ]
            }}
            If none are present, leave "detections" empty.
            """
            
            response = llm_model.generate_content([prompt, img_pil])
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            llm_data = json.loads(raw_text)
            
            detections = llm_data.get("detections", [])
            detected_main_tanks = set()
            
            self.last_llm_image_path = self.loaded_image_path
            self.last_llm_boxes = []
            
            for det in detections:
                detected_tank = det.get("tank_name", "Unknown")
                bbox = det.get("box", [0,0,0,0])
                
                # Tespit edilen tank veritabanımızda var mı kontrol et
                if detected_tank in tank_names:
                    detected_main_tanks.add(detected_tank)
                    
                    ymin, xmin, ymax, xmax = bbox
                    y1 = int((ymin / 1000.0) * h_img)
                    x1 = int((xmin / 1000.0) * w_img)
                    y2 = int((ymax / 1000.0) * h_img)
                    x2 = int((xmax / 1000.0) * w_img)
                    
                    self.last_llm_boxes.append((detected_tank, (x1, y1, x2, y2)))
                    cv2.rectangle(img_cv2, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    cv2.putText(img_cv2, f"{detected_tank.upper()} (LLM)", (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
            
            self.last_llm_detected_tanks = detected_main_tanks 
            self.image_viewer.set_image(img_cv2, is_array=True)
            
            ammo_name = self.opt_ammo.get()
            gun_name = self.opt_gun.get()
            dist = int(self.slider.get())
            penetration = ms.calculate_penetration(ammo_name, gun_name, dist)
            ammo_type = ms.AMMO_DATABASE[ammo_name]["type"]
            
            self.update_table_data(detected_main_tanks, set(), penetration, ammo_type, is_yolo=False)

        except Exception as e:
            messagebox.showerror("LLM Error", f"Failed to communicate or parse JSON.\n\nDetail: {e}")
            self.lbl_detected_tank.configure(text="Awaiting Detection...", text_color="orange")

    def update_table_data(self, detected_main_tanks, detected_parts, penetration, ammo_type, is_yolo=True):
        if detected_main_tanks:
            tank_names_str = ", ".join(list(detected_main_tanks)).upper()
            self.lbl_detected_tank.configure(text=f"Detected: {tank_names_str}", text_color="#2cc985")
        else:
            self.lbl_detected_tank.configure(text="Detected: (Unknown/None)", text_color="gray")

        self.last_analysis_data = []
        temp_display_dict = {}

        if detected_main_tanks:
            for tank_name in detected_main_tanks:
                if tank_name in tz.TANK_TEMPLATES:
                    for part_name, val_dict in tz.TANK_TEMPLATES[tank_name].items():
                        if tank_name == "Abrams":
                            temp_display_dict[part_name] = val_dict
                        else:
                            full_name = f"{tank_name}|{part_name}"
                            temp_display_dict[full_name] = val_dict
        else:
            if is_yolo and "Abrams" in tz.TANK_TEMPLATES:
                temp_display_dict.update(tz.TANK_TEMPLATES["Abrams"])

        for full_key, values in temp_display_dict.items():
            is_relevant = False
            if "Leopard" in full_key and "Leopard 2A4" in detected_main_tanks: is_relevant = True
            elif "T-14" in full_key and "T-14 Armata" in detected_main_tanks: is_relevant = True
            elif "Abrams" in full_key: 
                if "Abrams" in detected_main_tanks or not detected_main_tanks: is_relevant = True
            
            if not is_relevant: continue

            resistance = values[ammo_type]
            if penetration > resistance:
                color, is_pen = "#2cc985", True 
            else:
                color, is_pen = "#ff4d4d", False 

            if "|" in full_key: 
                display_name = full_key.split("|")[1] 
            else: 
                display_name = full_key

            is_detected = (full_key in detected_parts) if is_yolo else False

            item = {
                "name": display_name,
                "resistance": resistance,
                "status_color": color,
                "is_penetrated": is_pen,
                "is_detected": is_detected,
                "img": values.get("IMG", None)
            }
            self.last_analysis_data.append(item)

        self.refresh_table()

    def toggle_sort(self):
        self.is_sorted = not self.is_sorted
        arrow = "⇧" if self.is_sorted else "⇩"
        self.btn_sort.configure(text=f"{arrow}")
        self.refresh_table()

    def refresh_table(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        if not self.last_analysis_data: return

        display_list = self.last_analysis_data.copy()
        if self.is_sorted:
            display_list.sort(key=lambda x: x["is_penetrated"], reverse=True)

        for item in display_list:
            bg_color = "gray20" if item["is_detected"] else "transparent"
            row = ctk.CTkFrame(self.table_frame, fg_color=bg_color)
            row.pack(fill="x", pady=2)
            
            if item["img"]:
                btn_eye = ctk.CTkButton(row, text="👁️", width=30, height=20, fg_color="transparent", hover_color="gray30", text_color="gray80")
                btn_eye.pack(side="left", padx=(2,5))
                ImageTooltip(btn_eye, item["img"])
            else:
                ctk.CTkLabel(row, text="", width=30).pack(side="left", padx=(2,5))

            name_lbl = ctk.CTkLabel(row, text=item["name"], font=("Arial", 12, "bold"), text_color=item["status_color"], width=180, anchor="w")
            name_lbl.pack(side="left", padx=5)

            ctk.CTkLabel(row, text=f"{item['resistance']} mm", width=60).pack(side="left", padx=5)

    def open_graph_window(self):
        window = ms.GraphicWindow(self)
        window.grab_set()

if __name__ == "__main__":
    app = TankAnalysisApp()
    app.mainloop()