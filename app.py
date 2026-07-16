import os
import math
import re
import streamlit as st
from supabase import create_client, Client
from streamlit_geolocation import streamlit_geolocation
import pandas as pd

# 1. Page Configuration & Premium UI Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    /* Global Styles & Micro-Animations */
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    
    /* Uniform Badge Alignment Framework */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 12px;
        align-items: center;
    }
    .badge { background-color: #1e1e24; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; color: #00d2ff; font-weight: 600; display: inline-block; }
    .loc-badge { background-color: #2a2315; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; color: #ffaa00; font-weight: 600; display: inline-block; }
    .dist-badge { background-color: #1b2a3a; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; color: #00ffcc; font-weight: 600; display: inline-block; }
    .verified-badge { background-color: #064e3b; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; color: #34d399; font-weight: 700; border: 1px solid #059669; display: inline-block; }
    
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
    
    /* Card Layout Hover Animation */
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

# Initialize Session States safely
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# 2. Initialize Supabase Connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase API keys in Render secrets.")
    st.stop()

# Track Page View Hits
if "tracked_view" not in st.session_state:
    try:
        supabase.table("analytics").insert({"event_type": "page_view"}).execute()
        st.session_state.tracked_view = True
    except Exception:
        pass

def clean_listing_text(text):
    if not text: return ""
    cleaned = re.sub(r'\[\s*URGENT\s*DEAL\s*\]', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'URGENT', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\|VERIFIED\|', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[🚨🔴🔥🛑❗❗]', '', cleaned)
    return cleaned.strip()

def calculate_distance(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return None
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = rad_lat2 - rad_lat1, rad_lon2 - rad_lon1
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# Fetch databases
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

# 3. Sidebar Console
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
        merchant_menu = st.radio("Navigation Menu", ["📊 Dashboard Analytics", "📥 Deploy New Listing", "✏️ Edit/Manage Listings", "⚙️ Shop Settings"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out of Portal", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.rerun()

    st.markdown("---")
    st.markdown("### ❤️ My Saved Deals")
    if st.session_state.favorites:
        fav_items = [item for item in items if item.get('id') in st.session_state.favorites]
        for f_item in fav_items:
            col_fav1, col_fav2 = st.columns([4, 1])
            with col_fav1: st.markdown(f"**{f_item.get('title')}** (₹{f_item.get('price')})")
            with col_fav2:
                if st.button("❌", key=f"rm_fav_{f_item.get('id')}"):
                    st.session_state.favorites.remove(f_item.get('id'))
                    st.rerun()
    else: st.caption("No deals saved yet.")

is_merchant = st.session_state.logged_in

# 4. Main Header
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Auto-Detecting Nearby Deals Safely and Privately")
st.markdown("<br>", unsafe_allow_html=True)

location_data = streamlit_geolocation()
user_lat, user_lon = location_data.get("latitude"), location_data.get("longitude")

with st.container():
    if user_lat and user_lon:
        st.markdown(f"<div class='hero-scanner-box'><h3 style='margin:0 0 6px 0; color:#34d399;'>📍 Location Scanner Connected</h3><p style='margin:0; color:#9ca3af;'>Showcasing all live deals sorted directly by proximity.</p></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='hero-scanner-box'><h3 style='margin:0 0 6px 0; color:#a5b4fc;'>📡 Engage Proximity Scan</h3><p style='margin:0; color:#9ca3af;'>Click the tracking switch below to sort your deals geometrically.</p></div>", unsafe_allow_html=True)

# 5. Dashboard View Options
if is_merchant and merchant_menu == "📊 Dashboard Analytics":
    st.markdown(f"<div class='section-header'>📊 Performance Metrics for {st.session_state.merchant_name}</div>", unsafe_allow_html=True)
    real_views = len([x for x in analytics_data if x.get('event_type') == 'page_view'])
    real_clicks = len([x for x in analytics_data if x.get('event_type') == 'whatsapp_click'])
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric(label="Total Active Deals", value=len(items))
    with col_m2: st.metric(label="Registered Shop Partners", value=len(merchant_directory))
    with col_m3: st.metric(label="Real Page Views", value=real_views)
    with col_m4: st.metric(label="WhatsApp Chats Initiated", value=real_clicks)
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

# 6. Deploy Form Interface Tier
if is_merchant and merchant_menu == "📥 Deploy New Listing":
    st.markdown(f"<div class='section-header'>📥 Deploy New Promotional Item</div>", unsafe_allow_html=True)
    with st.container(border=True):
        with st.form(key="add_item_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            new_title = c1.text_input("Product Title*", placeholder="e.g., Sony TV")
            new_cat = c2.selectbox("Product Category*", ["General", "Electronics", "Vehicles", "Housing"])
            new_price = c3.number_input("Price (₹)*", min_value=0, step=10, value=0)
            c4, c5 = st.columns(2)
            new_desc = c4.text_input("Description Content*", placeholder="Condition, time frames...")
            new_loc = c5.text_input("City/Area Label*", placeholder="e.g., North Authoor, Thoothukudi")
            c6, c7 = st.columns(2)
            item_lat_input = c6.number_input("Item Latitude (Decimal)*", format="%.6f", value=8.8050, step=0.0001)
            item_lon_input = c7.number_input("Item Longitude (Decimal)*", format="%.6f", value=78.1519, step=0.0001)
            c8, c9 = st.columns(2)
            uploaded_file = c8.file_uploader("Upload Product Image", type=["png", "jpg", "jpeg"])
            new_payment = c9.text_input("Payment Link (Optional)")
            if st.form_submit_button("🚀 Deploy Listing Live", use_container_width=True, type="primary"):
                if new_title.strip() and new_desc.strip() and new_price > 0:
                    final_image_url = None
                    if uploaded_file:
                        try:
                            f_name = f"{st.session_state.merchant_id}_{uploaded_file.name}"
                            supabase.storage.from_("product-images").upload(path=f_name, file=uploaded_file.read(), file_options={"content-type": uploaded_file.type})
                            final_image_url = supabase.storage.from_("product-images").get_public_url(f_name)
                        except Exception: pass
                    try:
                        payload = {"title": clean_listing_text(new_title), "description": clean_listing_text(new_desc), "category": new_cat, "price": new_price, "location": new_loc if new_loc.strip() else "Local Area", "latitude": item_lat_input, "longitude": item_lon_input, "merchant_id": st.session_state.merchant_id}
                        if final_image_url: payload["image_url"] = final_image_url
                        if new_payment.strip(): payload["payment_url"] = new_payment.strip()
                        supabase.table("items").insert(payload).execute()
                        st.success("Listing deployed successfully!")
                        st.rerun()
                    except Exception as err: st.error(f"Error: {err}")
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

# 7. Edit/Manage Listings
if is_merchant and merchant_menu == "✏️ Edit/Manage Listings":
    st.markdown(f"<div class='section-header'>✏️ Edit and Update Active Web Listings</div>", unsafe_allow_html=True)
    my_items = [i for i in items if i.get('merchant_id') == st.session_state.merchant_id]
    if my_items:
        item_to_edit = st.selectbox("Select a listing to edit:", my_items, format_func=lambda x: f"{x.get('title')} (₹{x.get('price')})")
        if item_to_edit:
            st.markdown("### Update Values Below:")
            with st.container(border=True):
                with st.form(key="edit_item_form"):
                    e_title = st.text_input("Product Title", value=item_to_edit.get('title'))
                    e_cat = st.selectbox("Category", ["General", "Electronics", "Vehicles", "Housing"], index=["General", "Electronics", "Vehicles", "Housing"].index(item_to_edit.get('category', 'General')))
                    e_price = st.number_input("Price (₹)", value=int(item_to_edit.get('price', 0)))
                    e_desc = st.text_input("Description", value=item_to_edit.get('description'))
                    e_loc = st.text_input("City/Area Label", value=item_to_edit.get('location'))
                    e_lat = st.number_input("Latitude (Decimal)", format="%.6f", value=float(item_to_edit.get('latitude', 8.8050)))
                    e_lon = st.number_input("Longitude (Decimal)", format="%.6f", value=float(item_to_edit.get('longitude', 78.1519)))
                    e_pay = st.text_input("Payment Link", value=item_to_edit.get('payment_url', ''))
                    if st.form_submit_button("💾 Save Changes to Web Database", use_container_width=True, type="primary"):
                        try:
                            update_payload = {"title": clean_listing_text(e_title), "category": e_cat, "price": e_price, "description": clean_listing_text(e_desc), "location": e_loc if e_loc.strip() else "Local Area", "latitude": e_lat, "longitude": e_lon, "payment_url": e_pay}
                            supabase.table("items").update(update_payload).eq("id", item_to_edit.get('id')).execute()
                            st.success("Database parameters modified successfully live!")
                            st.rerun()
                        except Exception as edit_err: st.error(f"Failed to save changes: {edit_err}")
    else: st.info("You don't have any active listings deployed under this shop profile yet.")
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

if is_merchant and merchant_menu == "⚙️ Shop Settings":
    st.markdown(f"<div class='section-header'>⚙️ Profile Configurations</div>", unsafe_allow_html=True)
    st.info("Profiles operational.")
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

# 8. Core Consumer Filter Section
st.markdown("<div class='section-header'>🔍 Filter Controls</div>", unsafe_allow_html=True)
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    search_query = col_f1.text_input("Search...", placeholder="Type keywords here to look up items...", label_visibility="collapsed")
    category = col_f2.selectbox("Category Selector", ["All Categories", "General", "Electronics", "Vehicles", "Housing"], label_visibility="collapsed")
    max_budget = col_f3.slider("Max Budget Target (₹)", min_value=0, max_value=300000, value=150000, step=5000)

st.markdown("<br><br>", unsafe_allow_html=True)

# 9. Filter Logic Loop
filtered_items, map_data_list = [], []
for i in items:
    t_clean, d_clean, c_clean = clean_listing_text(i.get('title', '')), clean_listing_text(i.get('description', '')), clean_listing_text(i.get('category', 'General'))
    s_match = (search_query.lower() in t_clean.lower() or search_query.lower() in d_clean.lower())
    c_match = (category == "All Categories" or (category.lower() in c_clean.lower()))
    try: price_val = float(i.get('price', 0))
    except: price_val = 0
    i_lat, i_lon = i.get('latitude'), i.get('longitude')
    i['calculated_distance'] = calculate_distance(user_lat, user_lon, i_lat, i_lon)
    i['title'], i['description'], i['category'] = t_clean, d_clean, c_clean
    if not i.get('location') or i.get('location') == "None": i['location'] = "Local Area"
    if s_match and c_match and (price_val <= max_budget):
        filtered_items.append(i)
        if i_lat is not None and i_lon is not None: map_data_list.append({"latitude": float(i_lat), "longitude": float(i_lon)})

if user_lat and user_lon:
    filtered_items.sort(key=lambda x: x['calculated_distance'] if x['calculated_distance'] is not None else float('inf'))

if map_data_list:
    st.markdown("### 🗺️ Neighborhood Deal Map")
    st.map(pd.DataFrame(map_data_list), use_container_width=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# 10. Card Presentation Layout Rendering
if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 3]:
            with st.container(border=True):
                img_url = item.get('image_url') or item.get('photo_url')
                if img_url and img_url.strip() and img_url != "None":
                    st.markdown(f"<div class='img-container'><img src='{img_url}' alt='Product Image'></div>", unsafe_allow_html=True)
                else:
                    cat_type, item_title = str(item.get('category', 'General')).lower(), str(item.get('title', '')).lower()
                    emoji = "📦"
                    if "elect" in cat_type:
                        if any(k in item_title for k in ["tv", "television", "display", "monitor"]): emoji = "📺"
                        elif any(k in item_title for k in ["mac", "book", "laptop", "pc"]): emoji = "💻"
                        elif any(k in item_title for k in ["watch", "smartwatch"]): emoji = "⌚"
                        elif any(k in item_title for k in ["fridge", "ac", "cooler"]): emoji = "🔌"
                        else: emoji = "📱"
                    elif "hous" in cat_type: emoji = "🪑" if any(k in item_title for k in ["sofa", "chair", "table"]) else "🏠"
                    elif "vehic" in cat_type: emoji = "🏍️" if any(k in item_title for k in ["bike", "scooter"]) else "🚗"
                    st.markdown(f"<div class='img-container'><div class='placeholder-icon'>{emoji}</div></div>", unsafe_allow_html=True)
                
                dist_v = item.get('calculated_distance')
                dist_html = f"<span class='dist-badge'>⚡ {dist_v:.1f} km away</span>" if dist_v is not None else ""
                
                associated_merchant = item.get('merchant_id')
                is_verified = associated_merchant in verified_merchants and associated_merchant is not None
                v_html = "<span class='verified-badge'>✨ Verified Shop</span>" if is_verified else ""
                
                # Fixed Layout Order inside the flex block
                st.markdown(f"""
                    <div class='badge-container'>
                        <span class='badge'>🏷️ {item.get('category', 'General')}</span>
                        <span class='loc-badge'>📍 {item.get('location', 'Local Area')}</span>
                        {dist_html}
                        {v_html}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='product-title'>{item.get('title', 'No Title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='product-price'>₹{float(item.get('price', 0)):,.2f}</div>", unsafe_allow_html=True)
                st.write(item.get('description', ''))
                
                item_id = item['id']
                is_fav = item_id in st.session_state.favorites
                if st.button("❤️ Bookmarked" if is_fav else "🤍 Favorite Deal", key=f"fav_{item_id}", use_container_width=True):
                    if is_fav: st.session_state.favorites.remove(item_id)
                    else: st.session_state.favorites.append(item_id)
                    st.rerun()
                
                if is_merchant and item.get('merchant_id') == st.session_state.merchant_id:
                    st.markdown("---")
                    if st.button(f"🗑️ Remove Listing", key=f"del_{item_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("items").delete().eq("id", item_id).execute()
                            st.success("Listing cleared!")
                            st.rerun()
                        except Exception as err: st.error(f"Error: {err}")
                else:
                    st.markdown("<div style='margin-top: 12px; margin-bottom: 12px;'><a class='report-link' href='#'>⚠️ Report Listing</a></div>", unsafe_allow_html=True)
                    with st.expander("📝 Write a Review"):
                        with st.form(key=f"rev_{item_id}", clear_on_submit=True):
                            u_rating = st.selectbox("Stars", [5,4,3,2,1], key=f"s_{item_id}")
                            u_comment = st.text_input("Comment...", key=f"c_{item_id}")
                            if st.form_submit_button("Submit"):
                                if u_comment.strip():
                                    try: 
                                        supabase.table("feedback").insert({"item_id": item_id, "rating": u_rating, "comment": u_comment}).execute()
                                        st.rerun()
                                    except: pass
                    
                    pay_url = item.get('payment_url')
                    if pay_url and pay_url != "None": st.link_button("💳 Instant Buy / Pay Now", pay_url, use_container_width=True, type="primary")
                    
                    phone = merchant_directory.get(item.get('merchant_id'), "918072130833")
                    wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20interested%20in%20{item.get('title')}"
                    if st.button("💬 Chat on WhatsApp", key=f"wa_{item_id}", use_container_width=True):
                        try: supabase.table("analytics").insert({"event_type": "whatsapp_click"}).execute()
                        except: pass
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={wa_url}">', unsafe_allow_html=True)
else:
    st.info("No active promotions match your filter scopes currently.")
