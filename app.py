import os
import streamlit as st
from supabase import create_client, Client
# 2. Page Configuration & Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    .badge { background-color: #262730; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; color: #fafafa; }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Supabase Connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Fallback check if env variables aren't initialized yet
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error("Missing Supabase API keys in Render environment secrets.")
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# 4. Sidebar - Shopkeeper Portal
with st.sidebar:
    st.markdown("# 🔐 Shopkeeper Portal")
    st.write("Enter Merchant Pin to Unlock Management Tools")
    pin_input = st.text_input("Merchant PIN", type="password", label_visibility="collapsed")
    is_merchant = (pin_input == "123")
    
    if st.button("Login as Verified Merchant", use_container_width=True):
        if is_merchant:
            st.success("Welcome back, Verified Merchant!")
        else:
            st.error("Invalid PIN")

# 5. Main Header & Statistics Dashboard
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Your Local High-Contrast Trusted Marketplace Dashboard")

try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data
except Exception as e:
    items = []

col_stats1, col_stats2, col_stats3 = st.columns(3)
with col_stats1:
    st.metric("Total Active Listings", f"{len(items)} Items")
with col_stats2:
    total_circulation = sum([float(item.get('price', 0)) for item in items])
    st.metric("Total Marketplace Circulation", f"₹{total_circulation:,.2f}")
with col_stats3:
    st.metric("Merchant Mode Status", "Public Consumer View" if not is_merchant else "Admin Edit Mode")

st.markdown("---")

# 6. Search and Filter Controls
st.markdown("### 🔍 Filter Controls")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...")
with col_f2:
    category = st.selectbox("Filter by Category", ["All Categories", "General", "Electronics", "Vehicles", "Housing"])
with col_f3:
    max_budget = st.slider("Max Budget (₹)", min_value=0, max_value=300000, value=150000, step=5000)

# 7. Grid Layout for Product Cards
if items:
    filtered_items = [
        i for i in items 
        if (search_query.lower() in i.get('title', '').lower() or search_query.lower() in i.get('description', '').lower())
        and (float(i.get('price', 0)) <= max_budget)
    ]
    
    if filtered_items:
        cols = st.columns(3)
        for idx, item in enumerate(filtered_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"<span class='badge'>🏷️ {item.get('category', 'General')}</span> <span class='badge'>👤 Peer Listing</span>", unsafe_html=True)
                    st.markdown(f"### {item.get('title', 'No Title')}")
                    st.markdown(f"## Price: ₹{item.get('price', 0)}")
                    st.write(item.get('description', ''))
                    st.markdown("<a class='report-link' href='#'>⚠️ Report Damaged/Fake</a>", unsafe_html=True)
                    
                    # --- REVIEWS SYSTEM ---
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
                        st.markdown("*No ratings yet. Be the first to review!*")
                    
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
                                        st.success("Submitted! Refresh to update.")
                                    except Exception as err:
                                        st.error(f"Error saving review: {err}")
                                else:
                                    st.warning("Please leave a comment text.")
                                    
                    if reviews:
                        with st.expander("💬 View Recent Comments"):
                            for r in reviews[-2:]:
                                st.caption(f"{'⭐'*r['rating']} — \"{r['comment']}\"")
                    
                    # --- WhatsApp Action Link ---
                    msg = f"Hi, I'm interested in buying your {item.get('title')} listed for ₹{item.get('price')}."
                    whatsapp_url = f"https://wa.me/919999999999?text={msg.replace(' ', '%20')}"
                    st.link_button("💬 Chat on WhatsApp", whatsapp_url, use_container_width=True)
    else:
        st.info("No items match your filter settings.")
else:
    st.info("Your marketplace inventory is currently empty.")
