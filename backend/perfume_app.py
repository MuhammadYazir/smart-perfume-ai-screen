import streamlit as st
import asyncio
import base64
import os
import json
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv()

# Page config
st.set_page_config(
    page_title="Perfume Recommender",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Midnight Atelier Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Lato:wght@300;400;700&display=swap');
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main background */
    .stApp {
        background-color: #050505;
        background-image: url('https://images.unsplash.com/photo-1684952618317-07377f793d98?w=1920&q=20');
        background-size: cover;
        background-position: center;
        background-blend-mode: overlay;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(5, 5, 5, 0.92);
        z-index: -1;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #F5F5F5 !important;
    }
    
    p, span, label, div {
        font-family: 'Lato', sans-serif !important;
    }
    
    /* Main title */
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        font-weight: 500;
        color: #F5F5F5;
        text-align: center;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-family: 'Lato', sans-serif;
        font-size: 1rem;
        color: #A3A3A3;
        text-align: center;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        margin-bottom: 3rem;
    }
    
    /* Gold accent */
    .gold-text {
        color: #D4AF37 !important;
    }
    
    /* Selection cards */
    .selection-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.4s ease;
        margin: 0.5rem;
    }
    
    .selection-card:hover {
        border-color: rgba(212, 175, 55, 0.5);
        transform: translateY(-4px);
        box-shadow: 0 10px 40px -10px rgba(212, 175, 55, 0.2);
    }
    
    .selection-card.selected {
        border-color: #D4AF37;
        background: rgba(212, 175, 55, 0.1);
    }
    
    .card-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        color: #F5F5F5;
        margin-bottom: 0.5rem;
    }
    
    .card-desc {
        font-family: 'Lato', sans-serif;
        font-size: 0.8rem;
        color: #A3A3A3;
        letter-spacing: 0.1em;
    }
    
    /* Perfume result card */
    .perfume-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.5s ease;
    }
    
    .perfume-card:hover {
        border-color: rgba(212, 175, 55, 0.3);
    }
    
    .perfume-name {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        color: #F5F5F5;
        margin-bottom: 0.5rem;
    }
    
    .match-badge {
        display: inline-block;
        background: linear-gradient(45deg, #8A7020, #D4AF37, #F9E076);
        color: #050505;
        padding: 0.3rem 1rem;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.1em;
        margin-bottom: 1rem;
    }
    
    .scent-notes {
        font-family: 'Lato', sans-serif;
        color: #D4AF37;
        font-size: 0.9rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    
    .description {
        font-family: 'Lato', sans-serif;
        color: #A3A3A3;
        font-size: 1rem;
        line-height: 1.8;
    }
    
    /* Buttons */
    .stButton > button {
        background: #D4AF37 !important;
        color: #050505 !important;
        border: none !important;
        padding: 1rem 3rem !important;
        font-family: 'Lato', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        border-radius: 0 !important;
    }
    
    .stButton > button:hover {
        background: #F9E076 !important;
        transform: translateY(-2px);
    }
    
    /* Secondary button */
    .secondary-btn > button {
        background: transparent !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }
    
    .secondary-btn > button:hover {
        background: #D4AF37 !important;
        color: #050505 !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #F5F5F5 !important;
        border-radius: 0 !important;
    }
    
    .stSelectbox label {
        color: #D4AF37 !important;
        font-family: 'Lato', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed rgba(212, 175, 55, 0.3) !important;
        background: rgba(255, 255, 255, 0.02) !important;
        padding: 2rem !important;
    }
    
    .stFileUploader:hover {
        border-color: #D4AF37 !important;
    }
    
    /* Divider */
    .gold-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #D4AF37, transparent);
        margin: 3rem 0;
    }
    
    /* Section header */
    .section-header {
        font-family: 'Lato', sans-serif;
        font-size: 0.8rem;
        color: #D4AF37;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }
    
    /* Image container */
    .perfume-image-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 1rem;
    }
    
    .perfume-image-container img {
        max-height: 300px;
        object-fit: contain;
        filter: drop-shadow(0 20px 40px rgba(212, 175, 55, 0.2));
    }
    
    /* Radio buttons styling */
    .stRadio > div {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .stRadio label {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1rem 2rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        color: #F5F5F5 !important;
    }
    
    .stRadio label:hover {
        border-color: rgba(212, 175, 55, 0.5) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #D4AF37 !important;
    }
    
    /* Upload section */
    .upload-section {
        background: rgba(255, 255, 255, 0.02);
        border: 2px dashed rgba(212, 175, 55, 0.3);
        padding: 3rem;
        text-align: center;
        margin-top: 2rem;
    }
    
    .upload-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        color: #F5F5F5;
        margin-bottom: 0.5rem;
    }
    
    .upload-desc {
        font-family: 'Lato', sans-serif;
        font-size: 0.9rem;
        color: #A3A3A3;
    }
</style>
""", unsafe_allow_html=True)

# Perfume images database
PERFUME_IMAGES = {
    "woody": "https://images.unsplash.com/photo-1643797519086-cc9a821fbcfe?w=400&q=80",
    "floral": "https://images.unsplash.com/photo-1643797517590-c44cb552ddcc?w=400&q=80",
    "fresh": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=400&q=80",
    "musky": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=400&q=80",
    "oriental": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=400&q=80",
    "default": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=400&q=80"
}

def get_perfume_image(scent_type):
    """Get appropriate image based on scent type"""
    scent_lower = scent_type.lower() if scent_type else ""
    for key in PERFUME_IMAGES:
        if key in scent_lower:
            return PERFUME_IMAGES[key]
    return PERFUME_IMAGES["default"]

async def get_perfume_recommendations(preferences):
    """Get AI-powered perfume recommendations"""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"error": "API key not configured"}
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"perfume-rec-{preferences.get('gender', 'user')}",
        system_message="""You are a world-renowned perfume expert and luxury fragrance consultant. 
Your recommendations are precise, sophisticated, and tailored to each customer's unique profile.
Always respond in valid JSON format."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Based on these preferences, recommend 2 perfect perfumes:

Customer Profile:
- Gender: {preferences.get('gender', 'Any')}
- Time of Use: {preferences.get('time', 'Any')}
- Season: {preferences.get('season', 'Any')}
- Occasion: {preferences.get('occasion', 'Any')}
- Preferred Scent: {preferences.get('scent', 'Any')}
- Budget: {preferences.get('budget', 'Any')}

Respond ONLY with valid JSON in this exact format:
{{
    "recommendations": [
        {{
            "name": "Perfume Name by Brand",
            "match_percentage": 95,
            "scent_notes": "Top: bergamot, pink pepper | Heart: rose, jasmine | Base: sandalwood, musk",
            "description": "A sophisticated description of the fragrance, its character, and why it perfectly matches the customer's preferences.",
            "scent_family": "floral/woody/fresh/musky/oriental"
        }},
        {{
            "name": "Second Perfume Name by Brand",
            "match_percentage": 88,
            "scent_notes": "Top: citrus, lavender | Heart: iris, violet | Base: vetiver, amber",
            "description": "A captivating description explaining the fragrance profile.",
            "scent_family": "woody"
        }}
    ]
}}"""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        # Parse JSON from response
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        
        return json.loads(json_str.strip())
    except Exception as e:
        return {"error": str(e)}

async def analyze_perfume_image(image_base64, preferences=None):
    """Analyze uploaded perfume image"""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"error": "API key not configured"}
    
    chat = LlmChat(
        api_key=api_key,
        session_id="perfume-image-analysis",
        system_message="""You are an expert perfume identifier. Analyze perfume bottle images to identify the fragrance.
Always respond in valid JSON format."""
    ).with_model("openai", "gpt-4o")
    
    pref_text = ""
    if preferences:
        pref_text = f"""
        
Also, the customer has these preferences:
- Gender: {preferences.get('gender', 'Any')}
- Time: {preferences.get('time', 'Any')}
- Season: {preferences.get('season', 'Any')}
- Occasion: {preferences.get('occasion', 'Any')}
- Preferred Scent: {preferences.get('scent', 'Any')}

Tell them if this perfume matches their preferences."""
    
    prompt = f"""Analyze this perfume bottle image. Identify:
1. The perfume name and brand
2. Its scent profile and notes
3. Typical occasions and seasons it suits{pref_text}

Respond ONLY with valid JSON:
{{
    "identified": true,
    "name": "Perfume Name by Brand",
    "scent_notes": "Top notes, heart notes, base notes",
    "description": "Description of the fragrance",
    "suitable_for": "Best suited occasions and times",
    "matches_preferences": true/false,
    "match_explanation": "Why it does/doesn't match the customer's preferences"
}}

If you cannot identify the perfume, set "identified": false and provide your best guess."""
    
    try:
        image_content = ImageContent(image_base64=image_base64)
        response = await chat.send_message(UserMessage(
            text=prompt,
            file_contents=[image_content]
        ))
        
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        
        return json.loads(json_str.strip())
    except Exception as e:
        return {"error": str(e)}

def main():
    # Initialize session state
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'image_result' not in st.session_state:
        st.session_state.image_result = None
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    # Header
    st.markdown('<h1 class="main-title">PARFUM</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Discover Your Signature Scent</p>', unsafe_allow_html=True)
    
    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<p class="section-header">Your Preferences</p>', unsafe_allow_html=True)
        
        # Preference selections
        pref_col1, pref_col2 = st.columns(2)
        
        with pref_col1:
            gender = st.selectbox(
                "GENDER",
                ["Male", "Female", "Unisex"],
                key="gender",
                help="Select your gender preference"
            )
            
            time_of_day = st.selectbox(
                "TIME OF USE",
                ["Day", "Night", "Versatile"],
                key="time",
                help="When will you wear this fragrance?"
            )
            
            season = st.selectbox(
                "SEASON",
                ["Summer", "Winter", "Spring", "Fall", "All Seasons"],
                key="season",
                help="Primary season for wearing"
            )
        
        with pref_col2:
            occasion = st.selectbox(
                "OCCASION",
                ["Casual", "Formal", "Gift", "Daily Use", "Special Event", "Date Night"],
                key="occasion",
                help="Where will you wear it?"
            )
            
            scent = st.selectbox(
                "SCENT TYPE",
                ["Woody", "Floral", "Fresh", "Musky", "Oriental", "Citrus", "Aquatic", "Spicy"],
                key="scent",
                help="Your preferred scent family"
            )
            
            budget = st.selectbox(
                "BUDGET RANGE",
                ["Any", "Under $50", "$50 - $100", "$100 - $200", "$200 - $300", "Luxury ($300+)"],
                key="budget",
                help="Optional: Your budget range"
            )
        
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        
        # Get Recommendations Button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("DISCOVER PERFUMES", key="discover-btn", use_container_width=True):
                preferences = {
                    "gender": gender,
                    "time": time_of_day,
                    "season": season,
                    "occasion": occasion,
                    "scent": scent,
                    "budget": budget
                }
                
                with st.spinner("Curating your perfect fragrances..."):
                    result = asyncio.run(get_perfume_recommendations(preferences))
                    st.session_state.recommendations = result
                    st.session_state.show_results = True
                    st.session_state.current_preferences = preferences
        
        # Display Recommendations
        if st.session_state.show_results and st.session_state.recommendations:
            result = st.session_state.recommendations
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            elif "recommendations" in result:
                st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
                st.markdown('<p class="section-header">Your Perfect Matches</p>', unsafe_allow_html=True)
                
                for rec in result["recommendations"]:
                    rec_col1, rec_col2 = st.columns([1, 2])
                    
                    with rec_col1:
                        image_url = get_perfume_image(rec.get("scent_family", ""))
                        st.markdown(f'''
                            <div class="perfume-image-container">
                                <img src="{image_url}" alt="{rec["name"]}" data-testid="perfume-image">
                            </div>
                        ''', unsafe_allow_html=True)
                    
                    with rec_col2:
                        st.markdown(f'''
                            <div class="perfume-card" data-testid="perfume-card">
                                <div class="match-badge" data-testid="match-badge">{rec["match_percentage"]}% MATCH</div>
                                <h2 class="perfume-name" data-testid="perfume-name">{rec["name"]}</h2>
                                <p class="scent-notes" data-testid="scent-notes">{rec["scent_notes"]}</p>
                                <p class="description" data-testid="perfume-description">{rec["description"]}</p>
                            </div>
                        ''', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
        
        # Divider
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        
        # Image Upload Section
        st.markdown('<p class="section-header">Identify a Perfume</p>', unsafe_allow_html=True)
        st.markdown('''
            <div style="text-align: center; margin-bottom: 1rem;">
                <p class="upload-title">Have a bottle? Let us identify it</p>
                <p class="upload-desc">Upload an image of any perfume bottle</p>
            </div>
        ''', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload perfume image",
            type=["png", "jpg", "jpeg", "webp"],
            key="perfume-upload",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            st.image(uploaded_file, caption="Uploaded Perfume", use_container_width=True)
            
            col_analyze1, col_analyze2, col_analyze3 = st.columns([1, 2, 1])
            with col_analyze2:
                if st.button("IDENTIFY THIS PERFUME", key="identify-btn", use_container_width=True):
                    # Convert to base64
                    image_bytes = uploaded_file.read()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Get current preferences if available
                    prefs = st.session_state.get('current_preferences', {
                        "gender": gender,
                        "time": time_of_day,
                        "season": season,
                        "occasion": occasion,
                        "scent": scent
                    })
                    
                    with st.spinner("Analyzing perfume bottle..."):
                        result = asyncio.run(analyze_perfume_image(image_base64, prefs))
                        st.session_state.image_result = result
        
        # Display Image Analysis Results
        if st.session_state.image_result:
            result = st.session_state.image_result
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
                
                identified_text = "✓ Identified" if result.get("identified", False) else "Best Guess"
                match_text = ""
                if "matches_preferences" in result:
                    if result["matches_preferences"]:
                        match_text = '<span style="color: #D4AF37;">✓ Matches Your Preferences</span>'
                    else:
                        match_text = '<span style="color: #A3A3A3;">May not match your preferences</span>'
                
                st.markdown(f'''
                    <div class="perfume-card" data-testid="identified-perfume-card">
                        <div class="match-badge" data-testid="identification-badge">{identified_text}</div>
                        <h2 class="perfume-name" data-testid="identified-perfume-name">{result.get("name", "Unknown Perfume")}</h2>
                        <p class="scent-notes" data-testid="identified-scent-notes">{result.get("scent_notes", "")}</p>
                        <p class="description" data-testid="identified-description">{result.get("description", "")}</p>
                        <p class="description" style="margin-top: 1rem;"><strong>Best For:</strong> {result.get("suitable_for", "Various occasions")}</p>
                        <p class="description" style="margin-top: 1rem;">{match_text}</p>
                        {f'<p class="description" style="margin-top: 0.5rem; font-style: italic;">{result.get("match_explanation", "")}</p>' if result.get("match_explanation") else ""}
                    </div>
                ''', unsafe_allow_html=True)
        
        # Reset Button
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        col_reset1, col_reset2, col_reset3 = st.columns([1, 2, 1])
        with col_reset2:
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("START NEW SEARCH", key="reset-btn", use_container_width=True):
                st.session_state.recommendations = None
                st.session_state.image_result = None
                st.session_state.show_results = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown('''
            <div style="text-align: center; margin-top: 4rem; padding: 2rem;">
                <p style="color: #525252; font-size: 0.8rem; letter-spacing: 0.2em;">
                    POWERED BY AI • FOR IN-STORE USE ONLY
                </p>
            </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
