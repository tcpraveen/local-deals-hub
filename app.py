import folium
import streamlit as st
from streamlit_folium import st_folium

st.markdown("### 🗺️ Nearby Shop Locations & Your Position")

# 1. User/Center coordinates
user_lat = 8.8050   # Replace with your actual latitude or dynamic GPS
user_lon = 78.1519  # Replace with your actual longitude or dynamic GPS

# 2. Create interactive map
m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

# 3. Add User Marker (Blue Pin)
folium.Marker(
    location=[user_lat, user_lon],
    popup="<b>📍 You Are Here</b>",
    tooltip="Your Location",
    icon=folium.Icon(color="blue", icon="user", prefix="fa")
).add_to(m)

# 4. Add Shop Pins (Red Pins)
# Replace with your real shop data from Supabase/Database
sample_shops = [
    {"name": "Saravana Store", "lat": 8.8080, "lon": 78.1550, "deal": "30% Off Aadi Clearance"},
    {"name": "Raja Electronics", "lat": 8.8020, "lon": 78.1490, "deal": "Flat ₹1000 Off Smart TVs"}
]

for shop in sample_shops:
    maps_url = f"https://www.google.com/maps/search/?api=1&query={shop['lat']},{shop['lon']}"
    popup_html = f"""
    <div style='font-family: sans-serif; width: 160px;'>
        <b>{shop['name']}</b><br>
        <span>🏷️ {shop['deal']}</span><br><br>
        <a href='{maps_url}' target='_blank' style='background:#25D366; color:white; padding:4px 8px; border-radius:4px; text-decoration:none; font-size:11px;'>
            📍 Get Directions
        </a>
    </div>
    """
    folium.Marker(
        location=[shop["lat"], shop["lon"]],
        popup=folium.Popup(popup_html, max_width=200),
        tooltip=shop["name"],
        icon=folium.Icon(color="red", icon="shopping-cart", prefix="fa")
    ).add_to(m)

# 5. Render map in Streamlit
st_folium(m, use_container_width=True, height=400)
