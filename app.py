"""극장을 떠난 사람들은 OTT로 갔을까? — Streamlit 대시보드

실행: python -m streamlit run app.py
데이터: clean_data.py가 만든 data/processed/*.csv
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="극장을 떠난 사람들은 OTT로 갔을까?", page_icon="🎬", layout="wide")

HERE = Path(__file__).parent
BASE_YEAR = 2019  # 코로나 이전 기준 연도
AGES = ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"]
# 연령대마다 색을 하나씩 정해 두고, 모든 차트에서 같은 연령대는 같은 색으로 그린다.
COLORS = {"20대": "#2a78d6", "40대": "#eb6834", "60대": "#1baf7a", "30대": "#6250d6",
          "50대": "#eda100", "70대 이상": "#e34948", "10대": "#e87ba4"}


# ───────────── 1. 자료 읽기 ─────────────
@st.cache_data
def load_data():
    movie = pd.read_csv(HERE / "data" / "processed" / "movie.csv")
    ott = pd.read_csv(HERE / "data" / "processed" / "ott.csv")
    platform = pd.read_csv(HERE / "data" / "processed" / "platform.csv")
    return movie, ott, platform


movie, ott, platform = load_data()

# ───────────── 2. 위젯 ─────────────
ages = st.sidebar.multiselect("연령대", AGES, default=["20대", "40대", "60대"])
year = st.sidebar.selectbox("비교 연도 (2019년과 비교)", [2025, 2024, 2022, 2021, 2020])
metric_label = st.sidebar.selectbox("극장 지표", ["관람률(%)", "평균 관람 횟수(회)"])
metric = {"관람률(%)": "관람률", "평균 관람 횟수(회)": "평균관람횟수"}[metric_label]
plat_options = [p for p in platform["플랫폼"].unique() if p != "OTT 비이용"]
plat = st.sidebar.selectbox("OTT 플랫폼", plat_options, index=plat_options.index("넷플릭스"))

# ───────────── 3. 필터: 고른 연령대만 남기기 ─────────────
ORDER = {"연령대": [a for a in AGES if a in ages]}  # 고른 연령대만, 나이 순서로
movie_view = movie[movie["연령대"].isin(ages)]
ott_view = ott[ott["연령대"].isin(ages)]
plat_view = platform[(platform["연령대"].isin(ages)) & (platform["플랫폼"] == plat)]

st.title("🎬 극장을 떠난 사람들은 OTT로 갔을까?")
st.markdown("**질문**: 코로나 이후 극장에 돌아오지 않은 연령대는 OTT로 옮겨 갔을까?")

if movie_view.empty:
    st.warning("표시할 데이터가 없습니다. 연령대를 하나 이상 선택하세요.")
    st.stop()

# 연령대별 요약 표 (view): 아래의 카드, 막대, 산점도, 표가 모두 이 표를 쓴다.
before = movie_view[movie_view["연도"] == BASE_YEAR].set_index("연령대")[metric]
after = movie_view[movie_view["연도"] == year].set_index("연령대")[metric]
p2022 = plat_view[plat_view["연도"] == 2022].set_index("연령대")["이용률"]
p2025 = plat_view[plat_view["연도"] == 2025].set_index("연령대")["이용률"]
view = pd.DataFrame({
    f"2019년 {metric_label}": before,
    f"{year}년 {metric_label}": after,
    "극장 회복률(%)": (after / before * 100).round(1),
    f"{plat} 2022년(%)": p2022,
    f"{plat} 2025년(%)": p2025,
    f"{plat} 증가(%p)": (p2025 - p2022).round(1),
}).reindex([a for a in AGES if a in ages]).reset_index(names="연령대")

# ───────────── 4. 지표 카드 ─────────────
total_now = movie[(movie["연령대"] == "전체") & (movie["연도"] == year)][metric].iloc[0]
total_before = movie[(movie["연령대"] == "전체") & (movie["연도"] == BASE_YEAR)][metric].iloc[0]
low = view.loc[view["극장 회복률(%)"].idxmin()]
high = view.loc[view[f"{plat} 증가(%p)"].idxmax()]

if metric == "관람률":
    now_text, diff_text = f"{total_now:.1f}%", f"{total_now - total_before:+.1f}%p (2019년 대비)"
else:
    now_text, diff_text = f"{total_now:.2f}회", f"{total_now - total_before:+.2f}회 (2019년 대비)"

c1, c2, c3 = st.columns(3)
c1.metric(f"{year}년 전체 {metric_label}", now_text, diff_text)
c2.metric("극장이 가장 덜 회복된 연령대", f"{low['연령대']} ({low['극장 회복률(%)']:.0f}%)")
c3.metric(f"{plat} 이용이 가장 많이 늘어난 연령대", f"{high['연령대']} ({high[f'{plat} 증가(%p)']:+.1f}%p)")


# ───────────── 5. 차트 ─────────────
def style(fig):
    """모든 차트에 같은 글씨 크기와 범례 위치를 적용한다."""
    fig.update_layout(font=dict(size=15), legend_title_text="", height=420,
                      margin=dict(t=30, b=10))
    return fig


st.subheader(f"① 극장 영화 {metric_label}")
fig1 = px.line(movie_view, x="연도", y=metric, color="연령대", markers=True,
               color_discrete_map=COLORS, category_orders=ORDER,
               labels={metric: metric_label})
fig1.update_xaxes(dtick=1)
st.plotly_chart(style(fig1))
st.caption("2020·2021년은 코로나19 시기입니다. 2023년은 관람률을 조사하지 않아 비어 있습니다.")

st.subheader(f"② 2019년과 비교한 {year}년 극장 회복률")
fig2 = px.bar(view, x="연령대", y="극장 회복률(%)", color="연령대", text="극장 회복률(%)",
              color_discrete_map=COLORS, category_orders=ORDER)
fig2.add_hline(y=100, line_dash="dash", line_color="gray")  # 2019년 수준 = 100%
fig2.update_traces(textposition="outside")
fig2.update_layout(showlegend=False, yaxis_range=[0, 115])
st.plotly_chart(style(fig2))
st.caption(f"회복률 = {year}년 값 ÷ 2019년 값 × 100. 점선(100%)이 코로나 이전 수준입니다.")

st.subheader("③ OTT 이용률")
fig3 = px.line(ott_view, x="연도", y="OTT이용률", color="연령대", markers=True,
               color_discrete_map=COLORS, category_orders=ORDER,
               labels={"OTT이용률": "최근 3개월 OTT 이용률(%)"})
fig3.update_xaxes(dtick=1)
st.plotly_chart(style(fig3))
st.caption("한국미디어패널조사는 2021년부터 있습니다.")

st.subheader(f"④ 극장 회복률과 {plat} 이용 증가")
fig4 = px.scatter(view, x="극장 회복률(%)", y=f"{plat} 증가(%p)", color="연령대", text="연령대",
                  color_discrete_map=COLORS, category_orders=ORDER)
fig4.update_traces(marker_size=16, textposition="top center")
y = view[f"{plat} 증가(%p)"]
fig4.update_layout(showlegend=False, yaxis_range=[y.min() - 3, y.max() + 3])  # 이름표가 잘리지 않게 여유
st.plotly_chart(style(fig4))
st.caption(f"점 하나가 연령대 하나입니다. 왼쪽 위일수록 극장은 덜 돌아오고 {plat} 이용은 많이 늘어난 연령대입니다.")

# ───────────── 6. 표와 CSV 저장 ─────────────
st.subheader("선택한 연령대의 데이터")
st.dataframe(view, hide_index=True)
st.download_button("현재 선택 CSV 저장", data=view.to_csv(index=False).encode("utf-8-sig"),
                   file_name="selected_ages.csv", mime="text/csv")

# ───────────── 7. 결론과 한계 ─────────────
left, right = st.columns(2)
with left:
    st.subheader("결론")
    st.markdown(
        "- **20·30대**: 극장에는 돌아왔지만 가는 횟수가 절반 이하로 줄었다.\n"
        "- **40·50대**: 극장이 덜 회복됐고, 넷플릭스 이용이 가장 크게 늘었다.\n"
        "- **60대 이상**: 극장도 OTT 플랫폼도 적게 쓴다. 영화 관람 자체가 줄었다."
    )
with right:
    st.subheader("한계")
    st.markdown(
        "- 모두 설문조사라서 실제 관객 수가 아니다.\n"
        "- 함께 변했다는 것만 보여 주고, 인과관계는 증명하지 못한다.\n"
        "- OTT 자료는 2021년부터라 코로나 이전과 비교할 수 없다.\n"
        "- 조사마다 10대의 나이 구간과 조사 기간이 다르다."
    )

st.caption(
    "출처: 문화체육관광부 국민문화예술활동조사 "
    "([KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=113&tblId=DT_113_STBL_1026895)) · "
    "정보통신정책연구원 한국미디어패널조사 "
    "([KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=405&tblId=DT_405001_I095)) · "
    "한국방송광고진흥공사 OTT 이용 비율 "
    "([공공데이터포털](https://www.data.go.kr/data/15147384/fileData.do))"
)
