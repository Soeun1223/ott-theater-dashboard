"""극장이 멈춘 사이, 유료 OTT는 누가 더 썼을까? — Streamlit 대시보드

실행: python -m streamlit run app.py
데이터: clean_data.py가 만든 data/processed/*.csv
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="극장이 멈춘 사이, 유료 OTT는?", page_icon="🎬", layout="wide")

HERE = Path(__file__).parent
START = 2022  # 두 자료가 모두 있는 첫해. 비교는 이 해부터 한다.
# 10대는 조사마다 나이 구간이 달라서(15~19세 / 13~19세) 넣지 않는다.
AGES = ["20대", "30대", "40대", "50대", "60대", "70대 이상"]
# 유료 구독형 OTT만. 유튜브 같은 무료·광고형은 뺐고, 왓챠·애플TV플러스는 이용률이 2% 안팎이라 뺐다.
PAID = ["넷플릭스", "쿠팡플레이", "티빙", "디즈니플러스", "웨이브"]
# 연령대마다 색을 하나씩 정해 두고, 모든 차트에서 같은 연령대는 같은 색으로 그린다.
COLORS = {"20대": "#2a78d6", "30대": "#eb6834", "40대": "#1baf7a",
          "50대": "#eda100", "60대": "#e87ba4", "70대 이상": "#008300"}


# ───────────── 1. 자료 읽기 ─────────────
@st.cache_data
def load_data():
    movie = pd.read_csv(HERE / "data" / "processed" / "movie.csv")
    platform = pd.read_csv(HERE / "data" / "processed" / "platform.csv")
    return movie, platform


movie, platform = load_data()

# ───────────── 2. 위젯 ─────────────
ages = st.sidebar.multiselect("연령대", AGES, default=AGES)
end = st.sidebar.selectbox(f"비교 기간 ({START}년부터)", [2025, 2024], format_func=lambda y: f"{START} → {y}년")
metric_label = st.sidebar.selectbox("극장 지표", ["관람률(%)", "평균 관람 횟수(회)"])
metric = {"관람률(%)": "관람률", "평균 관람 횟수(회)": "평균관람횟수"}[metric_label]
unit = "%p" if metric == "관람률" else "회"
subject = "관람률이" if metric == "관람률" else "관람 횟수가"  # 문장에 넣을 때 조사까지
plat = st.sidebar.selectbox("유료 OTT", PAID)

# ───────────── 3. 필터: 고른 연령대만 남기기 ─────────────
ORDER = {"연령대": [a for a in AGES if a in ages]}  # 고른 연령대만, 나이 순서로
movie_view = movie[movie["연령대"].isin(ages)]
plat_view = platform[(platform["연령대"].isin(ages)) & (platform["플랫폼"] == plat)]

st.title("🎬 극장이 멈춘 사이, 유료 OTT는 누가 더 썼을까?")
st.markdown(f"**질문**: 코로나 이후 극장 관객이 돌아오지 않는 동안, 유료 OTT는 어느 연령대에서 늘었나? "
            f"(두 자료가 모두 있는 {START}년부터 비교)")

if movie_view.empty:
    st.warning("표시할 데이터가 없습니다. 연령대를 하나 이상 선택하세요.")
    st.stop()

# 연령대별 요약 표 (view): 아래의 카드, 막대, 산점도, 표가 모두 이 표를 쓴다.
m_start = movie_view[movie_view["연도"] == START].set_index("연령대")[metric]
m_end = movie_view[movie_view["연도"] == end].set_index("연령대")[metric]
p_start = plat_view[plat_view["연도"] == START].set_index("연령대")["이용률"]
p_end = plat_view[plat_view["연도"] == end].set_index("연령대")["이용률"]
view = pd.DataFrame({
    f"극장 {START}년": m_start,
    f"극장 {end}년": m_end,
    f"극장 변화({unit})": (m_end - m_start).round(1 if metric == "관람률" else 2),
    f"{plat} {START}년(%)": p_start,
    f"{plat} {end}년(%)": p_end,
    f"{plat} 변화(%p)": (p_end - p_start).round(1),
}).reindex(ORDER["연령대"]).reset_index(names="연령대")
m_change, p_change = f"극장 변화({unit})", f"{plat} 변화(%p)"

# ───────────── 4. 지표 카드 ─────────────
total = movie[movie["연령대"] == "전체"].set_index("연도")[metric]
digits = 1 if metric == "관람률" else 2  # 관람률은 소수 첫째 자리, 횟수는 둘째 자리
value_fmt = f"{total[end]:.{digits}f}{'%' if metric == '관람률' else '회'}"
biggest = view.loc[view[m_change].abs().idxmax()]  # 늘었든 줄었든 가장 많이 변한 연령대
most_up = view.loc[view[p_change].idxmax()]

c1, c2, c3 = st.columns(3)
c1.metric(f"{end}년 전체 극장 {metric_label}", value_fmt,
          f"{total[end] - total[START]:+.{digits}f}{unit} ({START}년 대비)")
c2.metric(f"극장 {subject} 가장 많이 변한 연령대",
          f"{biggest['연령대']} ({biggest[m_change]:+.{digits}f}{unit})")
c3.metric(f"{plat} 이용이 가장 많이 늘어난 연령대", f"{most_up['연령대']} ({most_up[p_change]:+.1f}%p)")


# ───────────── 5. 차트 ─────────────
def style(fig):
    """모든 차트에 같은 글씨 크기와 범례 위치를 적용한다."""
    fig.update_layout(font=dict(size=15), legend_title_text="", height=420,
                      margin=dict(t=30, b=10))
    return fig


st.subheader(f"① 극장 영화 {metric_label}: 2019년 수준으로 돌아오지 못했다")
fig1 = px.line(movie_view, x="연도", y=metric, color="연령대", markers=True,
               color_discrete_map=COLORS, category_orders=ORDER,
               labels={metric: metric_label})
fig1.update_xaxes(dtick=1)
st.plotly_chart(style(fig1))
st.caption(f"2020·2021년은 코로나19 시기입니다. 2023년은 관람률을 조사하지 않아 비어 있습니다. "
           f"아래 ②~④는 {START}년부터의 변화만 비교합니다.")

st.subheader(f"② 극장 {metric_label} 변화: {START} → {end}년")
fig2 = px.bar(view, x="연령대", y=m_change, color="연령대", text=m_change,
              color_discrete_map=COLORS, category_orders=ORDER)
fig2.update_traces(textposition="outside")
fig2.update_layout(showlegend=False)
st.plotly_chart(style(fig2))
st.caption(f"0보다 크면 늘었고, 작으면 줄었습니다. 선택한 연령대 중 가장 크게 변한 곳은 "
           f"{biggest['연령대']}({biggest[m_change]:+.{digits}f}{unit})입니다.")

st.subheader(f"③ {plat} 이용률: {START} → 2025년")
fig3 = px.line(plat_view, x="연도", y="이용률", color="연령대", markers=True,
               color_discrete_map=COLORS, category_orders=ORDER,
               labels={"이용률": f"{plat} 이용률(%)"})
fig3.update_xaxes(dtick=1)
st.plotly_chart(style(fig3))
st.caption("출처: 한국방송광고진흥공사. 한 사람이 여러 OTT를 쓸 수 있어서 플랫폼별 이용률을 더하면 안 됩니다.")

st.subheader(f"④ 같은 기간의 극장 변화와 {plat} 이용 변화 ({START} → {end}년)")
fig4 = px.scatter(view, x=m_change, y=p_change, color="연령대", text="연령대",
                  color_discrete_map=COLORS, category_orders=ORDER)
fig4.update_traces(marker_size=16, textposition="top center")
y = view[p_change]
fig4.update_layout(showlegend=False, yaxis_range=[min(y.min(), 0) - 3, y.max() + 3])  # 이름표가 잘리지 않게 여유
st.plotly_chart(style(fig4))
st.caption(f"점 하나가 연령대 하나입니다. 위로 갈수록 {plat} 이용이 많이 늘었고, "
           f"오른쪽으로 갈수록 극장 {subject} 늘었습니다.")

# ───────────── 6. 표와 CSV 저장 ─────────────
st.subheader("선택한 연령대의 데이터")
st.dataframe(view, hide_index=True)
st.download_button("현재 선택 CSV 저장", data=view.to_csv(index=False).encode("utf-8-sig"),
                   file_name="selected_ages.csv", mime="text/csv")

# ───────────── 7. 결론과 한계 ─────────────
left, right = st.columns(2)
with left:
    st.subheader("결론 (2022 → 2025년 기준)")
    st.markdown(
        "- **극장**: 2022년 이후 모든 연령대에서 관람률 변화가 5%p 안쪽이다. "
        "전체 관람률은 2019년 77.0%에서 2025년 50.6%로, 코로나 이전 수준을 회복하지 못했다.\n"
        "- **유료 OTT**: 넷플릭스, 쿠팡플레이, 티빙, 디즈니플러스 모두 **40대**에서 가장 많이 늘었고, "
        "20~50대도 함께 늘었다. 60대 이상은 증가 폭이 가장 작았다(넷플릭스 60대 +7.4%p, 나머지는 2%p 미만). "
        "웨이브는 늘어난 연령대가 없다.\n"
        "- **정리**: 극장이 멈춘 사이 유료 OTT는 40대를 중심으로 커졌다. "
        "하지만 극장 관객이 OTT로 옮겨 갔다고는 이 자료로 말할 수 없다."
    )
with right:
    st.subheader("한계")
    st.markdown(
        "- 두 자료 모두 설문조사라서 실제 관객 수나 가입자 수가 아니다.\n"
        "- 극장이 크게 줄어든 2019~2022년의 유료 OTT 자료가 없다.\n"
        "- 극장은 2024년에 잠깐 늘었다가 2025년에 다시 줄었다. 끝 연도를 2024년으로 바꾸면 결과가 달라진다.\n"
        "- 같은 기간에 함께 변했다는 것만 보여 주고, 인과관계는 증명하지 못한다.\n"
        "- 여러 OTT를 함께 쓰는 사람이 있어 '유료 OTT 전체' 이용률은 만들 수 없다.\n"
        "- 두 조사는 기관과 질문이 달라서 값끼리 비교하지 않고 같은 기간의 변화량만 비교했다.\n"
        "- 2023년은 영화 관람률이 없고, OTT 자료도 수치가 출렁여 조사 방식이 바뀌었을 수 있다.\n"
        "- 10대는 조사마다 나이 구간이 달라 제외했다. 연령대별 표본은 1천여 명이라 몇 %p 차이는 우연일 수 있다."
    )

st.caption(
    "출처: 문화체육관광부 국민문화예술활동조사 '직접 관람횟수 - 영화' "
    "([KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=113&tblId=DT_113_STBL_1026895)) · "
    "한국방송광고진흥공사 '성별 연령별 OTT 서비스 이용 비율' "
    "([공공데이터포털](https://www.data.go.kr/data/15147384/fileData.do))"
)
