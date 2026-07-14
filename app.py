import os
import math
import re
import streamlit as st
from supabase import create_client, Client
from streamlit_geolocation import streamlit_geolocation

# 1. Page Configuration & Professional Premium Theme UI Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    .badge { background-color: #1e1e24; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #00d2ff; font-weight: 600; margin-right: 5px; }
    .loc-badge { background-color: #2a2315; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #ffaa00; font-weight: 600; margin-right: 5px; }
    .dist-badge { background-color: #1b2a3a; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #00ffcc; font-weight: 600; }
    .verified-badge { background-color: #064e3b; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #34d399; font-weight: 700; margin-right: 5px; border: 1px solid #059669; }
    
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
    
    div[data-testid="stMetric"] {
        background-color: #1a1c23;
        border: 1px solid #2d313f;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
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
    .placeholder-icon {
        font-size: 4rem;
    }
    
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select {
        border: 1px solid #2d313f !important;
        background-color: #14161d !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    
    .hero-scanner-box {
        background: linear-gradient(135deg, #1e1b4b 0%, #111827 100%);
        border: 2px solid #4f46e5;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States safely
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None

# 2. Initialize Supabase Connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase API keys in Render environment secrets.")
    st.stop()

# Server-Side Listing Quality Content Rules Filter Engine
def clean_listing_text(text):
    if not text:
        return ""
    cleaned = re.sub(r'\[\s*URGENT\s*DEAL\s*\]', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'URGENT', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\|VERIFIED\|', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[🚨🔴🔥🛑❗❗]', '', cleaned)
    return cleaned.strip()

# Haversine Proximity Math Calculation
def calculate_distance(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 3. Sidebar – Multi-Tenant Shopkeeper Portal
with st.sidebar:
    st.markdown("## 🛍️ Shopkeeper Portal")
    
    if not st.session_state.logged_in:
        st.write("Sign in with your Shop Credentials")
        input_shop_id = st.text_input("Shopkeeper ID / Username", placeholder="e.g., shop_01")
        input_password = st.text_input("Merchant Password", type="password", placeholder="Enter account password")
        
        if st.button("Secure Login", use_container_width=True, type="primary"):
            if input_shop_id.strip() and input_password.strip():
                try:
                    response = supabase.table("merchants").select("*").eq("shop_id", input_shop_id.strip()).execute()
                    merchant_data = response.data
                    
                    if merchant_data and merchant_data[0].get("password") == input_password.strip():
                        st.session_state.logged_in = True
                        st.session_state.merchant_id = merchant_data[0].get("shop_id")
                        st.session_state.merchant_name = merchant_data[0].get("shop_name")
                        st.success(f"Logged in: {st.session_state.merchant_name}")
                        st.rerun()
                    else:
                        st.error("Invalid Shop ID or Password.")
                except Exception as login_err:
                    st.error(f"Authentication Service Error: {login_err}")
            else:
                st.warning("Please enter both fields.")
    else:
        st.success(f"🔒 Active: {st.session_state.merchant_name}")
        st.caption(f"ID Ref: `{st.session_state.merchant_id}`")
        if st.button("Log Out of Portal", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.rerun()

is_merchant = st.session_state.logged_in

# 4. Main Header Banner Layout
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Auto-Detecting Nearby Deals Safely and Privately")

st.markdown("""
<div class='hero-scanner-box'>
    <h3 style='margin:0 0 8px 0; color:#a5b4fc;'>📡 Tap to Scan Your Neighborhood</h3>
    <p style='margin:0 0 12px 0; font-size:0.9rem; color:#9ca3af;'>Grant safe browser GPS access below to instantly organize listings by real walking distance.</p>
</div>
""", unsafe_allow_html=True)

location_data = streamlit_geolocation()
user_lat = location_data.get("latitude")
user_lon = location_data.get("longitude")

if user_lat and user_lon:
    st.success(f"📍 Location automatically locked: Coordinates ({user_lat:.4f}, {user_lon:.4f})")
else:
    st.caption("💡 Tip: Enabling location permissions prioritizes active promotions right down your block.")

st.markdown("<br>", unsafe_allow_html=True)

# Fetch data pipelines from Supabase
try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data
    
    merchants_response = supabase.table("merchants").select("shop_id, phone_number").execute()
    merchant_directory = {m['shop_id']: m.get('phone_number') for m in merchants_response.data} if merchants_response.data else {}
except Exception as e:
    st.error(f"Database Error: {e}")
    items = []
    merchant_directory = {}

# 5. SECURE MERCHANT FORM INTERFACE
if is_merchant:
    st.markdown(f"<div class='section-header'>📥 Add New Item from {st.session_state.merchant_name}</div>", unsafe_allow_html=True)
    with st.container(border=True):
        with st.form(key="add_item_form", clear_on_submit=True):
            col_in1, col_in2, col_in3 = st.columns([2, 1, 1])
            with col_in1:
                new_title = st.text_input("Product Title*", placeholder="e.g., Fresh Sourdough Bread")
            with col_in2:
                new_cat = st.selectbox("Product Category*", ["General", "Electronics", "Vehicles", "Housing"])
            with col_in3:
                new_price = st.number_input("Price (₹)*", min_value=0, step=10, value=0)
                
            col_in4, col_in5 = st.columns([2, 2])
            with col_in4:
                new_desc = st.text_input("Description*", placeholder="Condition, specifics...")
            with col_in5:
                new_loc = st.text_input("City/Area Label*", placeholder="e.g., North Authoor, Coimbatore")
                
            col_gps1, col_gps2 = st.columns(2)
            with col_gps1:
                item_lat_input = st.number_input("Item Latitude (Decimal)*", format="%.6f", value=11.0168, step=0.0001)
            with col_gps2:
                item_lon_input = st.number_input("Item Longitude (Decimal)*", format="%.6f", value=76.9558, step=0.0001)
                
            col_in6, col_in7 = st.columns([2, 2])
            with col_in6:
                new_image = st.text_input("Product Photo URL (Optional)")
                st.caption("💡 Leaving this blank automatically applies a matching category vector icon.")
            with col_in7:
                new_payment = st.text_input("Payment Link (Optional)")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            submit_new_item = st.form_submit_button("🚀 Deploy Listing Live", use_container_width=True, type="primary")
            
            if submit_new_item:
                if new_title.strip() and new_desc.strip() and new_price > 0:
                    filtered_title = clean_listing_text(new_title)
                    filtered_desc = clean_listing_text(new_desc)
                    final_loc = new_loc.strip() if new_loc.strip() else "Local Area"
                    
                    try:
                        payload = {
                            "title": filtered_title,
                            "description": filtered_desc,
                            "category": new_cat,
                            "price": new_price,
                            "location": final_loc,
                            "latitude": item_lat_input,
                            "longitude": item_lon_input,
                            "merchant_id": st.session_state.merchant_id 
                        }
                        if new_image.strip():
                            payload["image_url"] = new_image.strip()
                        if new_payment.strip():
                            payload["payment_url"] = new_payment.strip()
                            
                        supabase.table("items").insert(payload).execute()
                        st.success("Listing successfully deployed live!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to push entry: {err}")
                else:
                    st.warning("Please fill out all required fields.")
    st.markdown("<br>", unsafe_allow_html=True)

# 6. Consumer Searching Panel & Filter System
st.markdown("<div class='section-header'>🔍 Filter Controls</div>", unsafe_allow_html=True)
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search_query = st.text_input("Search listings...", placeholder="Type keywords here...", label_visibility="collapsed")
    with col_f2:
        category = st.selectbox("Filter by Category", ["All Categories", "General", "Electronics", "Vehicles", "Housing"], label_visibility="collapsed")
    with col_f3:
        max_budget = st.slider("Max Budget (₹)", min_value=0, max_value=300000, value=150000, step=5000)

st.markdown("<br>", unsafe_allow_html=True)

# Content Sanitization & Proximity Sorting Engine
filtered_items = []
for i in items:
    t_clean = clean_listing_text(i.get('title', ''))
    d_clean = clean_listing_text(i.get('description', ''))
    c_clean = clean_listing_text(i.get('category', 'General'))
    
    search_match = (search_query.lower() in t_clean.lower() or search_query.lower() in d_clean.lower())
    cat_match = (category == "All Categories" or (category.lower() in c_clean.lower()))
    
    try:
        item_price = float(i.get('price', 0))
    except:
        item_price = 0
    price_match = (item_price <= max_budget)
    
    i_lat = i.get('latitude')
    i_lon = i.get('longitude')
    computed_dist = calculate_distance(user_lat, user_lon, i_lat, i_lon)
    i['calculated_distance'] = computed_dist
    
    i['title'] = t_clean
    i['description'] = d_clean
    i['category'] = c_clean
    if not i.get('location') or i.get('location') == "None":
        i['location'] = "Local Area"
        
    if search_match and cat_match and price_match:
        filtered_items.append(i)

if user_lat and user_lon:
    filtered_items.sort(key=lambda x: x['calculated_distance'] if x['calculated_distance'] is not None else float('inf'))

# 7. Dynamic Card Rendering Grid
if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 3]:
            with st.container(border=True):
                img_url = item.get('image_url') or item.get('photo_url')
                
                if img_url and img_url.strip() and img_url != "None":
                    st.markdown(f"""
                        <div class='img-container'>
                            <img src='{img_url}' alt='Product Image'>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    cat_type = str(item.get('category', 'General')).lower()
                    placeholder_emoji = "📦"
                    if "elect" in cat_type:
                        placeholder_emoji = "📱"
                    elif "hous" in cat_type:
                        placeholder_emoji = "🏠"
                    elif "vehic" in cat_type:
                        placeholder_emoji = "🚗"
                    
                    st.markdown(f"""
                        <div class='img-container'>
                            <div class='placeholder-icon'>{placeholder_emoji}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                dist_value = item.get('calculated_distance')
                dist_html = f"<span class='dist-badge'>⚡ {dist_value:.1f} km away</span>" if dist_value is not None else ""
                
                # Check backend verification mapping safely
                associated_merchant = item.get('merchant_id')
                is_verified_shop = associated_merchant in merchant_directory and associated_merchant is not None
                verified_html = "<span class='verified-badge'>✨ Verified Shop</span>" if is_verified_shop else ""
                
                st.markdown(f"""
                    <div style='margin-bottom: 6px;'>
                        <span class='badge'>🏷️ {item.get('category', 'General')}</span>
                        <span class='loc-badge'>📍 {item.get('location', 'Local Area')}</span>
                        {dist_html}
                        {verified_html}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='product-title'>{item.get('title', 'No Title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='product-price'>₹{float(item.get('price', 0)):,.2f}</div>", unsafe_allow_html=True)
                st.write(item.get('description', ''))
                
                item_id = item['id']
                
                if is_merchant and item.get('merchant_id') == st.session_state.merchant_id:
                    st.markdown("---")
                    st.caption("🛠️ Shop Manager Control Panel")
                    if st.button(f"🗑️ Remove Listing", key=f"del_{item_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("items").delete().eq("id", item_id).execute()
                            st.success("Listing removed!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error: {err}")
                else:
                    st.markdown("<div style='margin-top: 10px; margin-bottom: 10px;'><a class='report-link' href='#'>⚠️ Report Listing</a></div>", unsafe_allow_html=True)
                    
                    with st.expander("📝 Write a Review"):
                        with st.form(key=f"review_{item_id}", clear_on_submit=True):
                            user_rating = st.selectbox("Select Stars", [5, 4, 3, 2, 1], key=f"s_{item_id}")
                            user_comment = st.text_input("Comment...", key=f"c_{item_id}")
                            if st.form_submit_button("Submit"):
                                if user_comment.strip():
                                    try:
                                        supabase.table("feedback").insert({"item_id": item_id, "rating": user_rating, "comment": user_comment}).execute()
                                        st.success("Submitted!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error: {err}")
                    
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    pay_url = item.get('payment_url')
                    if pay_url and pay_url != "None":
                        st.link_button("💳 Instant Buy / Pay Now", pay_url, use_container_width=True, type="primary")
                    
                    raw_phone = merchant_directory.get(associated_merchant)
                    clean_phone = str(raw_phone).strip() if raw_phone else "918072130833"
                    
                    msg = f"Hi, I'm interested in buying your {item.get('title')} from Neighborhood Hub."
                    whatsapp_url = f"https://wa.me/{clean_phone}?text={msg.replace(' ', '%20')}"
                    
                    # Cleaned direct anchor button layout to bypass hover overlap bugs
                    st.markdown(f"""
                        <a href="{whatsapp_url}" target="_blank" style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            background-color: transparent;
                            color: #ffffff;
                            border: 1px solid #2d313f;
                            padding: 8px 16px;
                            border-radius: 8px;
                            text-decoration: none;
                            font-size: 0.9rem;
                            font-weight: 500;
                            transition: border-color 0.25s;
                            box-sizing: border-box;
                            margin-top: 8px;
                        " onmouseover="this.style.borderColor='#4f46e5'" onmouseout="this.style.borderColor='#2d313f'">
                            💬 Chat on WhatsApp
                        </a>
                    """, unsafe_allow_html=True)
else:
    st.info("No active neighborhood promotions match your filter scopes currently.")
