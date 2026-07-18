import os
import math
import re
from datetime import datetime
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Page Configuration & Premium Minimalist Dark UI Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Global Background and Canvas Setup */
    .stApp {
        background-color: #0f172a !important;
    }
    
    /* Top Navigation bar styling */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid #1e293b;
    }
    
    /* Category Navigation Bar Chips */
    .category-container {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding: 10px 0;
        margin-bottom: 25px;
    }
    
    /* Sleek Marketplace Product Card Layout */
    .product-card-frame {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        height: 100%;
        border: 1px solid #334155;
        position: relative;
    }
    .product-card-frame:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0,0,0,0.4);
        border-color: #475569;
    }
    
    /* Flipkart-Inspired Hero Image Canvas */
    .img-container {
        width: 100%;
        height: 200px;
        overflow: hidden;
        background-color: #0f172a;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        margin-bottom: 14px;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .placeholder-icon { 
        font-size: 4.5rem; 
        color: #475569;
    }
    
    /* Typography Component Rules */
    .product-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 4px;
        line-height: 1.3;
    }
    
    .merchant-name-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .product-price {
        font-size: 1.4rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 8px;
    }
    
    /* UX Metadata Row (Distance, Rating, Time) */
    .ux-metadata-row {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.8rem;
        color: #cbd5e1;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }
    .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        background-color: #0f172a;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .rating-badge {
        background-color: #15803d !important;
        color: #bfdbfe;
        font-weight: 600;
    }
    
    .product-desc {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 16px;
        line-height: 1.4;
    }

    /* Form input adjustments */
    div[data-testid="stWidgetLabel"] p {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }
    
    /* Merchant Dashboard Component Styles */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    .metric-val { font-size: 2rem; font-weight: 700; color: #38bdf8; }
    .metric-lbl { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; margin-top: 4px; }
    </style>
""", unsafe_allow_html=True)

# Session States Configuration
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None
if "current_category" not in st.session_state:
    st.session_state.current_category = "All"

# 2. Supabase Connection Setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase configuration keys.")
    st.stop()

# Indian Currency Formatter Helper (₹1,49,999)
def format_indian_currency(amount):
    try:
        val = int(float(amount))
        s = str(val)
        if len(s) <= 3:
            return f"₹{s}"
        else:
            last_three = s[-3:]
            remaining = s[:-3]
            remaining_fmt = re.sub(r'(..)(?=.)', r'\1,', remaining[::-1])[::-1]
            return f"₹{remaining_fmt},{last_three}"
    except:
        return f"₹{amount}"

# Human-Readable Relative Time Helper ("Posted 2 hours ago")
def get_relative_time(timestr):
    try:
        dt = datetime.fromisoformat(timestr.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except:
        return "Recently"

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    R = 6371.0 # Earth's radius in km
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 1)

# Fetch DB Records safely
try:
    items_response = supabase.table("items").select("*").order("created_at", desc=True).execute()
    items = items_response.data if items_response.data else []
    
    merchants_response = supabase.table("merchants").select("*").execute()
    merchants_dict = {m['shop_id']: m for m in merchants_response.data} if merchants_response.data else {}
    
    analytics_response = supabase.table("analytics").select("*").execute()
    analytics_data = analytics_response.data if analytics_response.data else []
except Exception:
    items, merchants_dict, analytics_data = [], {}, []

# Default location coordinates (Thoothukudi Base Center)
user_lat, user_lon = 8.8050, 78.1519

# 3. TOP NAVIGATION TIER (Customer-First Alignment)
st.markdown(f"""
    <div class="top-nav">
        <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff; display: flex; align-items: center; gap: 8px;">
            📍 <span style="background: linear-gradient(90deg, #38bdf8, #2874f0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Deals Near You</span>
        </div>
        <div style="color: #94a3b8; font-size: 0.9rem;">📍 Thoothukudi Center</div>
    </div>
""", unsafe_allow_html=True)

# 4. SIDEBAR PORTAL (Cleanly tucked away for Merchant Use)
with st.sidebar:
    st.markdown("### 🏢 Merchant Control Panel")
    if not st.session_state.logged_in:
        input_shop_id = st.text_input("Merchant Username", placeholder="e.g., shop_01")
        input_password = st.text_input("Password", type="password")
        if st.button("Secure Portal Login", use_container_width=True, type="primary"):
            if input_shop_id.strip() in merchants_dict and merchants_dict[input_shop_id.strip()].get("password") == input_password.strip():
                st.session_state.logged_in = True
                st.session_state.merchant_id = input_shop_id.strip()
                st.session_state.merchant_name = merchants_dict[input_shop_id.strip()].get("shop_name")
                st.rerun()
            else:
                st.error("Invalid merchant access keys.")
    else:
        m_info = merchants_dict.get(st.session_state.merchant_id, {})
        logo_url = m_info.get("logo_url") if m_info.get("logo_url") else "https://cdn-icons-png.flaticon.com/512/606/606547.png"
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px;">
                <img src="{logo_url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">
                <div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">{st.session_state.merchant_name}</div>
                    <div style="color: #4ade80; font-size: 0.75rem;">⚡ Manager Status</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        merchant_menu = st.radio("Dashboard Operations", ["📊 Analytics Metrics", "📥 Post New Product", "✏️ Update Catalog"])
        if st.button("Exit Portal Session", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.rerun()

is_merchant = st.session_state.logged_in

# 5. MERCHANT MANAGEMENT VIEW TIERS
if is_merchant:
    if merchant_menu == "📊 Analytics Metrics":
        st.markdown(f"### 📊 Shop Performance Console")
        my_items_count = len([x for x in items if x.get('merchant_id') == st.session_state.merchant_id])
        my_clicks = len([a for a in analytics_data if a.get('merchant_id') == st.session_state.merchant_id])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.markdown(f"<div class='metric-card'><div class='metric-val'>{my_clicks * 4}</div><div class='metric-lbl'>Total Impressions</div></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='metric-card'><div class='metric-val'>{my_items_count}</div><div class='metric-lbl'>Active Listings</div></div>", unsafe_allow_html=True)
        col_m3.markdown(f"<div class='metric-card'><div class='metric-val'>{my_clicks}</div><div class='metric-lbl'>WhatsApp Leads Generated</div></div>", unsafe_allow_html=True)
        st.markdown("<br><hr style='border-color:#334155;'><br>", unsafe_allow_html=True)

    elif merchant_menu == "📥 Post New Product":
        st.markdown(f"### 📥 Broadcast New Promotion")
        with st.form(key="add_item_form", clear_on_submit=True):
            col_i1, col_i2 = st.columns(2)
            new_title = col_i1.text_input("Product Title*")
            new_cat = col_i2.selectbox("Category*", ["Electronics", "Fashion", "Grocery", "Home", "General"])
            new_price = col_i1.number_input("Deal Price (₹)*", min_value=0, step=50)
            new_img = col_i2.text_input("Product Photo URL", placeholder="https://images.unsplash.com/...")
            new_desc = st.text_area("Product Specifications / Short Description*")
            
            # Simplified Location Selection to drop user friction points
            new_loc = st.selectbox("Select Drop Location Area*", ["North Authoor", "Central Bazar", "Tiruchendur Road", "Millerpuram"])
            loc_coords = {"North Authoor": (8.8050, 78.1519), "Central Bazar": (8.8100, 78.1450), "Tiruchendur Road": (8.7950, 78.1600), "Millerpuram": (8.8020, 78.1320)}
            
            if st.form_submit_button("🚀 Deploy Deal Card Live", use_container_width=True):
                if new_title.strip() and new_desc.strip() and new_price > 0:
                    try:
                        coords = loc_coords.get(new_loc, (8.8050, 78.1519))
                        payload = {"title": new_title.strip(), "description": new_desc.strip(), "category": new_cat, "price": new_price, "location": new_loc, "image_url": new_img.strip(), "latitude": coords[0], "longitude": coords[1], "merchant_id": st.session_state.merchant_id}
                        supabase.table("items").insert(payload).execute()
                        st.success("Deal updated inside standard local feeds!")
                        st.rerun()
                    except Exception as err: st.error(f"Error: {err}")

    elif merchant_menu == "✏️ Update Catalog":
        st.markdown(f"### ✏️ Manage Existing Listings")
        my_items = [i for i in items if i.get('merchant_id') == st.session_state.merchant_id]
        if my_items:
            item_to_edit = st.selectbox("Select deal record to edit:", my_items, format_func=lambda x: f"{x.get('title')} ({format_indian_currency(x.get('price'))})")
            if item_to_edit:
                with st.form(key="edit_item_form"):
                    e_title = st.text_input("Product Title", value=item_to_edit.get('title'))
                    e_price = st.number_input("Price (₹)", value=int(item_to_edit.get('price', 0)))
                    e_img = st.text_input("Image URL", value=item_to_edit.get('image_url', ''))
                    e_desc = st.text_area("Description", value=item_to_edit.get('description'))
                    if st.form_submit_button("💾 Apply Database Modifications", use_container_width=True):
                        try:
                            supabase.table("items").update({"title": e_title.strip(), "price": e_price, "image_url": e_img.strip(), "description": e_desc.strip()}).eq("id", item_to_edit.get('id')).execute()
                            st.success("Changes saved successfully!")
                            st.rerun()
                        except Exception as edit_err: st.error(f"Failed: {edit_err}")

# 6. FILTER STACK & CATEGORY ROW WIDGETS
col_s1, col_s2 = st.columns([4, 1])
search_query = col_s1.text_input("Search Engine Bar", placeholder="🔍 Search products, brands, local stores...", label_visibility="collapsed")

# Minimal Category Navigation Layout Chips Array
categories = ["All", "Electronics", "Fashion", "Grocery", "Home"]
cat_cols = st.columns(len(categories))
for idx, cat_name in enumerate(categories):
    if cat_cols[idx].button(cat_name, use_container_width=True, type="secondary" if st.session_state.current_category != cat_name else "primary"):
        st.session_state.current_category = cat_name
        st.rerun()

# 7. FILTER PROCESSING LOOP ENGINE
filtered_items = []
map_data_list = []

for i in items:
    m_info = merchants_dict.get(i.get('merchant_id'), {})
    i['shop_name'] = m_info.get('shop_name', 'Local Shop')
    i['shop_rating'] = m_info.get('rating', 4.5)
    i['is_verified'] = m_info.get('is_verified', False)
    
    # Process distance tracking pipeline
    i_lat, i_lon = i.get('latitude'), i.get('longitude')
    dist = calculate_distance(user_lat, user_lon, i_lat, i_lon)
    i['distance_km'] = dist if dist is not None else 1.2

    # Categorization match calculations
    cat_match = (st.session_state.current_category == "All" or i.get('category') == st.session_state.current_category)
    search_match = (search_query.lower() in i.get('title', '').lower() or search_query.lower() in i.get('description', '').lower())
    
    if cat_match and search_match:
        filtered_items.append(i)
        if i_lat and i_lon:
            map_data_list.append({"latitude": float(i_lat), "longitude": float(i_lon), "title": i.get('title')})

# 8. EXPOSED LIVE MAP CANVAS ELEMENT TIER
if map_data_list:
    st.map(pd.DataFrame(map_data_list), use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# 9. FLIPKART-INSPIRED CLEAN DEALS CONTAINER GRID
if filtered_items:
    cols = st.columns(4)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 4]:
            
            # Product Photo Hero Presentation Logic
            img_src = item.get('image_url')
            if img_src and str(img_src).strip().startswith("http"):
                img_html = f'<img src="{img_src.strip()}">'
            else:
                img_html = '<div class="placeholder-icon">📺</div>'
                
            # Render Verified badge element hook
            verified_badge = ' <span style="color:#2874f0; font-size:0.9rem;">💎</span>' if item.get('is_verified') else ''
            
            # UI Frame Injection Block
            st.markdown(f"""
                <div class="product-card-frame">
                    <div class="img-container">
                        {img_html}
                    </div>
                    <div class="merchant-name-label">
                        🏢 <span>{item.get('shop_name')}{verified_badge}</span>
                    </div>
                    <div class="product-title">{item.get('title')}</div>
                    <div class="product-price">{format_indian_currency(item.get('price', 0))}</div>
                    <div class="ux-metadata-row">
                        <span class="meta-item rating-badge">⭐ {item.get('shop_rating')}</span>
                        <span class="meta-item">📍 {item.get('distance_km')} km near me</span>
                        <span class="meta-item">⏱️ {get_relative_time(item.get('created_at', ''))}</span>
                    </div>
                    <div class="product-desc">{item.get('description')}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Interactive Action Triggers
            if is_merchant and item.get('merchant_id') == st.session_state.merchant_id:
                if st.button(f"🗑️ Remove Deal", key=f"del_{item['id']}", type="primary", use_container_width=True):
                    supabase.table("items").delete().eq("id", item['id']).execute()
                    st.rerun()
            else:
                phone = merchant_directory.get(item.get('merchant_id'), "918072130833")
                
                # Analytics Tracker Trigger Logic Callback
                def track_lead(m_id, item_id):
                    try: supabase.table("analytics").insert({"merchant_id": m_id, "item_id": item_id}).execute()
                    except: pass
                    
                wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20I%20am%20interested%20in%20your%20deal%20for%20{item.get('title')}"
                st.link_button("💬 Chat on WhatsApp", wa_url, use_container_width=True, on_click=track_lead, args=(item.get('merchant_id'), item.get('id')))
            
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("No active local deals match your search parameters.")
