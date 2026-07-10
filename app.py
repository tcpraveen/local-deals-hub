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

# # 6. Search and Filter Controls
st.markdown("### 🔍 Filter Controls")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...")
with col_f2:
    category = st.select_box("Filter by Category", ["All Categories", "General", "Electronics", "Vehicles", "Housing"])
with col_f3:
    max_budget = st.slider("Max Budget (₹)", min_value=0, max_value=300000, value=150000, step=5000)

# # 7. Grid Layout for Product Cards
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

if filtered_items:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
