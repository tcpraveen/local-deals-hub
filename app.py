import os
import math
import streamlit as st
from supabase import create_client, Client
from streamlit_geolocation import streamlit_geolocation

# 1. Page Configuration & Professional UI Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    .badge { background-color: #1e1e24; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #00d2ff; font-weight: 600; margin-right: 5px; }
    .loc-badge { background-color: #2a2315; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #ffaa00; font-weight: 600; margin-right: 5px; }
    .dist-badge { background-color: #1b2a3a; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; color: #00ffcc; font-weight: 600; }
    
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
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 2. Initialize Supabase Connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Missing Supabase API keys in Render environment secrets.")
    st.stop()

# 🧮 HAVERSINE FORMULA: Calculates real-world distance between two GPS coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    R = 6371.0  # Earth radius in kilometers
    
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# 3. Sidebar – Shopkeeper Portal
with st.sidebar:
    st.markdown("## 🛍️ Shopkeeper Portal")
    if not st.session_state.logged_in:
        st.write("Enter Merchant Pin to Unlock Management Tools")
        pin_input = st.text_input("Merchant PIN", type="password", label_visibility="collapsed")
        if st.button("Login as Verified Merchant", use_container_width=True):
            if pin_input == "123":
                st.session_state.logged_in = True
                st.success("Welcome back, Verified Merchant!")
                st.rerun()
            else:
                st.error("Invalid PIN")
    else:
        st.success("🔒 Authenticated: Merchant Mode Active")
        if st.button("Log Out of Portal", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

is_merchant = st.session_state.logged_in

# 4. Main Header & Live Auto-Location Sensor
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Auto-Detecting Nearby Deals Safely and Privately")

# 📍 AUTOMATIC GPS DETECTOR (Asks browser for location permission seamlessly)
with st.container(border=True):
    st.markdown("📡 **Live Smart Radius Active:** Click the button below to automatically scan for deals closest to you.")
    location_data = streamlit_geolocation()
    
user_lat = location_data.get("latitude")
user_lon = location_data.get("longitude")

if user_lat and user_lon:
    st.success(f"📍 Location automatically locked: Coordinates ({user_lat:.4f}, {user_lon:.4f})")
else:
    st.info("💡 Pro-Tip: Grant browser location permission above to sort items automatically by closest walking distance!")

st.markdown("<br>", unsafe_allow_html=True)

try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    items = []

# 📥 MERCHANT FORM FOR ADDING ITEMS
if is_merchant:
    st.markdown("<div class='section-header'>📥 Add New Item to Marketplace</div>", unsafe_allow_html=True)
    with st.container(border=True):
        with st.form(key="add_item_form", clear_on_submit=True):
            col_in1, col_in2, col_in3 = st.columns([2, 1, 1])
            with col_in1:
                new_title = st.text_input("Product Title*", placeholder="e.g., iPhone 15 Pro Max")
            with col_in2:
                new_cat = st.selectbox("Product Category*", ["Electronics", "General", "Vehicles", "Housing"])
            with col_in3:
                new_price = st.number_input("Price (₹)*", min_value=0, step=500, value=0)
                
            col_in4, col_in5 = st.columns([2, 2])
            with col_in4:
                new_desc = st.text_input("Description*", placeholder="Condition, details, etc...")
            with col_in5:
                new_loc = st.text_input("City/Area Label*", placeholder="e.g., North Authoor, Chennai")
                
            # New Coordinate Fields for Merchants
            col_gps1, col_gps2 = st.columns(2)
            with col_gps1:
                item_lat_input = st.number_input("Item Latitude (Decimal)*", format="%.6f", value=13.0827, step=0.0001)
            with col_gps2:
                item_lon_input = st.number_input("Item Longitude (Decimal)*", format="%.6f", value=80.2707, step=0.0001)
                
            col_in6, col_in7 = st.columns([2, 2])
            with col_in6:
                new_image = st.text_input("Product Photo URL (Optional)", placeholder="https://example.com/image.jpg")
            with col_in7:
                new_payment = st.text_input("Payment Gateway URL (Optional)", placeholder="Stripe/Razorpay link...")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            submit_new_item = st.form_submit_button("🚀 Deploy Listing Live", use_container_width=True, type="primary")
            if submit_new_item:
                if new_title.strip() and new_desc.strip() and new_price > 0:
                    try:
                        payload = {
                            "title": new_title,
                            "description": new_desc,
                            "category": new_cat,
                            "price": new_price,
                            "location": new_loc,
                            "latitude": item_lat_input,
                            "longitude": item_lon_input
                        }
                        if new_image.strip():
                            payload["image_url"] = new_image.strip()
                        if new_payment.strip():
                            payload["payment_url"] = new_payment.strip()
                            
                        supabase.table("items").insert(payload).execute()
                        st.success(f"Successfully listed '{new_title}' online!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to push entry: {err}")
                else:
                    st.warning("Please fill out all required fields.")
    st.markdown("<br>", unsafe_allow_html=True)

# 5. Search and Filter Controls
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

# 6. Processing Distance Calculations & Filtering Logics
filtered_items = []
for i in items:
    search_match = (search_query.lower() in str(i.get('title', '')).lower() or 
                    search_query.lower() in str(i.get('description', '')).lower())
    
    cat_db = i.get('category')
    cat_match = (category == "All Categories" or (cat_db and category.lower() in str(cat_db).lower()))
    
    try:
        item_price = float(i.get('price', 0))
    except:
        item_price = 0
    price_match = (item_price <= max_budget)
    
    # Calculate live distance if user GPS is available
    i_lat = i.get('latitude')
    i_lon = i.get('longitude')
    computed_dist = calculate_distance(user_lat, user_lon, i_lat, i_lon)
    i['calculated_distance'] = computed_dist  # Store inside item dict temporarily
    
    if search_match and cat_match and price_match:
        filtered_items.append(i)

# 📊 AUTO-SORT BY DISTANCE: Closest items go to the top if user location is found!
if user_lat and user_lon:
    filtered_items.sort(key=lambda x: x['calculated_distance'] if x['calculated_distance'] is not None else float('inf'))

# 7. Grid Layout for Product Cards
if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 3]:
            with st.container(border=True):
                img_url = item.get('image_url') or item.get('photo_url')
                if not img_url:
                    img_url = "https://placehold.co/600x400/1a1c23/fafafa?text=No+Image+Provided"
                
                st.markdown(f"""
                    <div class='img-container'>
                        <img src='{img_url}' alt='Product Image'>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show Live Distance Badges dynamically
                dist_value = item.get('calculated_distance')
                dist_html = f"<span class='dist-badge'>⚡ {dist_value:.1f} km away</span>" if dist_value is not None else ""
                
                st.markdown(f"""
                    <div style='margin-bottom: 10px;'>
                        <span class='badge'>🏷️ {item.get('category', 'General')}</span>
                        <span class='loc-badge'>📍 {item.get('location', 'Local')}</span>
                        {dist_html}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"### {item.get('title', 'No Title')}")
                st.markdown(f"### **₹{float(item.get('price', 0)):,.2f}**")
                st.write(item.get('description', ''))
                
                item_id = item['id']
                try:
                    reviews_resp = supabase.table("feedback").select("*").eq("item_id", item_id).execute()
                    reviews = reviews_resp.data
                except Exception:
                    reviews = []
                
                if reviews:
                    avg_rating = sum([r['rating'] for r in reviews]) / len(reviews)
                    st.markdown(f"**Rating:** {'⭐' * int(round(avg_rating))} ({avg_rating:.1f}/5)")
                else:
                    st.markdown("*No ratings yet.*")
                
                if is_merchant:
                    st.markdown("---")
                    st.caption("🛠️ Management Actions")
                    if st.button(f"🗑️ Delete Listing", key=f"del_{item_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("items").delete().eq("id", item_id).execute()
                            st.success("Listing removed!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error: {err}")
                else:
                    st.markdown("<div style='margin-top: 10px; margin-bottom: 10px;'><a class='report-link' href='#'>⚠️ Report Damaged/Fake</a></div>", unsafe_allow_html=True)
                    
                    with st.expander("📝 Write a Customer Review"):
                        with st.form(key=f"review_{item_id}", clear_on_submit=True):
                            user_rating = st.selectbox("Select Stars", [5, 4, 3, 2, 1], key=f"s_{item_id}")
                            user_comment = st.text_input("Comment...", placeholder="e.g., Great condition!", key=f"c_{item_id}")
                            if st.form_submit_button("Submit Review"):
                                if user_comment.strip():
                                    try:
                                        supabase.table("feedback").insert({
                                            "item_id": item_id,
                                            "rating": user_rating,
                                            "comment": user_comment
                                        }).execute()
                                        st.success("Submitted!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error saving review: {err}")
                                else:
                                    st.warning("Please leave a comment text.")
                    
                    if reviews:
                        with st.expander("💬 View Recent Comments"):
                            for r in reviews[-2:]:
                                st.caption(f"{'⭐'*r['rating']} – \"{r['comment']}\"")
                    
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    pay_url = item.get('payment_url')
                    if pay_url:
                        st.link_button("💳 Instant Buy / Pay Now", pay_url, use_container_width=True, type="primary")
                    
                    msg = f"Hi, I'm interested in buying your {item.get('title')} listed for ₹{item.get('price')}."
                    whatsapp_url = f"https://wa.me/919999999999?text={msg.replace(' ', '%20')}"
                    st.link_button("💬 Chat on WhatsApp", whatsapp_url, use_container_width=True)
else:
    st.info("No items match your filter settings.")
