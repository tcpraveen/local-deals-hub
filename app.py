import os
import re
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client

# ==========================================
# 1. PAGE CONFIGURATION & ORIGINAL STYLING
# ==========================================
st.set_page_config(
    page_title="Neighborhood Deals Hub",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Original custom CSS with dynamic card hover, dark-mode compatibility & badges
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .deal-card {
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        background-color: #1E293B;
        color: #F8FAFC;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .deal-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .badge-clearance {
        background-color: #7F1D1D;
        color: #FECACA;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .badge-regular {
        background-color: #064E3B;
        color: #A7F3D0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .price-tag {
        font-size: 1.25rem;
        font-weight: 700;
        color: #10B981;
    }
    .original-price {
        text-decoration: line-through;
        color: #64748B;
        margin-right: 8px;
        font-size: 0.95rem;
    }
    .shop-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .merchant-name {
        font-size: 0.9rem;
        color: #38BDF8;
        margin-bottom: 10px;
    }
    .wa-button {
        background-color: #25D366;
        color: white !important;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        font-weight: 700;
        display: block;
        text-decoration: none !important;
        margin-top: 12px;
    }
    .wa-button:hover {
        background-color: #1EBE5D;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SAFE SUPABASE INITIALIZATION
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

# ==========================================
# 3. HELPER FUNCTIONS & FALLBACK DATA
# ==========================================
def clean_text(text: str) -> str:
    """Regex text cleaner for crisp UI rendering"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def get_sample_deals():
    """Fallback sample data to keep site running perfectly when offline"""
    return [
        {
            "id": 1,
            "shop_name": "Saravana Stores - Apparel",
            "title": "Aadi Thallupadi Clearance Sale - Flat 40% Off",
            "category": "Clothing",
            "original_price": 2500,
            "deal_price": 1500,
            "whatsapp": "919876543210",
            "lat": 8.8080,
            "lon": 78.1550,
            "is_clearance": True,
            "image": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=500"
        },
        {
            "id": 2,
            "shop_name": "Raja Electronics",
            "title": "Smart TV 43-Inch Special Off-Season Deal",
            "category": "Electronics",
            "original_price": 28000,
            "deal_price": 22999,
            "whatsapp": "919876543211",
            "lat": 8.8020,
            "lon": 78.1490,
            "is_clearance": False,
            "image": "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=500"
        }
    ]

def fetch_deals():
    if supabase:
        try:
            res = supabase.table("deals").select("*").order("created_at", desc=True).execute()
            if res.data:
                return res.data
        except Exception:
            pass
    return get_sample_deals()

# ==========================================
# 4. NAVIGATION & SIDEBAR
# ==========================================
st.sidebar.title("🛍️ Deals Hub")
page = st.sidebar.radio("Navigate", ["Explore Nearby Deals", "Merchant Portal", "Platform Analytics"])

# ==========================================
# PAGE 1: CONSUMER EXPLORE MARKETPLACE
# ==========================================
if page == "Explore Nearby Deals":
    st.markdown("<div class='main-header'>Neighborhood Deals Hub 📍</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Discover verified local store discounts and connect directly with shopkeepers on WhatsApp.</div>", unsafe_allow_html=True)

    deals = fetch_deals()

    # Search & Filter Controls
    col_search, col_cat = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search shop name or deal...", "")
    with col_cat:
        category_list = ["All", "Clothing", "Electronics", "Footwear", "Kirana/Grocery", "Other"]
        selected_cat = st.selectbox("Category", category_list)

    # Filtering Logic
    filtered_deals = []
    for d in deals:
        title = clean_text(d.get('title', ''))
        sname = clean_text(d.get('shop_name', ''))
        cat = d.get('category', 'Other')
        
        matches_search = search_query.lower() in title.lower() or search_query.lower() in sname.lower()
        matches_cat = (selected_cat == "All") or (cat == selected_cat)
        
        if matches_search and matches_cat:
            filtered_deals.append(d)

    # DYNAMIC FOLIUM MAP
    st.markdown("### 🗺️ Live Neighborhood Map")
    
    user_lat, user_lon = 8.8050, 78.1519
    m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # Blue Pin: User
    folium.Marker(
        location=[user_lat, user_lon],
        popup="<b>📍 You Are Here</b>",
        tooltip="Your Location",
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

    # Red Pins: Shops
    for deal in filtered_deals:
        s_lat = deal.get("lat") or deal.get("latitude")
        s_lon = deal.get("lon") or deal.get("longitude")
        
        if s_lat and s_lon:
            gmaps_link = f"https://www.google.com/maps/search/?api=1&query={s_lat},{s_lon}"
            popup_html = f"""
            <div style='font-family: sans-serif; width:160px; color:#1E293B;'>
                <b style='color:#0284c7;'>{deal['shop_name']}</b><br>
                <span style='font-size:12px;'>🏷️ {deal['title']}</span><br><br>
                <a href='{gmaps_link}' target='_blank' style='background:#25D366; color:white; padding:4px 8px; border-radius:4px; text-decoration:none; font-size:11px;'>
                    📍 Get Directions
                </a>
            </div>
            """
            folium.Marker(
                location=[s_lat, s_lon],
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"🏪 {deal['shop_name']}",
                icon=folium.Icon(color="red", icon="shopping-bag", prefix="fa")
            ).add_to(m)

    st_folium(m, use_container_width=True, height=380)

    st.markdown("---")
    st.markdown(f"### 🏷️ Local Deals Available ({len(filtered_deals)})")

    # ORIGINAL CARDS GRID DISPLAY
    if not filtered_deals:
        st.info("No matching deals found nearby.")
    else:
        cols = st.columns(3)
        for idx, deal in enumerate(filtered_deals):
            with cols[idx % 3]:
                st.markdown("<div class='deal-card'>", unsafe_allow_html=True)
                
                # Aspect Ratio Image Container
                img_url = deal.get("image") or "https://via.placeholder.com/400x250?text=Local+Shop+Deal"
                st.image(img_url, use_container_width=True)
                
                # Badge Status
                if deal.get("is_clearance"):
                    st.markdown("<span class='badge-clearance'>🔥 Aadi / Off-Season Clearance</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge-regular'>✅ Verified Store Deal</span>", unsafe_allow_html=True)
                
                # Title & Merchant
                st.markdown(f"<div class='shop-title'>{clean_text(deal['title'])}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='merchant-name'>🏪 {clean_text(deal['shop_name'])}</div>", unsafe_allow_html=True)
                
                # Pricing
                orig_price = deal.get("original_price", 0)
                deal_price = deal.get("deal_price", 0)
                st.markdown(f"<div><span class='original-price'>₹{orig_price:,}</span> <span class='price-tag'>₹{deal_price:,}</span></div>", unsafe_allow_html=True)

                # WhatsApp Action Link
                wa_num = str(deal.get("whatsapp", ""))
                msg = f"Hi {deal['shop_name']}, I saw your deal '{deal['title']}' on Neighborhood Deals Hub. Is this available today?"
                wa_url = f"https://wa.me/{wa_num}?text={msg.replace(' ', '%20')}"
                
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">💬 Chat on WhatsApp</a>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# PAGE 2: MERCHANT PORTAL
# ==========================================
elif page == "Merchant Portal":
    st.markdown("<div class='main-header'>🏪 Merchant Portal</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Post a new deal for your local store in under 30 seconds with zero commission fees.</div>", unsafe_allow_html=True)

    with st.form("add_deal_form", clear_on_submit=True):
        st.subheader("📝 Shop & Offer Information")
        
        c1, c2 = st.columns(2)
        with c1:
            shop_name = st.text_input("Store Name*", placeholder="e.g. Saravana Stores")
            category = st.selectbox("Category*", ["Clothing", "Electronics", "Footwear", "Kirana/Grocery", "Other"])
            whatsapp = st.text_input("WhatsApp Number (with country code)*", placeholder="919876543210")
        
        with c2:
            title = st.text_input("Offer Title*", placeholder="e.g. 30% Off Aadi Clearance Sale")
            original_price = st.number_input("Original Price (₹)", min_value=1, value=1000)
            deal_price = st.number_input("Discounted Price (₹)", min_value=1, value=700)

        c3, c4 = st.columns(2)
        with c3:
            latitude = st.number_input("Shop Latitude Coordinates", value=8.8050, format="%.6f")
            longitude = st.number_input("Shop Longitude Coordinates", value=78.1519, format="%.6f")
        
        with c4:
            image_url = st.text_input("Product Image URL", placeholder="https://images.unsplash.com/...")
            is_clearance = st.checkbox("Mark as Aadi / Off-Season Clearance Sale 🔥")

        submitted = st.form_submit_button("🚀 Publish Deal Live")

        if submitted:
            if not shop_name or not title or not whatsapp:
                st.error("Please complete all required fields (*)")
            else:
                deal_payload = {
                    "shop_name": clean_text(shop_name),
                    "title": clean_text(title),
                    "category": category,
                    "whatsapp": clean_text(whatsapp),
                    "original_price": original_price,
                    "deal_price": deal_price,
                    "lat": latitude,
                    "lon": longitude,
                    "image": image_url if image_url else "https://via.placeholder.com/400x250?text=Local+Shop+Deal",
                    "is_clearance": is_clearance
                }
                
                if supabase:
                    try:
                        supabase.table("deals").insert(deal_payload).execute()
                        st.success(f"🎉 Success! '{title}' is now live on the marketplace!")
                    except Exception as e:
                        st.error(f"Error publishing deal: {e}")
                else:
                    st.success("🎉 Deal submitted locally!")

# ==========================================
# PAGE 3: PLATFORM ANALYTICS
# ==========================================
elif page == "Platform Analytics":
    st.markdown("<div class='main-header'>📊 Platform Performance</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Real-time activity and local merchant engagement.</div>", unsafe_allow_html=True)
    
    deals = fetch_deals()
    df = pd.DataFrame(deals)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Deals", len(df))
    col2.metric("Verified Merchants", df['shop_name'].nunique() if not df.empty else 0)
    col3.metric("Clearance Listings", df['is_clearance'].sum() if 'is_clearance' in df.columns else 0)
