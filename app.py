import os
import math
import re
from datetime import datetime
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Page Setup & Universal Dark Mode Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0f172a !important;
    }
    
    /* Hide Streamlit default sidebar drawer */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Brand Header Navigation Bar */
    .brand-logo-box {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-logo-icon {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
    }
    
    .hero-tagline {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: -10px;
        margin-bottom: 15px;
        font-weight: 400;
    }

    /* Social Proof Trust Badges */
    .trust-badge-row {
        display: flex;
        gap: 18px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }
    .trust-chip {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: #cbd5e1;
        background-color: #1e293b;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #334155;
    }
    
    /* Product Card Architecture with 16:9 Aspect Ratio */
    .product-card-frame {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s ease;
        display: flex;
        flex-direction: column;
        height: 480px; 
        border: 1px solid #334155;
        overflow: hidden;
    }
    .product-card-frame:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 32px -8px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.15);
        border-color: #38bdf8;
    }
    
    /* 16:9 Image Box Container */
    .img-container {
        width: 100%;
        aspect-ratio: 16 / 9; 
        height: 220px;
        overflow: hidden;
        background-color: #0f172a;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        margin-bottom: 12px;
        position: relative;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover !important;
        border-radius: 8px !important;
        transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .product-card-frame:hover .img-container img {
        transform: scale(1.05); /* 5% Subtle Scale Zoom */
    }
    
    /* Card Text Details */
    .card-details-box {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex-grow: 1;
    }
    
    .product-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .merchant-name-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .product-price {
        font-size: 1.4rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 6px;
    }
    
    /* Status Badges & Metadata */
    .ux-metadata-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.78rem;
        color: #cbd5e1;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }
    .meta-item {
        background-color: #0f172a;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .status-badge-new {
        background-color: #14532d;
        color: #4ade80;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .status-badge-limited {
        background-color: #7f1d1d;
        color: #fca5a5;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .status-badge-ending {
        background-color: #7c2d12;
        color: #fdba74;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .rating-badge {
        background-color: #15803d !important;
        color: #ffffff;
        font-weight: 600;
    }
    
    .product-desc {
        font-size: 0.88rem;
        color: #94a3b8;
        line-height: 1.35;
        height: 36px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 5px;
    }

    /* Input & Form Styling Overrides */
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
    
    /* Analytics Cards Styling */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 18px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    .metric-val { font-size: 1.9rem; font-weight: 700; color: #38bdf8; }
    .metric-lbl { font-size: 0.82rem; color: #f8fafc; font-weight:600; margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .metric-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }
    .metric-trend { font-size: 0.75rem; color: #4ade80; font-weight: 600; margin-top: 4px; }

    .empty-state-box {
        background-color: #1e293b;
        border: 1px dashed #475569;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
    }

    /* Mobile Responsiveness Helper Rules */
    @media (max-width: 768px) {
        .product-card-frame {
            height: auto !important;
            margin-bottom: 20px;
        }
        .img-container {
            height: 200px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Session State Setup
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

# 2. Supabase Cloud Connection Setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase configuration keys.")
    st.stop()

# Helper Functions
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

# Fetch Database Records
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

# Default Unsplash High-Quality Fallback Stock Images
DEFAULT_IMAGES = {
    "Electronics": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?auto=format&fit=crop&w=800&q=80",
    "Fashion": "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=800&q=80",
    "Grocery": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=800&q=80",
    "Home": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
    "General": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=800&q=80"
}

# 3. Interactive Modal Sheet View (Item Details)
@st.dialog("📦 Deal Specifications & Store Details")
def show_deal_modal(item, shop_info):
    img_src = item.get('image_url')
    if not (img_src and str(img_src).strip().startswith("http")):
        img_src = DEFAULT_IMAGES.get(item.get('category'), DEFAULT_IMAGES["General"])
    st.image(img_src.strip(), use_column_width=True)
    
    st.markdown(f"### {item.get('title')}")
    st.markdown(f"## {format_indian_currency(item.get('price', 0))}")
    
    col_d1, col_d2 = st.columns(2)
    col_d1.markdown(f"**Store:** {shop_info.get('shop_name', 'Local Shop')}")
    col_d1.markdown(f"**Category:** {item.get('category', 'General')}")
    col_d2.markdown(f"**Rating:** ⭐ {shop_info.get('rating', 4.5)}")
    col_d2.markdown(f"**Opening Hours:** 9:00 AM - 9:30 PM")
    
    st.markdown("---")
    st.markdown("**Description & Specifications:**")
    st.write(item.get('description'))
    
    phone = shop_info.get('phone_number', '918072130833')
    wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20I'm%20interested%20in%20{item.get('title')}"
    st.link_button("💬 Chat on WhatsApp with Merchant", wa_url, use_container_width=True, type="primary")

# 4. HEADER NAVIGATION
with st.container():
    col_nav1, col_nav2 = st.columns([4, 1])
    with col_nav1:
        st.markdown("""
            <div class="brand-logo-box">
                <div class="brand-logo-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path>
                        <polygon points="13 6 10 11 13 11 11 16 15 10 12 10 13 6"></polygon>
                    </svg>
                </div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff;">
                    <span style="background: linear-gradient(90deg, #38bdf8, #2874f0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Neighborhood Deals Hub</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col_nav2:
        if st.session_state.view_mode == "Customer":
            if st.button("🏢 Merchant Login", use_container_width=True, type="secondary"):
                st.session_state.view_mode = "Merchant"
                st.rerun()
        else:
            if st.button("🛒 Customer View", use_container_width=True, type="primary"):
                st.session_state.view_mode = "Customer"
                st.rerun()

# 5. CUSTOMER VIEW PIPELINE
if st.session_state.view_mode == "Customer":
    st.markdown("<div class='hero-tagline'>Find the best deal from a nearby local shop in under 30 seconds.</div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="trust-badge-row">
            <div class="trust-chip">🏪 <b>250+</b> Local Shops</div>
            <div class="trust-chip">🏷️ <b>3,400+</b> Deals Posted</div>
            <div class="trust-chip">💬 <b>8,000+</b> WhatsApp Enquiries</div>
        </div>
    """, unsafe_allow_html=True)
    
    search_query = st.text_input("Search Engine Console Field", placeholder="🔍 Search products, brands, local stores...", label_visibility="collapsed")
    
    categories = ["All", "Electronics", "Fashion", "Grocery", "Home"]
    cat_cols = st.columns(len(categories))
    for idx, cat_name in enumerate(categories):
        if cat_cols[idx].button(cat_name, use_container_width=True, type="secondary" if st.session_state.current_category != cat_name else "primary"):
            st.session_state.current_category = cat_name
            st.rerun()
            
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

    # Integrated Map Container
    if map_data_list:
        st.components.v1.html(
            f"""
            <div style="border-radius:12px; overflow:hidden; height:260px;">
                <iframe src="https://maps.google.com/maps?q={user_lat},{user_lon}&z=14&output=embed" width="100%" height="260" frameborder="0" style="border:0;" allowfullscreen></iframe>
            </div>
            """,
            height=260
        )
        st.markdown("<br>", unsafe_allow_html=True)
        
    # The Core 16:9 Grid Layout
    if filtered_items:
        st.markdown("<h3 style='color:#ffffff; font-size:1.3rem; font-weight:600; margin-bottom:15px;'>🔥 Today's Best Deals</h3>", unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, item in enumerate(filtered_items):
            with cols[idx % 3]:
                img_src = item.get('image_url')
                if not (img_src and str(img_src).strip().startswith("http")):
                    img_src = DEFAULT_IMAGES.get(item.get('category'), DEFAULT_IMAGES["General"])
                
                img_html = f'<img src="{img_src.strip()}">'
                verified_badge = ' <span style="color:#2874f0; font-size:0.85rem;">💎</span>' if item.get('is_verified') else ''
                
                # Dynamic Status Badges Logic
                if idx % 3 == 0:
                    status_badge = '<span class="status-badge-new">🟢 New</span>'
                elif idx % 3 == 1:
                    status_badge = '<span class="status-badge-ending">🟠 Ending Soon</span>'
                else:
                    status_badge = '<span class="status-badge-limited">🔴 Limited Stock</span>'
                
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
                                    {status_badge}
                                    <span class="meta-item rating-badge">⭐ {item.get('shop_rating')}</span>
                                    <span class="meta-item">📍 {item.get('distance_km')} km</span>
                                </div>
                                <div class="product-desc">{item.get('description')}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                if col_btn1.button("🔍 View Details", key=f"details_{item.get('id')}", use_container_width=True):
                    show_deal_modal(item, merchants_dict.get(item.get('merchant_id'), {}))
                    
                phone = merchants_dict.get(item.get('merchant_id'), {}).get('phone_number', '918072130833')
                def track_lead(m_id, item_id):
                    try: supabase.table("analytics").insert({"merchant_id": m_id, "item_id": item_id}).execute()
                    except: pass
                    
                wa_url = f"https://wa.me/{str(phone).strip()}?text=Hi,%20I'm%20interested%20in%20{item.get('title')}"
                col_btn2.link_button("💬 WhatsApp", wa_url, use_container_width=True, on_click=track_lead, args=(item.get('merchant_id'), item.get('id')))
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        # Structured Empty State Frame
        st.markdown("""
            <div class="empty-state-box">
                <div style="font-size: 3rem; margin-bottom: 10px;">📦</div>
                <h3 style="color:#ffffff; margin-bottom: 5px;">No deals available in this area yet</h3>
                <p style="color:#94a3b8; font-size: 0.95rem;">Check back later or search for another term/category.</p>
            </div>
        """, unsafe_allow_html=True)

# 6. MERCHANT CONTROL PANEL
else:
    if not st.session_state.logged_in:
        st.markdown("<h2 style='color:#ffffff; font-weight:600;'>🏢 Merchant Login</h2>", unsafe_allow_html=True)
        col_l1, col_l2 = st.columns([1, 2])
        with col_l1:
            st.markdown("<p style='color:#94a3b8;'>Access store parameters to broadcast promotional items live.</p>", unsafe_allow_html=True)
            input_shop_id = st.text_input("Merchant Username", placeholder="e.g., shop_01")
            input_password = st.text_input("Portal Password", type="password")
            if st.button("Secure Portal Login", use_container_width=True, type="primary"):
                if input_shop_id.strip() in merchants_dict and merchants_dict[input_shop_id.strip()].get("password") == input_password.strip():
                    st.session_state.logged_in = True
                    st.session_state.merchant_id = input_shop_id.strip()
                    st.session_state.merchant_name = merchants_dict[input_shop_id.strip()].get("shop_name")
                    st.toast("Logged in successfully!", icon="🎉")
                    st.rerun()
                else: 
                    st.error("Access credentials invalid.")
    else:
        m_info = merchants_dict.get(st.session_state.merchant_id, {})
        m_logo = m_info.get("logo_url") if m_info.get("logo_url") else "https://cdn-icons-png.flaticon.com/512/606/606547.png"
        
        st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <h2 style="color:#ffffff; font-weight:700; margin-bottom:4px;">Welcome back, {st.session_state.merchant_name} 👋</h2>
                <p style="color:#94a3b8; font-size:0.95rem;">Manage today's deals and customer enquiries.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px; background-color: #1e293b; padding: 14px; border-radius: 10px; border:1px solid #334155; margin-bottom: 25px; width: fit-content;">
                <img src="{m_logo}" style="width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid #38bdf8;">
                <div>
                    <div style="color:#ffffff; font-weight:600; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
                        {st.session_state.merchant_name} 
                        <span style="background-color:#15803d; color:#ffffff; font-size:0.7rem; padding:2px 8px; border-radius:12px; font-weight:600;">Verified Merchant</span>
                    </div>
                    <div style="color:#94a3b8; font-size:0.8rem; margin-top:2px;">📍 North Authoor • 🟢 Session Active</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        op_menu = st.tabs(["📊 Analytics", "📥 Add Deal", "✏️ Edit Deals"])
        
        with op_menu[0]:
            my_items = [x for x in items if x.get('merchant_id') == st.session_state.merchant_id]
            my_clicks = len([a for a in analytics_data if a.get('merchant_id') == st.session_state.merchant_id])
            
            views_val = my_clicks * 4
            views_sub = "<div class='metric-trend'>↑ +12% vs yesterday</div>" if views_val > 0 else "<div class='metric-sub'>No visits today</div>"
            clicks_sub = "<div class='metric-trend'>↑ +8% conversion rate</div>" if my_clicks > 0 else "<div class='metric-sub'>Updated 5 mins ago</div>"
            
            # Analytics Cards with Clean Icons
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-val'>{views_val}</div>
                    <div class='metric-lbl'>👁️ Views Today</div>
                    {views_sub}
                </div>
            """, unsafe_allow_html=True)
            
            col_m2.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-val'>{len(my_items)}</div>
                    <div class='metric-lbl'>📦 Active Deals</div>
                    <div class='metric-trend'>🟢 All Listings Live</div>
                </div>
            """, unsafe_allow_html=True)
            
            col_m3.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-val'>{my_clicks}</div>
                    <div class='metric-lbl'>💬 WhatsApp Clicks</div>
                    {clicks_sub}
                </div>
            """, unsafe_allow_html=True)
            
            # Mini Analytics Activity Sparkline / Bar Chart
            st.markdown("<br><h4 style='color:#ffffff; font-size:1rem; font-weight:600;'>📈 Weekly Customer Interest</h4>", unsafe_allow_html=True)
            chart_df = pd.DataFrame({
                "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "Customer Clicks": [2, 5, 3, 8, max(my_clicks, 12), my_clicks + 4, my_clicks + 1]
            }).set_index("Day")
            st.bar_chart(chart_df, height=180, color="#38bdf8")
            
        with op_menu[1]:
            with st.form(key="add_item_form_new", clear_on_submit=True):
                col_inputs = st.columns(2)
                n_title = col_inputs[0].text_input("Product Title*")
                n_cat = col_inputs[1].selectbox("Category Field*", ["Electronics", "Fashion", "Grocery", "Home", "General"])
                n_price = col_inputs[0].number_input("Deal Value (₹)*", min_value=0, step=50)
                n_img = col_inputs[1].text_input("Upload Photo (Paste Link)", placeholder="https://images.unsplash.com/...")
                n_desc = st.text_area("Product Specifications / Deal Details*")
                n_loc = st.selectbox("Assign Distribution Hub Area Node*", ["North Authoor", "Central Bazar", "Tiruchendur Road", "Millerpuram"])
                
                if st.form_submit_button("🚀 Publish Deal", use_container_width=True):
                    if n_title.strip() and n_desc.strip() and n_price > 0:
                        coords = {"North Authoor": (8.8050, 78.1519), "Central Bazar": (8.8100, 78.1450), "Tiruchendur Road": (8.7950, 78.1600), "Millerpuram": (8.8020, 78.1320)}.get(n_loc, (8.8050, 78.1519))
                        supabase.table("items").insert({"title": n_title.strip(), "description": n_desc.strip(), "category": n_cat, "price": n_price, "location": n_loc, "image_url": n_img.strip(), "latitude": coords[0], "longitude": coords[1], "merchant_id": st.session_state.merchant_id}).execute()
                        st.toast("Deal published successfully!", icon="🚀")
                        st.rerun()

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
                        if col_actions[0].form_submit_button("💾 Save Changes", use_container_width=True):
                            supabase.table("items").update({"title": e_title.strip(), "price": e_price, "image_url": e_img.strip(), "description": e_desc.strip()}).eq("id", edit_select.get('id')).execute()
                            st.toast("Changes saved!", icon="💾")
                            st.rerun()
                        if col_actions[1].form_submit_button("🗑️ Remove Deal", use_container_width=True):
                            supabase.table("items").delete().eq("id", edit_select.get('id')).execute()
                            st.toast("Deal removed successfully!", icon="🗑️")
                            st.rerun()
            else:
                st.info("No active deals yet. Publish your first deal to reach nearby customers.")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Logout", type="primary"):
            st.session_state.logged_in = False
            st.session_state.merchant_id = None
            st.session_state.merchant_name = None
            st.toast("Logged out cleanly.", icon="🔒")
            st.rerun()
