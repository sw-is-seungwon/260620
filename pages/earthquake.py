import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인 테마 적용 (소프트 지구 톤)
st.set_page_config(
    page_title="🌎 지구 탐사선: 판의 경계와 지진",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS로 부드러운 지구 느낌의 색감 지정 (너무 진한 색 지양)
st.markdown("""
    <style>
    /* 메인 배경색 및 폰트 설정 */
    .stApp {
        background-color: #f7f9fa;
    }
    /* 타이틀 및 헤더 색상 (소프트한 딥 블루) */
    h1, h2, h3 {
        color: #2c4a5e !important;
    }
    /* 안내 박스 스타일 (소프트 그린) */
    .stAlert {
        background-color: #f0f7f4 !important;
        color: #3b5a4a !important;
        border: 1px solid #d8ebd4 !important;
    }
    /* 사이드바 배경색 (연한 흙빛/베이지 톤) */
    [data-testid="stSidebar"] {
        background-color: #f1ede6 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌎 지구 탐사선: 판의 경계와 지진 분포 데이터")
st.markdown("""
실시간 지구 데이터(USGS)를 바탕으로 지진의 발생 위치를 확인하고, 
지구의 판의 경계와 지진 분포의 연관성을 알아봅시다.
""")

# 2. 사이드바 - 탐사 조건 설정
st.sidebar.header("🔍 탐사 조건 설정")
days = st.sidebar.slider("📅 조회할 최근 기간 (일)", min_value=1, max_value=30, value=7)
start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

min_magnitude = st.sidebar.slider("📐 최소 지진 규모 (Magnitude)", min_value=1.0, max_value=8.0, value=4.5, step=0.5)

# 3. USGS API 데이터 불러오기
@st.cache_data(ttl=1800)
def fetch_earthquake_data(start_time, min_mag):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {"format": "geojson", "starttime": start_time, "minmagnitude": min_mag}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

with st.spinner("🔄 실시간 지구 데이터 수집 중..."):
    geojson_data = fetch_earthquake_data(start_date, min_magnitude)

# 데이터프레임 변환
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
            "depth": geom["coordinates"][2]
        })

df = pd.DataFrame(eq_list)

# 4. 메인 화면 레이아웃 분할
if not df.empty:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🗺️ 실시간 지진 분포 지도")
        st.caption("💡 힌트: 지진 마커들이 거대한 선을 이루고 있나요? 그 선이 바로 '판의 경계'입니다.")
        
        # 지구 분위기에 맞춘 부드러운 지도 스타일 (CartoDB positron)
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
        
        # 소프트한 마커 색상 정의 (너무 튀지 않는 파스텔톤 계열)
        def get_color(depth):
            if depth < 70:
                return "#e07a5f" # 소프트 다홍 (천발)
            elif depth < 300:
                return "#f2cc8f" # 소프트 황토 (중발)
            else:
                return "#3d5a80" # 소프트 네이비 (심발)

        for _, row in df.iterrows():
            radius = row["mag"] * 2.5
            popup_text = f"<b>위치:</b> {row['place']}<br><b>규모:</b> M {row['mag']}<br><b>깊이:</b> {row['depth']} km"
            
            folium.CircleMarker(
                location=[row["lat"], row["lng"]],
                radius=radius,
                color=get_color(row["depth"]),
                fill=True,
                fill_color=get_color(row["depth"]),
                fill_opacity=0.6,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
            
        st_folium(m, width="100%", height=480, returned_objects=[])

    with col2:
        st.subheader("📊 데이터 통계")
        st.metric("총 발생 횟수", f"{len(df)} 건")
        st.metric("최대 규모 지진", f"M {df['mag'].max()}")
        
        st.markdown("---")
        st.markdown("**🎨 진원 깊이 범례**")
        st.markdown("🟤 **천발 지진** (0~70km)")
        st.markdown("🟡 **중발 지진** (70~300km)")
        st.markdown("🔵 **심발 지진** (300km+)")

# 5. 실시간 메모 기능 (초기 예시 추가)
st.markdown("---")
st.subheader("📝 조별 탐사 결과 메모장")
st.markdown("💡 지도를 보고 발견한 사실을 적어주세요. 작성 양식은 아래 우리 반 실시간 피드의 예시를 참고하면 됩니다!")

# 세션 상태 초기화 및 가이드용 초기 예시 데이터 주입
if "memo_storage" not in st.session_state:
    st.session_state["memo_storage"] = [
        {
            "timestamp": "10:00:15",
            "nickname": "📢 2조 탐험대장",
            "keyword": "태평양 불의 고리",
            "opinion": "일본 오른쪽 바다부터 칠레 앞바다까지 지진이 거대한 원 모양의 선을 그리며 발생하고 있어요! 이 라인이 태평양 판의 경계선이라는 것을 알 수 있었습니다."
        },
        {
            "timestamp": "10:02:40",
            "nickname": "📢 1조 지구지킴이",
            "keyword": "지진의 깊이 변화",
            "opinion": "일본 바다 쪽에는 갈색 점(천발)이 많은데, 일본 대륙 안쪽으로 들어올수록 점점 파란색 점(심발)이 찍히는 게 신기해요. 판이 비스듬하게 땅속으로 들어가면서 지진을 일으키나 봐요!"
        }
    ]

# 메모 입력 폼
with st.form(key="earth_memo_form", clear_on_submit=True):
    col_nick, col_key = st.columns([1, 2])
    with col_nick:
        nickname = st.text_input("👤 닉네임 (또는 모둠명)", placeholder="예: 3조, 지각변동팀")
    with col_key:
        keyword = st.text_input("🔑 핵심 키워드", placeholder="예: 판의 경계, 베니오프대")
        
    opinion = st.text_area("🧠 우리 조의 생각 정리", placeholder="지도를 보고 조원들과 토론한 핵심 내용을 한두 문장으로 정리해 적어주세요.")
    
    submit_btn = st.form_submit_button(label="🚀 메모 등록하기")

# 메모 등록 로직
if submit_btn:
    if not nickname.strip() or not opinion.strip():
        st.warning("⚠️ 닉네임과 의견을 모두 입력해 주세요!")
    else:
        new_memo = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "nickname": nickname,
            "keyword": keyword if keyword.strip() else "일반",
            "opinion": opinion
        }
        # 예시 데이터 바로 아래가 아닌, 무조건 맨 위에 최신글이 보이게 추가
        st.session_state["memo_storage"].insert(0, new_memo)
        st.success(f"🎉 {nickname}조의 의견이 등록되었습니다!")
        st.rerun()

# 6. 실시간 피드 출력
st.markdown("### 💬 우리 반 실시간 피드")

for memo in st.session_state["memo_storage"]:
    # 예시 메모와 학생들이 쓴 메모를 시각적으로 살짝 구분 (예시는 조금 다르게 표시)
    is_example = "[예시]" in memo["nickname"]
    with st.chat_message("assistant" if is_example else "user"):
        st.markdown(f"**{memo['nickname']}** | ⏱️ {memo['timestamp']} | 🏷️ *{memo['keyword']}*")
        st.write(memo['opinion'])
