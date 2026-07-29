import os
import re
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client

# ==========================================
# 1. PAGE CONFIG & FULL DARK THEME CSS
# ==========================================
st.set_page_config(
    page_title="Neighborhood Deals Hub",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0B132B;
        color: #F8FAFC;
    }
    
    /* Header Styling */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38BDF8;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 20px;
    }
    
    /* Stats Bar */
    .stat-pill {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 6px 16px;
        color: #E2E8F0;
        font-size: 0.88rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 10px;
        margin-bottom: 15px;
    }
    
    /* Deal Cards */
    .deal-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
    }
    .deal-card img {
        border-radius: 10px;
        object-fit: cover;
        width: 100%;
        height: 180px;
    }
    .shop-name-text {
        font-size: 0.9rem;
        font-weight: 700;
        color: #38BDF8;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    .deal-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 6px;
    }
    .deal-price {
        font-size: 1.3rem;
        font-weight: 800;
        color: #10B981;
        margin-bottom: 12px;
    }
    .merchant-badge {
        background-color: #0F172A;
        border: 1px solid #0284C7;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 20px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SUPABASE INITIALIZATION
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

try:
    if hasattr(st, "secrets"):
        if "SUPABASE_URL" in st.secrets:
            SUPABASE_URL = st.secrets["SUPABASE_URL"]
        if "SUPABASE_KEY" in st.secrets:
            SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

@st.cache_resource
def init_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# Session State
if "current_view" not in st.session_state:
    st.session_state.current_view = "customer"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def get_sample_deals():
    return [
        {
            "id": 1,
            "title": "Sony 55-Inch 4K Smart TV",
            "shop_name": "Vrc Electronics",
            "category": "Electronics",
            "deal_price": 150000,
            "image": "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=600",
            "description": "Brand new Sony TV at special offer",
            "whatsapp": "919876543210",
            "lat": 8.8080,
            "lon": 78.1550
        }
    ]

def fetch_deals():
    if supabase:
        try:
            res = supabase.table("deals").select("*").execute()
            if res.data:
                return res.data
        except Exception:
            pass
    return get_sample_deals()

# ==========================================
# 3. TOP NAVIGATION BAR
# ==========================================
col_logo, col_nav = st.columns([3, 1])

with col_logo:
    st.markdown("<div class='hero-title'>🛍️ Neighborhood Deals Hub</div>", unsafe_allow_html=True)

with col_nav:
    if st.session_state.current_view == "customer":
        if st.button("📁 Merchant Login"):
            st.session_state.current_view = "merchant"
            st.rerun()
    else:
        if st.button("🛒 Customer View"):
            st.session_state.current_view = "customer"
            st.rerun()

# ==========================================
# VIEW 1: CUSTOMER MARKETPLACE
# ==========================================
if st.session_state.current_view == "customer":
    st.markdown("<div class='hero-subtitle'>Find the best deal from a nearby local shop in under 30 seconds.</div>", unsafe_allow_html=True)
    
    # Hero Stats Bar
    st.markdown("""
        <span class='stat-pill'>🏪 <b>250+</b> Local Shops</span>
        <span class='stat-pill'>🏷️ <b>3,400+</b> Deals Posted</span>
        <span class='stat-pill'>💬 <b>8,000+</b> WhatsApp Enquiries</span>
    """, unsafe_allow_html=True)

    # Search Bar & Category Buttons
    search_q = st.text_input("", placeholder="Search products, brands, local stores...", label_visibility="collapsed")
    
    cat_cols = st.columns(5)
    categories = ["All", "Electronics", "Fashion", "Grocery", "Home"]
    
    for idx, cat in enumerate(categories):
        cat_cols[idx].button(cat, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # LIVE MAP
    deals = fetch_deals()
    user_lat, user_lon = 8.8050, 78.1519
    m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # Blue User Marker
    folium.Marker(
        location=[user_lat, user_lon],
        popup="<b>📍 You Are Here</b>",
        tooltip="Your Location",
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

    # Red Shop Markers
    for deal in deals:
        s_lat = deal.get("lat") or deal.get("latitude") or 8.8080
        s_lon = deal.get("lon") or deal.get("longitude") or 78.1550
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={s_lat},{s_lon}"
        
        popup_html = f"""
        <div style='font-family: sans-serif; width:160px; color:#1E293B;'>
            <b>{deal.get('shop_name', 'Vrc Electronics')}</b><br>
            <span>🏷️ {deal.get('title', '')}</span><br><br>
            <a href='{gmaps_link}' target='_blank' style='background:#25D366; color:white; padding:4px 8px; border-radius:4px; text-decoration:none;'>📍 Directions</a>
        </div>
        """
        folium.Marker(
            location=[s_lat, s_lon],
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=deal.get('shop_name', 'Vrc Electronics'),
            icon=folium.Icon(color="red", icon="shopping-bag", prefix="fa")
        ).add_to(m)

    st_folium(m, use_container_width=True, height=350)

    # TODAY'S BEST DEALS GRID (WITH SHOP NAME)
    st.markdown("### 🔥 Today's Best Deals")
    
    deal_cols = st.columns(3)
    for idx, deal in enumerate(deals):
        with deal_cols[idx % 3]:
            st.markdown("<div class='deal-card'>", unsafe_allow_html=True)
            st.image(deal.get("image", "https://via.placeholder.com/400x250"), use_container_width=True)
            
            # SHOP NAME DISPLAYED HERE
            shop_name_display = deal.get('shop_name') or "Vrc Electronics"
            st.markdown(f"<div class='shop-name-text'>🏪 {shop_name_display}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='deal-title'>{deal.get('title')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='deal-price'>₹{deal.get('deal_price', 0):,}</div>", unsafe_allow_html=True)
            
            wa_num = deal.get("whatsapp", "919876543210")
            msg = f"Hi {shop_name_display}, I saw your deal '{deal.get('title')}' on Neighborhood Deals Hub!"
            wa_url = f"https://wa.me/{wa_num}?text={msg.replace(' ', '%20')}"
            
            st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#25D366; color:white; text-align:center; padding:10px; border-radius:8px; font-weight:bold;">
                        💬 Chat on WhatsApp
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# VIEW 2: MERCHANT LOGIN & DASHBOARD
# ==========================================
else:
    # IF NOT LOGGED IN -> SHOW ID & PASS LOGIN FORM
    if not st.session_state.logged_in:
        st.markdown("## 🔐 Shopkeeper Portal Login")
        st.markdown("<p style='color:#94A3B8;'>Sign in to manage your store deals, inventory, and analytics.</p>", unsafe_allow_html=True)
        
        login_col, _ = st.columns([1, 1])
        with login_col:
            with st.form("merchant_login_form"):
                merchant_id = st.text_input("Merchant ID / Username", placeholder="e.g. admin or vrc_electronics")
                merchant_pass = st.text_input("Password", type="password", placeholder="••••••••")
                login_btn = st.form_submit_button("🚀 Login to Portal", use_container_width=True)
                
                if login_btn:
                    if (merchant_id in ["admin", "vrc_electronics"]) and (merchant_pass == "1234"):
                        st.session_state.logged_in = True
                        st.success("Login Successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid Merchant ID or Password! (Default: ID=admin, Pass=1234)")
    
    # IF LOGGED IN -> SHOW DASHBOARD
    else:
        d_head, d_out = st.columns([3, 1])
        with d_head:
            st.markdown("## Welcome back, Vrc Electronics 👋")
            st.markdown("<p style='color:#94A3B8;'>Manage today's deals and customer enquiries.</p>", unsafe_allow_html=True)
        with d_out:
            if st.button("🔒 Logout"):
                st.session_state.logged_in = False
                st.rerun()

        st.markdown("""
            <div class='merchant-badge'>
                <b>🏪 Vrc Electronics</b> <span style='background:#10B981; color:white; padding:2px 6px; border-radius:4px; font-size:12px;'>Verified Merchant</span><br>
                <span style='color:#94A3B8; font-size:13px;'>📍 North Authoor • 🟢 Session Active</span>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📊 Analytics", "➕ Add Deal", "✏️ Edit Deals"])

        # TAB 1: ANALYTICS
        with tab1:
            m1, m2, m3 = st.columns(3)
            m1.metric("👁️ Views Today", "0", "No visits today")
            m2.metric("📦 Active Deals", "1", "🟢 All Listings Live")
            m3.metric("💬 WhatsApp Clicks", "0", "Updated 5 mins ago")

            st.markdown("#### 📈 Weekly Customer Interest")
            chart_data = pd.DataFrame({
                'Days': ['Fri', 'Mon', 'Sat', 'Sun', 'Thu', 'Tue', 'Wed'],
                'Interests': [8, 2, 4, 0, 7, 5, 4]
            })
            st.bar_chart(chart_data.set_index('Days'))

        # TAB 2: ADD DEAL
        with tab2:
            with st.form("add_deal_merchant"):
                c1, c2 = st.columns(2)
                with c1:
                    p_title = st.text_input("Product Title*")
                    p_price = st.number_input("Deal Value (₹)*", min_value=0)
                    p_desc = st.text_area("Product Specifications / Deal Details*")
                with c2:
                    p_cat = st.selectbox("Category Field*", ["Electronics", "Fashion", "Grocery", "Home"])
                    p_img = st.text_input("Upload Photo (Paste Link)", placeholder="https://images.unsplash.com/...")
                    p_hub = st.selectbox("Assign Distribution Hub Area Node*", ["North Authoor", "Tuticorin Main", "Millerpuram"])

                if st.form_submit_button("🚀 Publish Deal"):
                    st.success("🎉 Deal published live!")

        # TAB 3: EDIT DEALS
        with tab3:
            st.selectbox("Select deal record card to modify:", ["sony tv (₹1,50,000)"])
            st.text_input("Product Title", value="sony tv")
            st.number_input("Price Value (₹)", value=150000)
            st.text_input("Photo Link")
            st.text_area("Description Text", value="brand new sony tv at offer")
            
            col_s, col_d = st.columns(2)
            col_s.button("💾 Save Changes", use_container_width=True)
            col_d.button("🗑️ Remove Deal", use_container_width=True)
