import os
import math
import re
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Page Configuration & UI Layout Config
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    
    label[data-testid="stWidgetLabel"] p {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }
    ::placeholder {
        color: #64748b !important;
        opacity: 0.85;
    }
    
    .product-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 5px;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    .product-price {
        font-size: 1.15rem;
        font-weight: 600;
        color: #00ffcc;
        margin-bottom: 8px;
    }
    
    div[data-child-config="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    div[data-child-config="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.5);
    }
    
    .img-container {
        width: 100%;
        height: 200px;
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 12px;
        background-color: #1a1c23;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #2d313f;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .placeholder-icon { font-size: 4rem; }
    
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select {
        border: 1px solid #2d313f !important;
        background-color: #14161d !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    .hero-scanner-box {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 2px solid #6366f1;
        padding: 26px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# 2. Supabase Connection Setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase keys.")
    st.stop()

def clean_listing_text(text):
    if not text: return ""
    cleaned = re.sub(r'<[^>]*>', '', str(text))
    cleaned = re.sub(r'\[\s*URGENT\s*DEAL\s*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'URGENT', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\|VERIFIED\|', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def calculate_distance(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return None
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = rad_lat2 - rad_lat1, rad_lon2 - rad_lon1
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data
    merchants_response = supabase.table("merchants").select("shop_id, phone_number, is_verified").execute()
    merchant_directory = {}
    verified_merchants = set()
    if merchants_response.data:
        for m in merchants_response.data:
            merchant_directory[m['shop_id']] = m.get('phone_number')
            if m.get('is_verified') is True:
                verified_merchants.add(m['shop_id'])
    analytics_response = supabase.table("analytics").select("*").execute()
    analytics_data = analytics_response.data if analytics_response.data else []
except Exception as e:
    items, merchant_directory, verified_merchants, analytics_data = [], {}, set(), []

# 3. Sidebar Panel
with st.sidebar:
    st.markdown("## 🛍️ Shopkeeper Portal")
    if not st.session_state.logged_in:
        st.write("Sign in with your Shop Credentials")
        input_shop_id = st.text_input("Shopkeeper ID / Username", placeholder="e.g., shop_01")
        input_password = st.text_input("Merchant Password", type="password")
        if st.button("Secure Login", use_container_width=True, type="primary"):
            if input_shop_id.strip() and input_password.strip():
                try:
                    response = supabase.table("merchants").select("*").eq("shop_id", input_shop_id.strip()).execute()
                    m_data = response.data
                    if m_data and m_data[0].get("password") == input_password.strip():
                        st.session_state.logged_in = True
                        st.session_state.merchant_id = m_data[0].get("shop_id")
                        st.session_state.merchant_name = m_data[0].get("shop_name")
                        st.rerun()
                    else: st.error("Invalid credentials.")
                except Exception as err: st.error(f"Auth Error: {err}")
    else:
        st.success(f"🔒 Active: {st.session_state.merchant_name}")
        merchant_menu = st.radio("Navigation Menu", ["📊 Dashboard Analytics", "📥 Deploy New Listing", "✏️ Edit/Manage Listings"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out of Portal", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.rerun()

is_merchant = st.session_state.logged_in

# 4. App Headers
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Auto-Detecting Nearby Deals Safely and Privately")
st.markdown("<br>", unsafe_allow_html=True)

# DEFAULT BASE STABILIZATION: Thoothukudi fallback parameters
user_lat, user_lon = 8.8050, 78.1519

try:
    from streamlit_geolocation import streamlit_geolocation
    location_data = streamlit_geolocation()
    if location_data and location_data.get("latitude"):
        user_lat, user_lon = location_data.get("latitude"), location_data.get("longitude")
except Exception:
    pass

# 5. Form Deployment Console Tier
if is_merchant and merchant_menu == "📥 Deploy New Listing":
    st.markdown(f"### 📥 Deploy New Item")
    with st.form(key="add_item_form", clear_on_submit=True):
        new_title = st.text_input("Product Title*")
        new_cat = st.selectbox("Product Category*", ["General", "Electronics", "Vehicles", "Housing"])
        new_price = st.number_input("Price (₹)*", min_value=0, step=10)
        new_desc = st.text_input("Description Content*")
        new_loc = st.text_input("City/Area Label*", value="Thoothukudi")
        item_lat_input = st.number_input("Item Latitude*", format="%.6f", value=8.8050)
        item_lon_input = st.number_input("Item Longitude*", format="%.6f", value=78.1519)
        if st.form_submit_button("🚀 Deploy Listing Live", use_container_width=True, type="primary"):
            if new_title.strip() and new_desc.strip() and new_price > 0:
                try:
                    payload = {"title": clean_listing_text(new_title), "description": clean_listing_text(new_desc), "category": new_cat, "price": new_price, "location": clean_listing_text(new_loc), "latitude": item_lat_input, "longitude": item_lon_input, "merchant_id": st.session_state.merchant_id}
                    supabase.table("items").insert(payload).execute()
                    st.success("Listing deployed!")
                    st.rerun()
                except Exception as err: st.error(f"Error: {err}")

# 6. Web Editor Manager Interface Tier
if is_merchant and merchant_menu == "✏️ Edit/Manage Listings":
    st.markdown(f"### ✏️ Edit Live Web Listings")
    my_items = [i for i in items if i.get('merchant_id') == st.session_state.merchant_id]
    if my_items:
        item_to_edit = st.selectbox("Select a listing to edit:", my_items, format_func=lambda x: f"{clean_listing_text(x.get('title'))} (₹{x.get('price')})")
        if item_to_edit:
            with st.form(key="edit_item_form"):
                e_title = st.text_input("Product Title", value=clean_listing_text(item_to_edit.get('title')))
                e_cat = st.selectbox("Category", ["General", "Electronics", "Vehicles", "Housing"], index=["General", "Electronics", "Vehicles", "Housing"].index(item_to_edit.get('category', 'General')))
                e_price = st.number_input("Price (₹)", value=int(item_to_edit.get('price', 0)))
                e_desc = st.text_input("Description", value=clean_listing_text(item_to_edit.get('description')))
                e_loc = st.text_input("City/Area Label", value=clean_listing_text(item_to_edit.get('location')))
                e_lat = st.number_input("Latitude", format="%.6f", value=float(item_to_edit.get('latitude', 8.8050)))
                e_lon = st.number_input("Longitude", format="%.6f", value=float(item_to_edit.get('longitude', 78.1519)))
                if st.form_submit_button("💾 Save Changes to Web Database", use_container_width=True, type="primary"):
                    try:
                        update_payload = {"title": clean_listing_text(e_title), "category": e_cat, "price": e_price, "description": clean_listing_text(e_desc), "location": clean_listing_text(e_loc), "latitude": e_lat, "longitude": e_lon}
                        supabase.table("items").update(update_payload).eq("id", item_to_edit.get('id')).execute()
                        st.success("Database update saved successfully live!")
                        st.rerun()
                    except Exception as edit_err: st.error(f"Failed: {edit_err}")

# 7. Core Consumer Filter Section
st.markdown("<div class='section-header'>🔍 Filter Controls</div>", unsafe_allow_html=True)
with st.container(border=True):
    col_f1, col_f2 = st.columns(2)
    search_query = col_f1.text_input("Search...", placeholder="Type keywords...", label_visibility="collapsed")
    category = col_f2.selectbox("Category Selector", ["All Categories", "General", "Electronics", "Vehicles", "Housing"], label_visibility="collapsed")

# 8. Clean Filter Processing Logic Loop
filtered_items = []
map_data_list = []
for i in items:
    t_clean = clean_listing_text(i.get('title', ''))
    d_clean = clean_listing_text(i.get('description', ''))
    c_clean = clean_listing_text(i.get('category', 'General'))
    l_clean = clean_listing_text(i.get('location', 'Thoothukudi'))
    
    s_match = (search_query.lower() in t_clean.lower() or search_query.lower() in d_clean.lower())
    c_match = (category == "All Categories" or (category.lower() in c_clean.lower()))
    
    i_lat, i_lon = i.get('latitude'), i.get('longitude')
    i['calculated_distance'] = calculate_distance(user_lat, user_lon, i_lat, i_lon)
    i['title'], i['description'], i['category'], i['location'] = t_clean, d_clean, c_clean, l_clean
    
    if s_match and c_match:
        filtered_items.append(i)
        if i_lat is not None and i_lon is not None:
            map_data_list.append({"latitude": float(i_lat), "longitude": float(i_lon)})

# 9. MAP RESTORE: Render interactive geographical placement widget immediately
if map_data_list:
    st.markdown("### 🗺️ Neighborhood Deal Map")
    st.map(pd.DataFrame(map_data_list), use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# 10. Native Streamlit Grid Card presentation
if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown("<div class='img-container'><div class='placeholder-icon'>📺</div></div>", unsafe_allow_html=True)
                
                b_col1, b_col2 = st.columns(2)
                b_col1.markdown(f"🏷️ `{item.get('category')}`")
                b_col2.markdown(f"📍 `{item.get('location')}`")
                
                is_verified = item.get('merchant_id') in verified_merchants and item.get('merchant_id') is not None
                if is_verified:
                    st.success("✨ Verified Shop Partner")
                
                st.markdown(f"<div class='product-title'>{item.get('title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='product-price'>₹{float(item.get('price')):,.2f}</div>", unsafe_allow_html=True)
                st.write(item.get('description'))
                st.markdown("---")
                
                if is_merchant and item.get('merchant_id') == st.session_state.merchant_id:
                    if st.button(f"🗑️ Remove Deal Item", key=f"del_{item['id']}", type="primary", use_container_width=True):
                        supabase.table("items").delete().eq("id", item['id']).execute()
                        st.rerun()
                else:
                    phone = merchant_directory.get(item.get('merchant_id'), "918072130833")
                    wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20interested%20in%20{item.get('title')}"
                    st.link_button("💬 Chat on WhatsApp", wa_url, use_container_width=True)
else:
    st.info("No active promotions match your query.")
