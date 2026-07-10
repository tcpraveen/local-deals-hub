import os
import streamlit as st
from supabase import create_client, Client

# 1. Page Configuration & Styling
st.set_page_config(page_title="Neighborhood Deals Hub", layout="wide")

st.markdown("""
    <style>
    .report-link { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; text-decoration: none; }
    .badge { background-color: #262730; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; color: #fafafa; }
    </style>
""", unsafe_allow_html=True)

# Save the login status so it doesn't vanish on refresh
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

# 3. Sidebar – Shopkeeper Portal
with st.sidebar:
    st.markdown("# 🛍️ Shopkeeper Portal")
    
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

# 4. Main Header & Statistics Dashboard
st.markdown("# ⚡ Neighborhood Deals Hub")
st.caption("Your Local High-Contrast Trusted Marketplace Dashboard")

try:
    items_response = supabase.table("items").select("*").execute()
    items = items_response.data
except Exception as e:
    st.error(f"Database Error: {e}")
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

# 📥 NEW: MERCHANT FORM FOR UPDATING/ADDING ITEMS
if is_merchant:
    st.markdown("## 📥 Add New Item to Marketplace")
    with st.form(key="add_item_form", clear_on_submit=True):
        col_in1, col_in2, col_in3 = st.columns([2, 1, 1])
        with col_in1:
            new_title = st.text_input("Product Title*", placeholder="e.g., iPhone 15 Pro Max")
            new_desc = st.text_input("Description*", placeholder="Condition, details, etc...")
        with col_in2:
            new_cat = st.selectbox("Product Category*", ["Electronics", "General", "Vehicles", "Housing"])
        with col_in3:
            new_price = st.number_input("Price (₹)*", min_value=0, step=500, value=0)
            
        submit_new_item = st.form_submit_button("🚀 Deploy Listing to Marketplace", use_container_width=True)
        if submit_new_item:
            if new_title.strip() and new_desc.strip() and new_price > 0:
                try:
                    supabase.table("items").insert({
                        "title": new_title,
                        "description": new_desc,
                        "category": new_cat,
                        "price": new_price
                    }).execute()
                    st.success(f"Successfully listed '{new_title}'!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Failed to push entry: {err}")
            else:
                st.warning("Please fill out all fields.")
    st.markdown("---")

# 5. Search and Filter Controls
st.markdown("### 🔍 Filter Controls")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...")
with col_f2:
    category = st.selectbox("Filter by Category", ["All Categories", "General", "Electronics", "Vehicles", "Housing"])
with col_f3:
    max_budget = st.slider("Max Budget (₹)", min_value=0, max_value=300000, value=150000, step=5000)

# 6. Safe Filtering Logic
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
    
    if search_match and cat_match and price_match:
        filtered_items.append(i)

# 7. Grid Layout for Product Cards
if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"<span class='badge'>🏷️ {item.get('category', 'General')}</span> <span class='badge'>👤 Peer Listing</span>", unsafe_allow_html=True)
                st.markdown(f"### {item.get('title', 'No Title')}")
                st.markdown(f"**Price:** ₹{float(item.get('price', 0)):,.2f}")
                st.write(item.get('description', ''))
                st.markdown("<a class='report-link' href='#'>⚠️ Report Damaged/Fake</a>", unsafe_allow_html=True)
                
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
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Error saving review: {err}")
                            else:
                                st.warning("Please leave a comment text.")
                
                if reviews:
                    with st.expander("💬 View Recent Comments"):
                        for r in reviews[-2:]:
                            st.caption(f"{'⭐'*r['rating']} – \"{r['comment']}\"")
                
                # --- WhatsApp Action Link ---
                msg = f"Hi, I'm interested in buying your {item.get('title')} listed for ₹{item.get('price')}."
                whatsapp_url = f"https://wa.me/919999999999?text={msg.replace(' ', '%20')}"
                st.link_button("💬 Chat on WhatsApp", whatsapp_url, use_container_width=True)
                
                # --- MERCHANT DELETE ACTION ---
                if is_merchant:
                    st.markdown("---")
                    if st.button(f"🗑️ Delete Listing", key=f"del_{item_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("items").delete().eq("id", item_id).execute()
                            st.success("Listing removed!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error: {err}")
else:
    if items:
        st.info("No items match your filter settings.")
    else:
        st.info("Your marketplace inventory is currently empty.")
