import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk
import cv2
import numpy as np
from ultralytics import YOLO

# Tank şablonumuzda olan Abrams sınıfları
abrams_parcalari = [
    "Abrams kule yanak", "Abrams kule yan", "Abrams kule arka",
    "Abrams kule kalkan", "Abrams govde on", "Abrams govde yan", "Abrams govde arka"
]

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


class FilterTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mekansal Filtre (SBF) Test Arayüzü - Zoom Destekli")
        self.geometry("1300x750")
        ctk.set_appearance_mode("Dark")

        # Modeli Yükle
        self.model = YOLO("best.pt")
        self.img_path = None
        self.img_cv2 = None

        # --- SOL PANEL (KONTROLLER) ---
        self.left_panel = ctk.CTkFrame(self, width=320)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.left_panel, text="FİLTRE TESTİ", font=("Arial", 20, "bold"), text_color="#3B8ED0").pack(pady=(20, 10))

        ctk.CTkButton(self.left_panel, text="Görüntü Yükle 📂", height=40, command=self.load_image).pack(pady=10, padx=20, fill="x")

        # Filtre Anahtarı (Switch)
        self.filter_var = ctk.BooleanVar(value=False)
        self.switch = ctk.CTkSwitch(self.left_panel, text="Mekansal Filtreyi Aç", font=("Arial", 14, "bold"), 
                                    variable=self.filter_var, command=self.run_analysis)
        self.switch.pack(pady=20)

        ctk.CTkFrame(self.left_panel, height=2, fg_color="gray30").pack(fill="x", pady=10, padx=10)

        # İstatistik Etiketleri
        self.lbl_total = ctk.CTkLabel(self.left_panel, text="Bulunan Ham Maske: 0", font=("Arial", 15, "bold"))
        self.lbl_total.pack(pady=10, anchor="w", padx=20)

        self.lbl_blocked = ctk.CTkLabel(self.left_panel, text="Ekrana Yansıyan Hata: 0", font=("Arial", 15, "bold"), text_color="#ff4d4d")
        self.lbl_blocked.pack(pady=10, anchor="w", padx=20)

        self.lbl_valid = ctk.CTkLabel(self.left_panel, text="Geçerli Doğru Maske: 0", font=("Arial", 15, "bold"), text_color="#2cc985")
        self.lbl_valid.pack(pady=10, anchor="w", padx=20)

        # --- SAĞ PANEL (GÖRÜNTÜLEYİCİ - ZOOM DESTEKLİ) ---
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.image_viewer = ZoomableImageCanvas(self.right_panel)
        self.image_viewer.pack(fill="both", expand=True, padx=5, pady=5)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            self.img_path = path
            self.img_cv2 = cv2.imread(path)
            self.run_analysis() # Resim yüklenince otomatik çalıştır

    def run_analysis(self):
        if self.img_cv2 is None: return

        img_copy = self.img_cv2.copy()
        overlay = img_copy.copy()
        
        # YOLO Tespiti (Çok ufak detayları da yakalamak için conf=0.3)
        results = self.model(self.img_path, conf=0.3, verbose=False)
        
        toplam_tespit = 0
        engellenen = 0
        gecerli = 0

        for result in results:
            if not hasattr(result, 'boxes') or result.boxes is None or len(result.boxes) == 0:
                continue 

            other_tank_boxes = []
            
            for i, box in enumerate(result.boxes.xyxy):
                cls_name = result.names[int(result.boxes.cls[i])]
                x1, y1, x2, y2 = map(int, box)
                
                # YOLO'nun çalıştığını görmek için ana tank kutularını ekrana çizdiriyoruz
                if cls_name in ["Abrams", "Leopard 2A4", "T-14 Armata"]:
                    box_color = (255, 200, 0) if cls_name != "Abrams" else (0, 255, 255)
                    cv2.rectangle(img_copy, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(img_copy, cls_name, (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2, cv2.LINE_AA)

                # Leopard veya Armata ise filtrenin kısıtlama (engel) listesine ekle
                if cls_name in ["Leopard 2A4", "T-14 Armata"]:
                    other_tank_boxes.append([x1, y1, x2, y2])

            if hasattr(result, 'masks') and result.masks is not None:
                for i, mask in enumerate(result.masks.xy):
                    cls_name = result.names[int(result.boxes.cls[i])]
                    
                    if cls_name in abrams_parcalari:
                        toplam_tespit += 1
                        
                        part_box = result.boxes.xyxy[i]
                        px1, py1, px2, py2 = map(int, part_box)
                        center_x, center_y = (px1 + px2) / 2, (py1 + py2) / 2
                        
                        inside_other_tank = False
                        
                        # Filtre Mantığı: Merkez nokta (centroid) başka tankın sınırlarında mı?
                        for lx1, ly1, lx2, ly2 in other_tank_boxes:
                            if lx1 <= center_x <= lx2 and ly1 <= center_y <= ly2:
                                inside_other_tank = True
                                break
                        
                        if inside_other_tank:
                            engellenen += 1
                        else:
                            gecerli += 1
                            
                        # Eğer filtre açıksa ve bu maske hatalıysa (başka tanktaysa), SİL (çizme geç)
                        if self.filter_var.get() and inside_other_tank:
                            continue 
                            
                        # Kırmızı = Hatalı Halüsinasyon, Yeşil = Doğru Maske
                        draw_color = (0, 0, 255) if inside_other_tank else (0, 255, 0)
                        
                        pts = np.array(mask, np.int32).reshape((-1, 1, 2))
                        cv2.fillPoly(overlay, [pts], draw_color)
                        cv2.putText(img_copy, cls_name, (px1, py1+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)

        self.lbl_total.configure(text=f"Bulunan Ham Maske: {toplam_tespit}")
        
        if self.filter_var.get():
            self.lbl_blocked.configure(text=f"Filtrenin Sildiği Hata: {engellenen}", text_color="gray")
            self.lbl_valid.configure(text=f"Ekranda Kalan Doğru: {gecerli}")
        else:
            self.lbl_blocked.configure(text=f"Ekrana Yansıyan Hata: {engellenen}", text_color="#ff4d4d")
            self.lbl_valid.configure(text=f"Geçerli Doğru Maske: {gecerli}")

        final_img = cv2.addWeighted(overlay, 0.5, img_copy, 0.5, 0)
        
        # ZoomableImageCanvas'a Numpy Array olarak gönderiyoruz
        self.image_viewer.set_image(final_img, is_array=True)

if __name__ == "__main__":
    app = FilterTestApp()
    app.mainloop()