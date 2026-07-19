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
    /* Premium Dark Mode Global Setup */
    .stApp {
        background-color: #0f172a !important;
    }
    
    /* Hide the default Streamlit sidebar toggle entirely for a pure clean homepage layout */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Sleek Top Navigation Header Bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-bottom: 25px;
        border-bottom: 1px solid #1e293b;
    }
    
    /* Clean Subtitle Tagline */
    .hero-tagline {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: -15px;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    /* 65-35 Premium Card Architecture Framework */
    .product-card-frame {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        height: 440px; 
        border: 1px solid #334155;
    }
    .product-card-frame:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -6px rgba(0,0,0,0.4);
        border-color: #475569;
    }
    
    /* Image Section: Fills exactly ~60-65% profile space */
    .img-container {
        width: 100%;
        height: 240px; 
        overflow: hidden;
        background-color: #0f172a;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .placeholder-icon { 
        font-size: 5rem; 
        color: #475569;
    }
    
    /* Text Details Section */
    .card-details-box {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex-grow: 1;
    }
    
    .product-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .merchant-name-label {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .product-price {
        font-size: 1.35rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 6px;
    }
    
    /* UX Micro-Metadata Rows */
    .ux-metadata-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.75rem;
        color: #cbd5e1;
        margin-bottom: 8px;
    }
    .meta-item {
        background-color: #0f172a;
        padding: 3px 6px;
        border-radius: 4px;
    }
    .rating-badge {
        background-color: #15803d !important;
        color: #ffffff;
        font-weight: 600;
    }
    
    .product-desc {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.3;
        height: 36px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 5px;
    }

    /* Core Input Layout Polish overrides */
    div[data-testid="stWidgetLabel"] p {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stForm"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 20px !important;
    }
    
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-val { font-size: 1.8rem; font-weight: 700; color: #38bdf8; }
    .metric-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

# Instantiating persistent layout toggles
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None
if "current_category" not in st.session_state:
    st.session_state.current_category = "All"
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Customer"

# 2. Supabase Connection Setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase cloud service credentials.")
    st.stop()

# Formatting Utilities
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

def get_relative_time(timestr):
    try:
        dt = datetime.fromisoformat(timestr.replace("Z", "+00:00"))
        diff = datetime.now(dt.tzinfo) - dt
        if diff.days > 0: return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0: return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        return f"{minutes}m ago" if minutes > 0 else "Just now"
    except:
        return "Recently"

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 1)

# Pull database records
try:
    items_response = supabase.table("items").select("*").order("created_at", desc=True).execute()
    items = items_response.data if items_response.data else []
    
    merchants_response = supabase.table("merchants").select("*").execute()
    merchants_dict = {m['shop_id']: m for m in merchants_response.data} if merchants_response.data else {}
    
    analytics_response = supabase.table("analytics").select("*").execute()
    analytics_data = analytics_response.data if analytics_response.data else []
except Exception:
    items, merchants_dict, analytics_data = [], {}, []

user_lat, user_lon = 8.8050, 78.1519

# 3. CUSTOMER-FIRST NAVIGATION BAR TIER
with st.container():
    col_nav1, col_nav2 = st.columns([4, 1])
    with col_nav1:
        st.markdown("""
            <div style="font-size: 1.65rem; font-weight: 700; color: #ffffff; padding-top: 5px;">
                📍 <span style="background: linear-gradient(90deg, #38bdf8, #2874f0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Neighborhood Deals Hub</span>
            </div>
        """, unsafe_allow_html=True)
    with col_nav2:
        if st.session_state.view_mode == "Customer":
            if st.button("🏢 Merchant Portal", use_container_width=True, type="secondary"):
                st.session_state.view_mode = "Merchant"
                st.rerun()
        else:
            # FIXED: Shifted to a consistent blue accent type configuration to protect structural visual hierarchy
            if st.button("🛒 Customer View", use_container_width=True, type="primary"):
                st.session_state.view_mode = "Customer"
                st.rerun()

# 4. CUSTOMER-FIRST HOME VIEW ENTRY
if st.session_state.view_mode == "Customer":
    st.markdown("<div class='hero-tagline'>Discover today's best offers from verified local shops near you.</div>", unsafe_allow_html=True)
    
    # Unified Search Input Block
    search_query = st.text_input("Search Engine Console Field", placeholder="🔍 Search products, brands, local shops...", label_visibility="collapsed")
    
    # Category Filter Chips Bar
    categories = ["All", "Electronics", "Fashion", "Grocery", "Home"]
    cat_cols = st.columns(len(categories))
    for idx, cat_name in enumerate(categories):
        if cat_cols[idx].button(cat_name, use_container_width=True, type="secondary" if st.session_state.current_category != cat_name else "primary"):
            st.session_state.current_category = cat_name
            st.rerun()
            
    # Process Catalog Data Pipeline Filters
    filtered_items = []
    map_data_list = []
    for i in items:
        m_info = merchants_dict.get(i.get('merchant_id'), {})
        i['shop_name'] = m_info.get('shop_name', 'Local Shop')
        i['shop_rating'] = m_info.get('rating', 4.5)
        i['is_verified'] = m_info.get('is_verified', False)
        
        dist = calculate_distance(user_lat, user_lon, i.get('latitude'), i.get('longitude'))
        i['distance_km'] = dist if dist is not None else 1.2
        
        cat_match = (st.session_state.current_category == "All" or i.get('category') == st.session_state.current_category)
        search_match = (search_query.lower() in i.get('title', '').lower() or search_query.lower() in i.get('description', '').lower())
        
        if cat_match and search_match:
            filtered_items.append(i)
            if i.get('latitude') and i.get('longitude'):
                map_data_list.append({"latitude": float(i.get('latitude')), "longitude": float(i.get('longitude')), "title": i.get('title')})

    # Integrated Geographic Map View Header Canvas
    if map_data_list:
        st.map(pd.DataFrame(map_data_list), use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
    # The Core 65-35 Dynamic Image Card Catalog Grid
    if filtered_items:
        st.markdown("<h3 style='color:#ffffff; font-size:1.3rem; font-weight:600; margin-bottom:15px;'>🔥 Hot Promotions Near You</h3>", unsafe_allow_html=True)
        cols = st.columns(4)
        for idx, item in enumerate(filtered_items):
            with cols[idx % 4]:
                img_src = item.get('image_url')
                img_html = f'<img src="{img_src.strip()}">' if (img_src and str(img_src).strip().startswith("http")) else '<div class="placeholder-icon">📺</div>'
                verified_badge = ' <span style="color:#2874f0; font-size:0.85rem;">💎</span>' if item.get('is_verified') else ''
                
                # HTML Architecture Layer
                st.markdown(f"""
                    <div class="product-card-frame">
                        <div class="img-container">
                            {img_html}
                        </div>
                        <div class="card-details-box">
                            <div>
                                <div class="merchant-name-label">🏢 {item.get('shop_name')}{verified_badge}</div>
                                <div class="product-title">{item.get('title')}</div>
                            </div>
                            <div>
                                <div class="product-price">{format_indian_currency(item.get('price', 0))}</div>
                                <div class="ux-metadata-row">
                                    <span class="meta-item rating-badge">⭐ {item.get('shop_rating')}</span>
                                    <span class="meta-item">📍 {item.get('distance_km')} km</span>
                                    <span class="meta-item">⏱️ {get_relative_time(item.get('created_at', ''))}</span>
                                </div>
                                <div class="product-desc">{item.get('description')}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Dynamic Trigger Actions
                phone = merchants_dict.get(item.get('merchant_id'), {}).get('phone_number', '918072130833')
                def track_lead(m_id, item_id):
                    try: supabase.table("analytics").insert({"merchant_id": m_id, "item_id": item_id}).execute()
                    except: pass
                    
                wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20I'm%20interested%20in%20{item.get('title')}"
                st.link_button("💬 Chat on WhatsApp", wa_url, use_container_width=True, on_click=track_lead, args=(item.get('merchant_id'), item.get('id')))
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No active local deals match your current query parameter sets.")

# 5. ISOLATED MERCHANT CONSOLE PORTAL VIEW TIER
else:
    st.markdown("<h2 style='color:#ffffff; font-weight:600;'>🏢 Merchant Portal Console</h2>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        col_l1, col_l2 = st.columns([1, 2])
        with col_l1:
            st.markdown("<p style='color:#94a3b8;'>Access your manager catalog credentials to host local advertising pipelines.</p>", unsafe_allow_html=True)
            input_shop_id = st.text_input("Merchant Username", placeholder="e.g., shop_01")
            input_password = st.text_input("Portal Password", type="password")
            if st.button("Secure Authentication Access", use_container_width=True, type="primary"):
                if input_shop_id.strip() in merchants_dict and merchants_dict[input_shop_id.strip()].get("password") == input_password.strip():
                    st.session_state.logged_in = True
                    st.session_state.merchant_id = input_shop_id.strip()
                    st.session_state.merchant_name = merchants_dict[input_shop_id.strip()].get("shop_name")
                    st.rerun()
                else: st.error("Access rejected. Please check variables.")
    else:
        m_info = merchants_dict.get(st.session_state.merchant_id, {})
        m_logo = m_info.get("logo_url") if m_info.get("logo_url") else "https://cdn-icons-png.flaticon.com/512/606/606547.png"
        
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; background-color: #1e293b; padding: 15px; border-radius: 8px; border:1px solid #334155; margin-bottom: 25px; width: fit-content;">
                <img src="{m_logo}" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;">
                <div>
                    <div style="color:#ffffff; font-weight:600; font-size:1.05rem;">{st.session_state.merchant_name}</div>
                    <div style="color:#4ade80; font-size:0.8rem; font-weight:500;">🔒 Active Session Established</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        op_menu = st.tabs(["📊 Analytics Dashboard", "📥 Add Promotion Card", "✏️ Edit Store Catalog"])
        
        # TAB 1: Analytics metrics dashboard
        with op_menu[0]:
            my_items = [x for x in items if x.get('merchant_id') == st.session_state.merchant_id]
            my_clicks = len([a for a in analytics_data if a.get('merchant_id') == st.session_state.merchant_id])
            
            # FIXED: Refined metadata metrics using high-readability phrasing for non-technical users
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.markdown(f"<div class='metric-card'><div class='metric-val'>{my_clicks * 4}</div><div class='metric-lbl'>Views Today</div></div>", unsafe_allow_html=True)
            col_m2.markdown(f"<div class='metric-card'><div class='metric-val'>{len(my_items)}</div><div class='metric-lbl'>Active Deals</div></div>", unsafe_allow_html=True)
            col_m3.markdown(f"<div class='metric-card'><div class='metric-val'>{my_clicks}</div><div class='metric-lbl'>WhatsApp Clicks</div></div>", unsafe_allow_html=True)
            
        # TAB 2: Add Promotion Card
        with op_menu[1]:
            with st.form(key="add_item_form_new", clear_on_submit=True):
                col_inputs = st.columns(2)
                n_title = col_inputs[0].text_input("Product Title*")
                n_cat = col_inputs[1].selectbox("Category Field*", ["Electronics", "Fashion", "Grocery", "Home", "General"])
                n_price = col_inputs[0].number_input("Deal Value (₹)*", min_value=0, step=50)
                # FIXED: Relabeled to lower merchant friction points completely
                n_img = col_inputs[1].text_input("Upload Photo (Paste Link)", placeholder="https://unsplash.com/...")
                n_desc = st.text_area("Specifications details content text string*")
                n_loc = st.selectbox("Assign Distribution Hub Area Node*", ["North Authoor", "Central Bazar", "Tiruchendur Road", "Millerpuram"])
                
                if st.form_submit_button("🚀 Deploy Broadcast Entry Live", use_container_width=True):
                    if n_title.strip() and n_desc.strip() and n_price > 0:
                        coords = {"North Authoor": (8.8050, 78.1519), "Central Bazar": (8.8100, 78.1450), "Tiruchendur Road": (8.7950, 78.1600), "Millerpuram": (8.8020, 78.1320)}.get(n_loc, (8.8050, 78.1519))
                        supabase.table("items").insert({"title": n_title.strip(), "description": n_desc.strip(), "category": n_cat, "price": n_price, "location": n_loc, "image_url": n_img.strip(), "latitude": coords[0], "longitude": coords[1], "merchant_id": st.session_state.merchant_id}).execute()
                        st.success("Deal broadcast catalog pipeline synced successfully!")
                        st.rerun()

        # TAB 3: Edit / Delete catalog records
        with op_menu[2]:
            my_items = [i for i in items if i.get('merchant_id') == st.session_state.merchant_id]
            if my_items:
                edit_select = st.selectbox("Select deal record card to modify:", my_items, format_func=lambda x: f"{x.get('title')} ({format_indian_currency(x.get('price'))})")
                if edit_select:
                    with st.form(key="edit_catalog_form"):
                        e_title = st.text_input("Product Title", value=edit_select.get('title'))
                        e_price = st.number_input("Price Value (₹)", value=int(edit_select.get('price', 0)))
                        e_img = st.text_input("Photo Link", value=edit_select.get('image_url', ''))
                        e_desc = st.text_area("Description Text", value=edit_select.get('description'))
                        
                        col_actions = st.columns([4, 1])
                        if col_actions[0].form_submit_button("💾 Save Database Record Alterations", use_container_width=True):
                            supabase.table("items").update({"title": e_title.strip(), "price": e_price, "image_url": e_img.strip(), "description": e_desc.strip()}).eq("id", edit_select.get('id')).execute()
                            st.success("Alterations synchronized live successfully!")
                            st.rerun()
                        if col_actions[1].form_submit_button("🗑️ Delete Listing", use_container_width=True):
                            supabase.table("items").delete().eq("id", edit_select.get('id')).execute()
                            st.rerun()
            else:
                st.info("No active catalog promotional metrics available under your assigned ID yet.")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Logout of Portal Session Framework", type="primary"):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.rerun()
