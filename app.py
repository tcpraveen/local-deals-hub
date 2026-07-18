import os
import math
import re
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Page Configuration & Premium Dark UI Styling Configuration
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    /* Premium Dark Mode Global Canvas Layout */
    .stApp {
        background-color: #0f172a !important;
    }
    
    /* Merchant Dashboard Analytics Tier */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
    }
    
    /* Dark Theme Hero Banner Frame */
    .hero-scanner-box {
        background-color: #1e293b;
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        border-left: 5px solid #2874f0;
    }
    
    /* Sidebar Portal Custom Badging Styles */
    .merchant-profile-box {
        display: flex;
        align-items: center;
        gap: 12px;
        background-color: #1e293b;
        padding: 10px;
        border-radius: 6px;
        border: 1px solid #334155;
        margin-bottom: 15px;
    }
    .merchant-logo-img {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        object-fit: cover;
        background-color: #0f172a;
    }
    
    /* Clean Dark Input Filter Forms Area */
    div[data-testid="stForm"] {
        background-color: #1e293b !important;
        border: none !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2) !important;
        padding: 15px !important;
    }
    
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f8fafc;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    /* Sleek Marketplace Product Card Framework Layout */
    .product-card-frame {
        background-color: #1e293b;
        border-radius: 6px;
        padding: 16px;
        box-shadow: 0 2px 8px 0 rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        height: 100%;
        border: 1px solid #334155;
    }
    .product-card-frame:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.4);
        border-color: #475569;
    }
    
    /* Dynamic Dark Image Canvas Cover Container */
    .img-container {
        width: 100%;
        height: 180px;
        overflow: hidden;
        background-color: #0f172a;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        border-radius: 4px;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .placeholder-icon { 
        font-size: 4.5rem; 
        color: #64748b;
    }
    
    /* Typography Component Rules */
    .product-title {
        font-size: 1.05rem;
        font-weight: 500;
        color: #f8fafc;
        margin-bottom: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .product-price {
        font-size: 1.25rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 6px;
    }
    
    .product-desc {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 12px;
        height: 40px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    
    /* Badge tags layout arrays */
    .tag-row {
        display: flex;
        gap: 6px;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    .ui-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 6px;
        border-radius: 3px;
        text-transform: uppercase;
    }
    .cat-tag { background-color: #0369a1; color: #e0f2fe; }
    .loc-tag { background-color: #334155; color: #cbd5e1; }
    
    /* Form input text label styling hooks */
    div[data-testid="stWidgetLabel"] p {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }
    h1 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "merchant_id" not in st.session_state:
    st.session_state.merchant_id = None
if "merchant_name" not in st.session_state:
    st.session_state.merchant_name = None
if "merchant_logo" not in st.session_state:
    st.session_state.merchant_logo = None

# 2. Supabase Connection Setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase configuration keys.")
    st.stop()

# Indian Currency Formatter Helper (₹1,50,000)
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

def clean_listing_text(text):
    if not text: return ""
    cleaned = re.sub(r'<[^>]*>', '', str(text))
    cleaned = re.sub(r'\[\s*URGENT\s*DEAL\s*\]', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

# Fetch DB Records safely
try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data if items_response.data else []
    merchants_response = supabase.table("merchants").select("shop_id, phone_number, is_verified, logo_url").execute()
    merchant_directory = {m['shop_id']: m.get('phone_number') for m in merchants_response.data} if merchants_response.data else {}
    verified_merchants = {m['shop_id'] for m in merchants_response.data if m.get('is_verified') is True} if merchants_response.data else set()
    analytics_response = supabase.table("analytics").select("*").execute()
    analytics_data = analytics_response.data if analytics_response.data else []
except Exception:
    items, merchant_directory, verified_merchants, analytics_data = [], {}, set(), []

# 3. Sidebar Panel Interface Console
with st.sidebar:
    st.markdown("### 🛍️ Merchant Management")
    if not st.session_state.logged_in:
        input_shop_id = st.text_input("Username", placeholder="e.g., shop_01")
        input_password = st.text_input("Password", type="password")
        if st.button("Login to Shop Portal", use_container_width=True, type="primary"):
            if input_shop_id.strip() and input_password.strip():
                try:
                    response = supabase.table("merchants").select("*").eq("shop_id", input_shop_id.strip()).execute()
                    if response.data and response.data[0].get("password") == input_password.strip():
                        st.session_state.logged_in = True
                        st.session_state.merchant_id = response.data[0].get("shop_id")
                        st.session_state.merchant_name = response.data[0].get("shop_name")
                        st.session_state.merchant_logo = response.data[0].get("logo_url")
                        st.rerun()
                    else: st.error("Invalid credentials.")
                except Exception as err: st.error(f"Error: {err}")
    else:
        # Shop Logo Branding Injection
        logo_display = st.session_state.merchant_logo if st.session_state.merchant_logo else "https://cdn-icons-png.flaticon.com/512/606/606547.png"
        st.markdown(f"""
            <div class="merchant-profile-box">
                <img src="{logo_display}" class="merchant-logo-img">
                <div>
                    <div style="color:#ffffff; font-weight:600; font-size:0.95rem;">{st.session_state.merchant_name}</div>
                    <div style="color:#4ade80; font-size:0.75rem; font-weight:500;">🔒 Active Session</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        merchant_menu = st.radio("Tasks Menu", ["📊 Dashboard Analytics", "📥 Add New Item", "✏️ Edit Listings"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.session_state.merchant_logo = None
            st.rerun()

is_merchant = st.session_state.logged_in

# 4. Main App Branding Frame Layout
st.markdown("<h1 style='font-weight:600; margin-bottom:0;'>Neighborhood Deals Hub</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; margin-top:0; font-size:0.95rem;'>Browse live promotions scaled directly onto local catalog nodes.</p>", unsafe_allow_html=True)

# 5. Core Live Clicks Analytics Counter Layer
if is_merchant and merchant_menu == "📊 Dashboard Analytics":
    st.markdown(f"<div class='section-header'>📊 Store Operational Performance ({st.session_state.merchant_name})</div>", unsafe_allow_html=True)
    
    my_products_count = len([x for x in items if x.get('merchant_id') == st.session_state.merchant_id])
    my_clicks = len([a for a in analytics_data if a.get('merchant_id') == st.session_state.merchant_id])
    estimated_views = my_clicks * 4  # Balanced local visibility calculation pipeline scale
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.markdown(f"<div class='metric-card'><div class='metric-val'>{estimated_views}</div><div class='metric-lbl'>Estimated Views</div></div>", unsafe_allow_html=True)
    col_m2.markdown(f"<div class='metric-card'><div class='metric-val'>{my_products_count}</div><div class='metric-lbl'>Active Products</div></div>", unsafe_allow_html=True)
    col_m3.markdown(f"<div class='metric-card'><div class='metric-val'>{my_clicks}</div><div class='metric-lbl'>WhatsApp Leads / Clicks</div></div>", unsafe_allow_html=True)
    st.markdown("<br><hr style='border-color:#334155;'><br>", unsafe_allow_html=True)

# 6. Form Deployment Console Tier
if is_merchant and merchant_menu == "📥 Add New Item":
    st.markdown(f"<div class='section-header'>📥 Deploy New Item</div>", unsafe_allow_html=True)
    with st.form(key="add_item_form", clear_on_submit=True):
        new_title = st.text_input("Product Title*")
        new_cat = st.selectbox("Product Category*", ["General", "Electronics", "Vehicles", "Housing"])
        new_price = st.number_input("Price (₹)*", min_value=0, step=10)
        new_img_url = st.text_input("Product Image URL", placeholder="https://example.com/photo.jpg")
        new_desc = st.text_input("Description Content*")
        new_loc = st.text_input("City/Area Label*", value="Thoothukudi")
        if st.form_submit_button("🚀 Deploy Listing Live", use_container_width=True):
            if new_title.strip() and new_desc.strip() and new_price > 0:
                try:
                    payload = {"title": clean_listing_text(new_title), "description": clean_listing_text(new_desc), "category": new_cat, "price": new_price, "location": clean_listing_text(new_loc), "image_url": new_img_url.strip(), "latitude": 8.8050, "longitude": 78.1519, "merchant_id": st.session_state.merchant_id}
                    supabase.table("items").insert(payload).execute()
                    st.success("Listing deployed successfully!")
                    st.rerun()
                except Exception as err: st.error(f"Error: {err}")

# 7. Web Editor Manager Interface Tier
if is_merchant and merchant_menu == "✏️ Edit Listings":
    st.markdown(f"<div class='section-header'>✏️ Edit Live Web Listings</div>", unsafe_allow_html=True)
    my_items = [i for i in items if i.get('merchant_id') == st.session_state.merchant_id]
    if my_items:
        item_to_edit = st.selectbox("Select listing to modify:", my_items, format_func=lambda x: f"{clean_listing_text(x.get('title'))} ({format_indian_currency(x.get('price'))})")
        if item_to_edit:
            with st.form(key="edit_item_form"):
                e_title = st.text_input("Product Title", value=clean_listing_text(item_to_edit.get('title')))
                e_cat = st.selectbox("Category", ["General", "Electronics", "Vehicles", "Housing"], index=["General", "Electronics", "Vehicles", "Housing"].index(item_to_edit.get('category', 'General')))
                e_price = st.number_input("Price (₹)", value=int(item_to_edit.get('price', 0)))
                e_img = st.text_input("Image URL", value=item_to_edit.get('image_url', ''))
                e_desc = st.text_input("Description", value=clean_listing_text(item_to_edit.get('description')))
                e_loc = st.text_input("City/Area Label", value=clean_listing_text(item_to_edit.get('location')))
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    try:
                        update_payload = {"title": clean_listing_text(e_title), "category": e_cat, "price": e_price, "image_url": e_img.strip(), "description": clean_listing_text(e_desc), "location": clean_listing_text(e_loc)}
                        supabase.table("items").update(update_payload).eq("id", item_to_edit.get('id')).execute()
                        st.success("Database record updated successfully!")
                        st.rerun()
                    except Exception as edit_err: st.error(f"Failed: {edit_err}")

# 8. Core Consumer Filter Section
with st.container():
    col_f1, col_f2 = st.columns([3, 1])
    search_query = col_f1.text_input("Search query", placeholder="Search for products, stores and more...", label_visibility="collapsed")
    category = col_f2.selectbox("Category Filter", ["All Categories", "General", "Electronics", "Vehicles", "Housing"], label_visibility="collapsed")

# 9. Clean Filter Processing Logic Loop
filtered_items = []
map_data_list = []
for i in items:
    t_clean = clean_listing_text(i.get('title', ''))
    d_clean = clean_listing_text(i.get('description', ''))
    c_clean = clean_listing_text(i.get('category', 'General'))
    l_clean = clean_listing_text(i.get('location', 'Thoothukudi'))
    
    s_match = (search_query.lower() in t_clean.lower() or search_query.lower() in d_clean.lower())
    c_match = (category == "All Categories" or (category.lower() in c_clean.lower()))
    
    i['title'], i['description'], i['category'], i['location'] = t_clean, d_clean, c_clean, l_clean
    
    if s_match and c_match:
        filtered_items.append(i)
        if i.get('latitude') and i.get('longitude'):
            map_data_list.append({"latitude": float(i.get('latitude')), "longitude": float(i.get('longitude'))})

# 10. Open Live Map Integration (Exposed Header Component View)
if map_data_list:
    st.markdown("<div class='section-header'>🗺️ Neighborhood Live Deals Map</div>", unsafe_allow_html=True)
    st.map(pd.DataFrame(map_data_list), use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# 11. Modernized Flipkart-Inspired Grid Presentation
if filtered_items:
    st.markdown("<div class='section-header'>🔥 Hot Promotions Near You</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 4]:
            
            # Dynamic Image Selection Logic Engine
            img_src = item.get('image_url')
            if img_src and str(img_src).strip().startswith("http"):
                img_html = f'<img src="{img_src.strip()}">'
            else:
                # Elegant emoji canvas placeholder backup standard
                img_html = '<div class="placeholder-icon">📺</div>'
                
            st.markdown(f"""
                <div class="product-card-frame">
                    <div class="img-container">
                        {img_html}
                    </div>
                    <div class="tag-row">
                        <span class="ui-badge cat-tag">{item.get('category')}</span>
                        <span class="ui-badge loc-tag">📍 {item.get('location')}</span>
                    </div>
                    <div class="product-title">{item.get('title')}</div>
                    <div class="product-price">{format_indian_currency(item.get('price', 0))}</div>
                    <div class="product-desc">{item.get('description')}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # High-Contrast Bright Green Verification Badge
            is_verified = item.get('merchant_id') in verified_merchants and item.get('merchant_id') is not None
            if is_verified:
                st.markdown("<p style='color: #4ade80; font-weight: 600; font-size: 0.85rem; margin-top: 6px; margin-bottom: 4px;'>✨ Verified Store Promotion</p>", unsafe_allow_html=True)
                
            if is_merchant and item.get('merchant_id') == st.session_state.merchant_id:
                if st.button(f"🗑️ Delete", key=f"del_{item['id']}", type="primary", use_container_width=True):
                    supabase.table("items").delete().eq("id", item['id']).execute()
                    st.rerun()
            else:
                phone = merchant_directory.get(item.get('merchant_id'), "918072130833")
                
                # WhatsApp lead generation logging execution callback pipeline
                def log_lead_click(m_id, item_id):
                    try:
                        supabase.table("analytics").insert({"merchant_id": m_id, "item_id": item_id}).execute()
                    except: pass
                
                wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20interested%20in%20{item.get('title')}"
                st.link_button("💬 Chat on WhatsApp", wa_url, use_container_width=True, on_click=log_lead_click, args=(item.get('merchant_id'), item.get('id')))
            
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("No active local deals match your query parameters.")
