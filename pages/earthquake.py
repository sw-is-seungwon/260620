import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="🌎 교육용 지진 탐사선 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌎 교육용 지진 탐사 데이터 시각화")
st.markdown("""
학생들이 전 세계 지진 데이터를 실시간으로 분석하며 **판 구조론(Plate Tectonics)**과 
**지진의 특성(규모, 깊이)**을 자기주도적으로 학습할 수 있는 공간입니다.
""")

# 2. 사이드바 - 교육용 필터 설정
st.sidebar.header("🔍 탐사 조건 설정")

# 기간 선택 (기본 최근 7일)
days = st.sidebar.slider("조회할 최근 기간 (일)", min_value=1, max_value=30, value=7)
start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

# 최소 규모 설정
min_magnitude = st.sidebar.slider("최소 지진 규모 (Magnitude)", min_value=1.0, max_value=8.0, value=4.5, step=0.5)

# 3. USGS API 데이터 불러오기
@st.cache_data(ttl=3600)  # 1시간 동안 캐싱하여 성능 최적화
def fetch_earthquake_data(start_time, min_mag):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_time,
        "minmagnitude": min_mag
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("USGS API로부터 데이터를 가져오지 못했습니다.")
        return None

with st.spinner("🔄 실시간 지구 데이터 수집 중..."):
    geojson_data = fetch_earthquake_data(start_date, min_magnitude)

# 4. 데이터프레임 변환 및 전처리
eq_list = []
if geojson_data and "features" in geojson_data:
    for feature in geojson_data["features"]:
        props = feature["properties"]
        geom = feature["geometry"]
        eq_list.append({
            "place": props["place"],
            "mag": props["mag"],
            "time": pd.to_datetime(props["time"], unit="ms"),
            "lng": geom["coordinates"][0],
            "lat": geom["coordinates"][1],
            "depth": geom["coordinates"][2] # km 단위 깊이
        })

df = pd.DataFrame(eq_list)

# 5. 메인 화면 레이아웃 분할
if not df.empty:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🗺️ 실시간 지진 분포 지도")
        st.caption("💡 힌트: 지진 마커들이 거대한 선을 이루고 있나요? 그 선이 바로 '판의 경계'입니다. 마커를 클릭해 깊이를 확인해보세요!")
        
        # 지도 생성 (전 세계를 보기 위해 중심을 [20, 0]으로 설정)
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
        
        # 깊이에 따른 색상 분류 함수 (천발, 중발, 심발 지진 교육용)
        def get_color(depth):
            if depth < 70:
                return "#ff4b4b" # 천발 지진 (적색)
            elif depth < 300:
                return "#ffa500" # 중발 지진 (주황색)
            else:
                return "#1f77b4" # 심발 지진 (청색)

        # 지도에 지진 마커 추가
        for _, row in df.iterrows():
            # 규모에 비례한 마커 크기 설정
            radius = row["mag"] * 2.5
            
            popup_text = f"""
            <b>위치:</b> {row['place']}<br>
            <b>규모:</b> M {row['mag']}<br>
            <b>깊이:</b> {row['depth']} km<br>
            <b>시간:</b> {row['time'].strftime('%Y-%m-%d %H:%M')}
            """
            
            folium.CircleMarker(
                location=[row["lat"], row["lng"]],
                radius=radius,
                color=get_color(row["depth"]),
                fill=True,
                fill_color=get_color(row["depth"]),
                fill_opacity=0.6,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
            
        # Streamlit에 지도 렌더링
        st_folium(m, width="100%", height=500, returned_objects=[])

    with col2:
        st.subheader("📊 데이터 통계 정보")
        st.metric("총 발생 횟수", f"{len(df)} 건")
        st.metric("최대 규모 지진", f"M {df['mag'].max()}")
        
        st.markdown("---")
        st.markdown("**🎨 지도 범례 (진원 깊이)**")
        st.markdown("🔴 **천발 지진** (0~70km)")
        st.markdown("🟠 **중발 지진** (70~300km)")
        st.markdown("🔵 **심발 지진** (300km+)")
        
        st.markdown("---")
        st.markdown("**📐 마커 크기**")
        st.caption("지진의 규모($M$)가 클수록 원의 크기가 커집니다.")

    # 하단 데이터 테이블 및 교육 퀴즈/토론 질문
    st.markdown("---")
    st.subheader("📋 탐사 데이터 테이블")
    st.dataframe(df[["time", "place", "mag", "depth"]].sort_values(by="mag", ascending=False), use_container_width=True)
    
    # 교육용 질문 섹션
    st.info("""
    ### 🧠 생각해보기 (조별 토론 과제)
    1. 지진이 많이 발생하는 지역은 주로 대륙의 중심부인가요, 아니면 바다와 대륙의 경계부인가요?
    2. '심발 지진(파란색)'은 주로 어느 지역에서 관찰되나요? 해구와 베니오프대 구조와 어떤 연관이 있을지 토론해봅시다.
    """)
else:
    st.warning("선택한 조건에 부합하는 지진 데이터가 없습니다. 필터를 조정해보세요.")
