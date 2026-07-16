# AI-Tank-Armor-Analyzer
AI-powered armor penetration analysis system using YOLOv8 and Gemini LLM

<img width="957" height="487" alt="resim 2" src="https://github.com/user-attachments/assets/a4a5ccd1-03a2-4975-bf70-5d98410c0748" />
<img width="956" height="493" alt="resim 1" src="https://github.com/user-attachments/assets/fceb20f5-2ab4-4711-8686-6460b581056d" />

# 📥 Installation

1. Clone the repository:

`git clone https://github.com/Arkhanus185/AI-Tank-Armor-Analyzer.git
cd AI-Tank-Armor-Analyzer `


2. Install required dependencies:

`pip install -r requirements.txt`


3. Set up the API Key:
To use the Gemini LLM engine, you must provide your own API key.

Open `main_app.py` in your editor.

Locate the `GEMINI_API_KEY` variable at the top of the file.

Replace the placeholder with your actual Google Gemini API key.

`GEMINI_API_KEY = "YOUR_API_KEY_HERE"`


# 🚀 Usage

Running the Main Application:
Start the tactical interface by running:

`python main_app.py`


Click **"Load Image 📂"** to select a target image.

Select your AI Engine, Ammunition, and Gun from the left panel.

Adjust the distance using the slider.

Click **"ANALYZE TARGET 🎯"** to view real-time penetration results on the detected armor parts.

Managing the Database:
<img width="960" height="491" alt="resim 4" src="https://github.com/user-attachments/assets/4fc4fde1-f923-4543-889b-2dd4b9c0e4b3" />
<img width="952" height="487" alt="resim 3" src="https://github.com/user-attachments/assets/c100fa5e-069c-4730-b494-92007e297407" />

You can launch the Database Manager directly from the main app or run it standalone to modify military data:

`python db_manager.py`


# 📊 Academic Resources & Training Data

Please Note: The ballistics and armor resistance data provided in the default JSON databases (armor_db.json, ammo_db.json) are open, representative estimates intended for "Proof of Concept" purposes; they are not real.

Training Graphs & Metrics:
The full training results, precision-recall curves, F1-score graphs, and confusion matrices for the YOLO models (v8s, 11s, 26s) are available in the [Releases](https://github.com/Arkhanus185/AI-Tank-Armor-Analyzer/releases/tag/v1.0) section as a ZIP file and also [here](https://app.roboflow.com/deneme-w6wjd/leopard-abrams-with-parts-armata/browse?queryText=&pageSize=50&startingIndex=0&browseQuery=true) is the model dataset used in yolo training.

# 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
