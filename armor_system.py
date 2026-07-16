import json
import os

DB_FILE = "armor_db.json"

# DİKKAT: Anahtar kelimeler YOLO'nun eğittiği Türkçe isimlerle BİREBİR aynıdır.
# Resim yolları da senin orijinal Türkçe klasör isimlerine göre ayarlandı.
DEFAULT_TEMPLATES = {
    "Abrams": {
        "Abrams kule yanak": {"KE": 850, "CE": 430, "IMG": r"tank parçaları resimleri\Abrams kule yanak.jpg"},
        "Abrams kule yan":   {"KE": 350, "CE": 750, "IMG": r"tank parçaları resimleri\Abrams kule yan.jpg"},
        "Abrams kule arka":  {"KE": 100, "CE": 200, "IMG": r"tank parçaları resimleri\Abrams kule arka.jpg"},
        "Abrams kule kalkan":{"KE": 250, "CE": 620, "IMG": r"tank parçaları resimleri\Abrams kule kalkan.jpg"},
        "Abrams govde on":   {"KE": 430, "CE": 680, "IMG": r"tank parçaları resimleri\Abrams govde on.jpg"},
        "Abrams govde yan":  {"KE": 200, "CE": 450, "IMG": r"tank parçaları resimleri\Abrams govde yan.jpg"},
        "Abrams govde arka": {"KE": 60,  "CE": 100, "IMG": r"tank parçaları resimleri\Abrams govde arka.jpg"}
    },
    "Leopard 2A4": {
        "Leo Kule yanak":    {"KE": 750, "CE": 1100, "IMG": r"tank parçaları resimleri\Leo 2A4 Kule Yanak.jpg"},
        "Leo Kule kalkan":   {"KE": 600, "CE": 850,  "IMG": r"tank parçaları resimleri\Leo2A4 kalkan.jpg"},
        "Leo Kule yan":      {"KE": 300, "CE": 700,  "IMG": r"tank parçaları resimleri\Leo 2A4 kule yan.png"},
        "Leo Kule nişancı":  {"KE": 600, "CE": 850,  "IMG": r"tank parçaları resimleri\Leo 2A4 nisanci optigi.jpg"},
        "Leo Kule arka":     {"KE": 132, "CE": 215,  "IMG": r"tank parçaları resimleri\Leo 2A4 kule Arka.png"},
        "Leo Gövde Ön Üst":  {"KE": 390, "CE": 700,  "IMG": r"tank parçaları resimleri\Leo 2A4 govde ön üst.png"},
        "Leo Gövde ön":      {"KE": 550, "CE": 750,  "IMG": r"tank parçaları resimleri\Leo 2A4 Govde on.png"},
        "Leo Gövde ön alt":  {"KE": 350, "CE": 0,    "IMG": r"tank parçaları resimleri\Leo 2A4 govde onu alt.png"},
        "Leo Gövde yan":     {"KE": 350, "CE": 500,  "IMG": r"tank parçaları resimleri\Leo 2A4 govde yan.png"},
        "Leo Gövde arka":    {"KE": 71,  "CE": 261,  "IMG": r"tank parçaları resimleri\Leo 2A4 govde arka.png"}
    },
    "T-14 Armata": {
        "armt Kule ön":      {"KE": 55,  "CE": 200,  "IMG": r"tank parçaları resimleri\armata kule ön.png"},
        "armt Kule genel":   {"KE": 0,   "CE": 0,    "IMG": r"tank parçaları resimleri\armata kule genel.png"},
        "armt Gövde Ön":     {"KE": 1100,"CE": 1500, "IMG": r"tank parçaları resimleri\Armata Gövde ön.jpg"},
        "armt Gövde Ön alt": {"KE": 250, "CE": 0,    "IMG": r"tank parçaları resimleri\Armata gövde ön alt.jpg"},
        "armt Gövde Yan":    {"KE": 400, "CE": 900,  "IMG": r"tank parçaları resimleri\armata gövde yan.png"},
        "armt Gövde Arka":   {"KE": 400, "CE": 900,  "IMG": r"tank parçaları resimleri\armata gövde arka.jpg"}
    }
}

def load_db():
    """Loads armor data from JSON, creates default if not exists."""
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    """Saves armor data to JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Global variable to hold the loaded data
TANK_TEMPLATES = load_db()