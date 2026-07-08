import os
import subprocess
import sys

# Automatically force-install supabase if Render misses it
try:
    from supabase import create_client, Client
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client, Client

import streamlit as st


# 1. DATABASE CONNECTION
# Automatically connects using your existing Render environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Page configuration
st.set_page_config(page_title="Neighborhood Deals Hub", page_icon="⚡", layout="wide")

# 2. SIDEBAR - SHOPKEEPER PORTAL
with st.sidebar:
    st.markdown("## 🔐 Shopkeeper Portal")
    st.caption("Enter Merchant Pin to Unlock Management Tools")
    merchant_pin = st.text_input("Merchant PIN", type="password", label_visibility="collapsed")
    is_merchant = (merchant_pin == "123")  # Replace with your test PIN if different
    
    if is_merchant:
        st.success("✨ Logged in as Verified Merchant")
        st.markdown("---")
        st.markdown("### ➕ Add New Item Listing")
        with st.form("add_item_form", clear_on_submit=True):
            new_title = st.text_input("Item Title")
            new_price = st.number_input("Price (₹)", min_value=0, step=1)
            new_desc = st.text_area("Description")
            new_cat = st.selectbox("Category", ["Electronics", "Vehicles", "Furniture", "Books", "Other"])
            submit_item = st.form_submit_button("Post Listing")
            
            if submit_item and new_title:
                item_data = {"title": new_title, "price": new_price, "description": new_desc, "category": new_cat}
                supabase.table("items").insert(item_data).execute()
                st.success("Listing posted successfully!")
                st.rerun()
    else:
        st.info("Browsing as a local shopper. Enter pin to unlock posting privileges.")

# 3. MAIN DASHBOARD HEADER
st.title("⚡ Neighborhood Deals Hub")
st.caption("Your Local High-Contrast Trusted Marketplace Dashboard")

# Fetch all items from Supabase
items_response = supabase.table("items").select("*").execute()
all_items = items_response.data if items_response.data else []

# 4. FILTER CONTROLS
st.markdown("### 🔍 Filter Controls")
col_search, col_cat, col_budget = st.columns([2, 1, 1])

with col_search:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...")
with col_cat:
    categories = ["All Categories"] + list(set([item["category"] for item in all_items if "category" in item]))
    selected_cat = st.selectbox("Filter by Category", categories)
with col_budget:
    max_budget = st.slider("Max Budget (₹)", min_value=0, max_value=200000, value=150000, step=5000)

# Apply filter logic
filtered_items = []
for item in all_items:
    matches_search = search_query.lower() in item.get("title", "").lower() or search_query.lower() in item.get("description", "").lower()
    matches_cat = selected_cat == "All Categories" or item.get("category") == selected_cat
    matches_budget = item.get("price", 0) <= max_budget
    
    if matches_search and matches_cat and matches_budget:
        filtered_items.append(item)

# 5. DYNAMIC HUB STATISTICS
st.markdown("### 📊 Hub Statistics")
stat_col1, stat_col2, stat_col3 = st.columns(3)
with stat_col1:
    st.metric("Total Active Listings", f"{len(filtered_items)} Items")
with stat_col2:
    total_circulation = sum([item.get("price", 0) for item in filtered_items])
    st.metric("Total Marketplace Circulation", f"₹{total_circulation:,.2f}")
with stat_col3:
    st.metric("Merchant Mode Status", "Merchant Mode Unlocked" if is_merchant else "Public Consumer View")

st.markdown("---")

# 6. PRODUCT GRID SYSTEM
if not filtered_items:
    st.info("No listings found matching your filters.")
else:
    # Render items in a structured row/column grid layout
    cols_per_row = 3
    for i in range(0, len(filtered_items), cols_per_row):
        row_items = filtered_items[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        
        for idx, item in enumerate(row_items):
            with cols[idx]:
                with st.container(border=True):
                    # Category badges
                    st.caption(f"📁 {item.get('category', 'General')}")
                    
                    # Product Core Info
                    st.markdown(f"### {item.get('title')}")
                    st.markdown(f"#### Price: ₹{item.get('price')}")
                    st.write(item.get('description', 'No description provided.'))
                    
                    st.markdown("---")
                    
                    # --- NEW INTEGRATED FEATURE: RATINGS & REVIEWS SYSTEM ---
                    item_id = item['id']
                    
                    # Fetch comments from Supabase 'feedback' table
                    try:
                        reviews_res = supabase.table("feedback").select("*").eq("item_id", item_id).execute()
                        reviews = reviews_res.data if reviews_res.data else []
                    except Exception:
                        reviews = []
                    
                    # Render Star System Math
                    if reviews:
                        avg_rating = sum([r['rating'] for r in reviews]) / len(reviews)
                        stars_display = "⭐" * int(round(avg_rating))
                        st.markdown(f"**Rating:** {stars_display} ({avg_rating:.1f}/5 — {len(reviews)} reviews)")
                    else:
                        st.markdown("*ℹ️ No ratings yet. Be the first to review!*")
                    
                    # Dropdown form to type a new review
                    with st.expander("📝 Write a Customer Review"):
                        with st.form(key=f"rev_form_{item_id}", clear_on_submit=True):
                            u_rating = st.selectbox("Select Stars", [5, 4, 3, 2, 1], key=f"s_{item_id}")
                            u_comment = st.text_input("Your comment...", placeholder="Excellent condition!", key=f"c_{item_id}")
                            submit_rev = st.form_submit_button("Submit Review")
                            
                            if submit_rev:
                                if not u_comment.strip():
                                    st.warning("Please enter a review message.")
                                else:
                                    rev_payload = {"item_id": item_id, "rating": u_rating, "comment": u_comment}
                                    supabase.table("feedback").insert(rev_payload).execute()
                                    st.success("Review recorded! Please refresh.")
                                    st.rerun()
                    
                    # Show recent comments left by others
                    if reviews:
                        with st.expander("💬 View Recent Comments"):
                            for r in reviews[-3:]:
                                st.caption(f"{'⭐' * r['rating']} — \"{r['comment']}\"")
                    
                    # --- ACTIONS ---
                    st.markdown("⚠️ [Report Damaged/Fake](#)")
                    
                    # Formatted WhatsApp Chat Button Link
                    encoded_msg = f"Hello! I am interested in buying your listing: {item.get('title')} for ₹{item.get('price')}."
                    whatsapp_url = f"https://wa.me/919876543210?text={encoded_msg.replace(' ', '%20')}"
                    st.link_button("💬 Chat on WhatsApp", whatsapp_url, use_container_width=True)
                    
                    # Merchant action tool
                    if is_merchant:
                        if st.button("❌ Delete Listing", key=f"del_{item_id}", use_container_width=True):
                            supabase.table("items").delete().eq("id", item_id).execute()
                            st.success("Listing deleted.")
                            st.rerun()
