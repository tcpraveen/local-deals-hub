import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="Neighborhood Deals Hub",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI and clean card layout
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .deal-card {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .badge-clearance {
        background-color: #FEF2F2;
        color: #DC2626;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SAFE SUPABASE & SECRETS INITIALIZATION
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Safely check Streamlit secrets without throwing StreamlitSecretNotFoundError
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
# 3. HELPER & FALLBACK DATA FUNCTIONS
# ==========================================
def get_sample_deals():
    """Fallback sample data to keep site running smoothly when DB is disconnected"""
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
page = st.sidebar.radio("Navigate", ["Explore Nearby Deals", "Merchant Portal"])

# ==========================================
# PAGE 1: CONSUMER EXPLORE MARKETPLACE
# ==========================================
if page == "Explore Nearby Deals":
    st.markdown("<div class='main-header'>Neighborhood Deals Hub 📍</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Discover verified local store discounts and contact shopkeepers directly on WhatsApp.</div>", unsafe_allow_html=True)

    deals = fetch_deals()

    # Search & Category Filters
    col_search, col_cat = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search shop name or deal...", "")
    with col_cat:
        category_list = ["All", "Clothing", "Electronics", "Footwear", "Kirana/Grocery", "Other"]
        selected_cat = st.selectbox("Category", category_list)

    # Filter Logic
    filtered_deals = []
    for d in deals:
        matches_search = search_query.lower() in d['title'].lower() or search_query.lower() in d['shop_name'].lower()
        matches_cat = (selected_cat == "All") or (d.get('category') == selected_cat)
        if matches_search and matches_cat:
            filtered_deals.append(d)

    # MAP SECTION (FOLIUM)
    st.markdown("### 🗺️ Live Neighborhood Map")
    
    # Default Center Coordinates
    user_lat, user_lon = 8.8050, 78.1519
    m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # Blue Marker: User Location
    folium.Marker(
        location=[user_lat, user_lon],
        popup="<b>📍 You Are Here</b>",
        tooltip="Your Location",
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

    # Red Markers: Nearby Shops
    for deal in filtered_deals:
        s_lat = deal.get("lat") or deal.get("latitude")
        s_lon = deal.get("lon") or deal.get("longitude")
        
        if s_lat and s_lon:
            gmaps_link = f"https://www.google.com/maps/search/?api=1&query={s_lat},{s_lon}"
            popup_html = f"""
            <div style='font-family: sans-serif; width:160px;'>
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
    st.markdown(f"### 🏷️ Available Local Deals ({len(filtered_deals)})")

    # DEAL CARDS GRID
    if not filtered_deals:
        st.info("No deals found matching your search criteria.")
    else:
        cols = st.columns(3)
        for idx, deal in enumerate(filtered_deals):
            with cols[idx % 3]:
                st.markdown("<div class='deal-card'>", unsafe_allow_html=True)
                
                # Deal Image
                img_url = deal.get("image") or "https://via.placeholder.com/400x250?text=Local+Shop+Deal"
                st.image(img_url, use_container_width=True)
                
                # Deal Content
                if deal.get("is_clearance"):
                    st.markdown("<span class='badge-clearance'>🔥 Aadi / Off-Season Clearance</span>", unsafe_allow_html=True)
                
                st.markdown(f"#### {deal['title']}")
                st.markdown(f"🏪 **{deal['shop_name']}**")
                
                # Pricing
                orig_price = deal.get("original_price", 0)
                deal_price = deal.get("deal_price", 0)
                st.markdown(f"💰 ~~₹{orig_price:,}~~ **₹{deal_price:,}**")

                # Direct WhatsApp Link Button
                wa_num = str(deal.get("whatsapp", ""))
                msg = f"Hi {deal['shop_name']}, I saw your deal '{deal['title']}' on Neighborhood Deals Hub. Is this available today?"
                wa_url = f"https://wa.me/{wa_num}?text={msg.replace(' ', '%20')}"
                
                st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#25D366; color:white; text-align:center; padding:10px; border-radius:8px; font-weight:bold; margin-top:10px;">
                        💬 Chat on WhatsApp
                    </div>
                </a>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# PAGE 2: MERCHANT PORTAL (ADD DEALS)
# ==========================================
elif page == "Merchant Portal":
    st.markdown("<div class='main-header'>🏪 Merchant Portal</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Post a new deal for your local shop in 30 seconds with 0% commission.</div>", unsafe_allow_html=True)

    with st.form("add_deal_form", clear_on_submit=True):
        st.subheader("📝 Shop & Offer Details")
        
        c1, c2 = st.columns(2)
        with c1:
            shop_name = st.text_input("Store / Shop Name*", placeholder="e.g. Saravana Stores")
            category = st.selectbox("Category*", ["Clothing", "Electronics", "Footwear", "Kirana/Grocery", "Other"])
            whatsapp = st.text_input("WhatsApp Number (with country code)*", placeholder="919876543210")
        
        with c2:
            title = st.text_input("Offer Title*", placeholder="e.g. 30% Off Aadi Clearance Sale")
            original_price = st.number_input("Original Price (₹)", min_value=1, value=1000)
            deal_price = st.number_input("Discounted Deal Price (₹)", min_value=1, value=700)

        c3, c4 = st.columns(2)
        with c3:
            latitude = st.number_input("Shop Latitude Coordinates", value=8.8050, format="%.6f")
            longitude = st.number_input("Shop Longitude Coordinates", value=78.1519, format="%.6f")
        
        with c4:
            image_url = st.text_input("Product Image URL", placeholder="https://example.com/image.jpg")
            is_clearance = st.checkbox("Mark as Aadi / Off-Season Clearance Deal 🔥")

        submitted = st.form_submit_button("🚀 Publish Deal Live")

        if submitted:
            if not shop_name or not title or not whatsapp:
                st.error("Please fill in all required fields (*)")
            else:
                deal_payload = {
                    "shop_name": shop_name,
                    "title": title,
                    "category": category,
                    "whatsapp": whatsapp,
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
                        st.success(f"🎉 Success! '{title}' is now live on Neighborhood Deals Hub!")
                    except Exception as e:
                        st.error(f"Failed to post deal to database: {e}")
                else:
                    st.success("🎉 Deal submitted locally! (Connect Supabase to store long-term).")
