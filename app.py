import streamlit as st
from ultralytics import YOLO
import cv2
from PIL import Image
import numpy as np
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="EcoWarrior AI", page_icon="🌍", layout="wide")

# CUSTOM CSS: Fixed Instruction Visibility & Whimsical Theme
st.markdown("""
    <style>
    /* Whimsical Background with a modern clean look */
    .main { 
        background-color: #f7fdf7; 
        background-image: url("https://img.icons8.com/plasticine/400/globe.png");
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: bottom right;
        background-size: 200px;
    }

    /* HIGH VISIBILITY Instruction Box: Dark Green with White Text */
    .instruction-box { 
        background-color: #1e8449; 
        color: #ffffff !important; 
        padding: 25px; 
        border-radius: 20px; 
        border: 4px solid #2ecc71; 
        margin-bottom: 25px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
    }
    .instruction-box strong { color: #ffffff !important; font-size: 20px; }

    [data-testid="stMetricValue"] { color: #1e8449 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #2c3e50 !important; font-size: 18px !important; }
    .stProgress > div > div > div > div { background-color: #2ecc71; }
    
    /* Modern Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 50px;
        background-color: #1e8449;
        color: white;
        font-weight: bold;
        border: none;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOAD MODEL ---
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt') 

model = load_model()

# --- 3. SESSION STATE ---
if 'eco_credits' not in st.session_state: st.session_state.eco_credits = 0
if 'total_co2' not in st.session_state: st.session_state.total_co2 = 0.0
if 'history' not in st.session_state: st.session_state.history = []
if 'scan_complete' not in st.session_state: st.session_state.scan_complete = False

# --- 4. DYNAMIC GOALS ---
current_pts_goal = 1000 * ((st.session_state.eco_credits // 1000) + 1)
current_co2_goal = 5.0 * ((st.session_state.total_co2 // 5.0) + 1)

# --- 5. UI DASHBOARD ---
st.title("🛡️ Smart Bin AI: Global Impact Tracker")

# Progress Bars
c1, c2 = st.columns(2)
with c1:
    st.write(f"**Eco-Credit Progress (Goal: {current_pts_goal})**")
    st.progress(min(st.session_state.eco_credits / current_pts_goal, 1.0))
with c2:
    st.write(f"**CO2 Offset Progress (Goal: {current_co2_goal:.1f}kg)**")
    st.progress(min(st.session_state.total_co2 / current_co2_goal, 1.0))

# Metrics
m1, m2, m3 = st.columns(3)
with m1: st.metric("🌟 Total Points", f"{st.session_state.eco_credits}")
with m2: st.metric("🌱 CO2 Saved", f"{st.session_state.total_co2:.3f} kg")
with m3:
    rank = "Seedling"
    if st.session_state.eco_credits > 1000: rank = "Eco-Guardian"
    st.metric("Current Rank", rank)

st.write("---")

# --- 6. VISIBLE INSTRUCTIONS ---
st.markdown("""
<div class="instruction-box">
    <strong>🚀 Quick Guide:</strong><br>
    1. Hold your waste item (Plastic, Paper, Metal, Glass, or E-Waste) 1-2 feet away.<br>
    2. Click 'Take Photo'. <br>
    3. Follow the disposal instruction to earn your Eco-Credits!
</div>
""", unsafe_allow_html=True)

# Mapping Logic with Detailed Disposal Instructions
BIN_LOGIC = {
    'plastic': {'cat': 'PLASTIC', 'pts': 50, 'co2': 1.08, 'inst': '🧼 **Rinse & Flatten:** Remove caps and labels. Place in the Blue Recycling Bin.'},
    'paper': {'cat': 'PAPER', 'pts': 30, 'co2': 0.46, 'inst': '📝 **Keep it Dry:** Ensure there are no food stains. Place in the Paper Bin.'},
    'metal': {'cat': 'METAL', 'pts': 150, 'co2': 8.14, 'inst': '🦾 **Empty & Clean:** Rinse food cans. Place in the Metal/Silver Recycling Bin.'},
    'ewaste': {'cat': 'E-WASTE', 'pts': 200, 'co2': 1.40, 'inst': '🛑 **Special Disposal:** Contains toxins. Take to your nearest authorized E-Waste collection hub.'},
    'glass': {'cat': 'GLASS', 'pts': 80, 'co2': 0.67, 'inst': '🫙 **Handle Gently:** Ensure it is not broken. Place in the designated Green Glass Bin.'}
}

# Scanner Logic
if not st.session_state.scan_complete:
    img_file = st.camera_input("📷 Live AI Scanner")
    if img_file:
        image = Image.open(img_file)
        results = model.predict(np.array(image), conf=0.18)
        
        found = False
        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls[0])].lower()
                match = None
                
                # Class Mapping
                if label in ['bottle', 'cup']: match = 'plastic'
                elif label in ['cell phone', 'laptop', 'mouse']: match = 'ewaste'
                elif label in ['book', 'handbag']: match = 'paper'
                elif label in ['can']: match = 'metal'
                elif label in ['wine glass', 'vase']: match = 'glass'

                if match:
                    data = BIN_LOGIC[match]
                    st.session_state.eco_credits += data['pts']
                    st.session_state.total_co2 += data['co2']
                    st.session_state.history.insert(0, f"♻️ {data['cat']} -> +{data['pts']} pts")
                    
                    
                    
                    # DISPLAYING THE DISPOSAL INSTRUCTION
                    st.success(f"## 🎉 GREAT JOB! THIS IS {data['cat']}!")
                    st.info(f"### 💡 **Disposal Instruction:** \n {data['inst']}")
                    
                    st.session_state.scan_complete = True
                    time.sleep(1) # Small delay for the user to read
                    st.rerun()
                    found = True
                    break
            if found: break
        
        if not found and img_file:
            st.error("### 🧐 Object not scanned properly!")
            st.warning("I couldn't identify that. Please try moving closer or adjusting the light! 📸")
else:
    # After a successful scan, show the result and the next button
    if st.session_state.history:
        latest = st.session_state.history[0]
        st.write(f"### Last Scanned: {latest}")

    if st.button("🌟 SCAN NEXT ITEM 🌟"):
        st.session_state.scan_complete = False
        st.rerun()

if st.session_state.history:
    st.write("---")
    st.write("### 📜 Recents")
    for entry in st.session_state.history[:3]:
        st.write(entry)
