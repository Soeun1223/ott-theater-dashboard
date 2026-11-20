"""극장을 떠난 사람들은 OTT로 갔을까? — Streamlit 대시보드

실행: streamlit run app.py
데이터: clean_data.py가 만든 data/processed/*.csv
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data" / "processed"
BASE_YEAR = 2019  # 코로나 이전 기준 연도

AGES = ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"]
# 연령대를 세 그룹으로 묶어서 색으로 구분한다. 같은 그룹 안에서는 선 모양(실선/점선)으로 구분.
GROUP = {"10대": "10대", "20대": "청년층", "30대": "청년층", "40대": "중년층",
         "50대": "중년층", "60대": "고령층", "70대 이상": "고령층"}
COLOR = {"청년층": "#2a78d6", "중년층": "#eb6834", "고령층": "#1baf7a", "10대": "#8a8985"}
DASH = {"10대": "solid", "20대": "solid", "30대": "dot", "40대": "solid",
        "50대": "dot", "60대": "solid", "70대 이상": "dot"}

st.set_page_config(page_title="극장을 떠난 사람들은 OTT로 갔을까?", page_icon="🎬", layout="wide")


@st.cache_data
def load():
    movie = pd.read_csv(DATA / "movie.csv")
    ott = pd.read_csv(DATA / "ott.csv")
    platform = pd.read_csv(DATA / "platform.csv")
    return movie, ott, platform


movie, ott, platform = load()


def style(fig, y_title, height=380):
    """모든 차트에 같은 모양을 적용: 얇은 격자, 범례 위쪽, 마우스를 올리면 값 표시."""
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1.12, x=0, title=None),
        hovermode="x unified", font=dict(size=13),
    )
    fig.update_yaxes(title=y_title, gridcolor="rgba(128,128,128,0.2)", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def md(text):
    """Streamlit은 '~'를 취소선으로 바꿔서 '20~30대'가 깨진다. 그래서 '~' 앞에 \\를 붙인다."""
    st.markdown(text.replace("~", r"\~"))


def age_lines(fig, df, x, y, ages, unit):
    """연령대마다 선을 그리고, 마지막 점 옆에 연령대 이름을 직접 적는다.
    이름표끼리 겹치지 않도록 값이 가까우면 위아래로 벌려 놓는다."""
    ends = []
    for age in ages:
        d = df[df["연령대"] == age]
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], name=age, mode="lines+markers", connectgaps=False,
            line=dict(color=COLOR[GROUP[age]], width=2, dash=DASH[age]),
            marker=dict(size=8, line=dict(width=2, color="white")),
            hovertemplate=f"{age}: %{{y}}{unit}<extra></extra>",
        ))
        last = d.dropna(subset=[y]).iloc[-1]
        ends.append([age, last[x], last[y]])
    values = df[df["연령대"].isin(ages)][y]
    gap = (values.max() - values.min()) * 0.07  # 이름표 사이 최소 간격
    # 값이 위쪽에 몰려 있으면 아래로, 아래쪽에 몰려 있으면 위로 벌린다 (그래프 밖으로 나가지 않게)
    top_heavy = bool(sum(e[2] for e in ends) / len(ends) > (values.max() + values.min()) / 2)
    ends.sort(key=lambda e: e[2], reverse=top_heavy)
    label_y = []
    for _, _, v in ends:
        if not label_y:
            label_y.append(v)
        elif top_heavy:
            label_y.append(min(v, label_y[-1] - gap))
        else:
            label_y.append(max(v, label_y[-1] + gap))
    for (age, lx, v), ly in zip(ends, label_y):
        fig.add_annotation(x=lx, y=ly, text=age, showarrow=False,
                           xanchor="left", xshift=8, font=dict(size=12))


# ───────────────────────── 제목 ─────────────────────────
st.title("🎬 극장을 떠난 사람들은 OTT로 갔을까?")
md(
    "**질문**: 코로나 이후 극장에 누가 돌아오지 않았나? 그리고 그들은 OTT로 갔나?  \n"
    "**답**: 연령대마다 다르다. 20~30대는 극장에 돌아왔지만 덜 자주 가고, "
    "40~50대는 극장이 덜 회복된 만큼 OTT 이용이 크게 늘었고, "
    "60대 이상은 OTT가 아니라 영화 관람 자체가 줄었다."
)

# ───────────────────────── 조건 선택 위젯 ─────────────────────────
c1, c2, c3, c4 = st.columns([3, 1.3, 1.3, 1.5])
ages = c1.multiselect("연령대", AGES, default=["20대", "40대", "60대"])
year = c2.selectbox("비교 연도 (2019년과 비교)", [2025, 2024, 2022, 2021, 2020])
metric = c3.radio("극장 지표", ["관람률", "평균관람횟수"],
                  format_func=lambda m: "관람률(%)" if m == "관람률" else "평균 관람 횟수(회)")
platforms = sorted(platform["플랫폼"].unique(), key=lambda p: -platform.query("플랫폼 == @p")["이용률"].mean())
plat = c4.selectbox("OTT 플랫폼", [p for p in platforms if p != "OTT 비이용"],
                    index=[p for p in platforms if p != "OTT 비이용"].index("넷플릭스"))

if not ages:
    st.warning("연령대를 하나 이상 선택해 주세요.")
    st.stop()
ages = [a for a in AGES if a in ages]  # 항상 나이 순서대로
unit = "%" if metric == "관람률" else "회"

# ───────────────────────── 핵심 숫자 ─────────────────────────
def value(df, age, yr, col):
    s = df[(df["연령대"] == age) & (df["연도"] == yr)][col]
    return float(s.iloc[0]) if len(s) and pd.notna(s.iloc[0]) else None


now_rate, base_rate = value(movie, "전체", year, "관람률"), value(movie, "전체", BASE_YEAR, "관람률")
now_cnt, base_cnt = value(movie, "전체", year, "평균관람횟수"), value(movie, "전체", BASE_YEAR, "평균관람횟수")
now_ott = value(ott, "전체", year, "OTT이용률")

recovery = pd.DataFrame({
    "연령대": ages,
    "회복률": [round(value(movie, a, year, metric) / value(movie, a, BASE_YEAR, metric) * 100, 1) for a in ages],
})
lowest = recovery.loc[recovery["회복률"].idxmin()]

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"{year}년 극장 관람률 (전체)", f"{now_rate:.1f}%", f"{now_rate - base_rate:+.1f}%p (2019년 대비)")
k2.metric(f"{year}년 1인당 연평균 관람", f"{now_cnt:.2f}회", f"{now_cnt - base_cnt:+.2f}회 (2019년 대비)")
k3.metric(f"{year}년 OTT 이용률 (전체)", f"{now_ott:.1f}%" if now_ott else "자료 없음",
          help="한국미디어패널조사는 2021년부터 있습니다.")
k4.metric(f"가장 덜 회복된 연령대 ({'관람률' if metric == '관람률' else '관람 횟수'} 기준)",
          f"{lowest['연령대']} · {lowest['회복률']:.0f}%",
          help="선택한 연령대 중에서 2019년 대비 회복률이 가장 낮은 연령대입니다.")

st.divider()

# ───────────────────────── 차트 1, 2: 극장 ─────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("① 극장 영화 관람은 어떻게 변했나")
    fig = go.Figure()
    fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor="gray", opacity=0.1, line_width=0,
                  annotation_text="코로나19", annotation_position="top left")
    age_lines(fig, movie, "연도", metric, ages, unit)
    fig.add_annotation(x=2023, y=0, yref="paper", yanchor="bottom", showarrow=False,
                       text="2023년<br>미조사", font=dict(size=11, color="gray"))
    fig.update_xaxes(tickmode="array", tickvals=sorted(movie["연도"].unique()))
    st.plotly_chart(style(fig, "관람률(%)" if metric == "관람률" else "평균 관람 횟수(회)"))
    st.caption("관람률 = 지난 1년간 극장에서 영화를 1번 이상 본 사람의 비율. "
               "2023년은 관람자에게만 횟수를 물어 관람률을 계산할 수 없어 빈칸으로 두었습니다.")

with right:
    st.subheader(f"② 2019년 대비 {year}년 회복률")
    fig = go.Figure(go.Bar(
        x=recovery["연령대"], y=recovery["회복률"],
        marker=dict(color=[COLOR[GROUP[a]] for a in recovery["연령대"]], cornerradius=4,
                    line=dict(width=2, color="white")),
        text=[f"{v:.0f}%" for v in recovery["회복률"]], textposition="outside",
        hovertemplate="%{x}: 2019년의 %{y}%<extra></extra>",
    ))
    fig.add_hline(y=100, line_dash="dash", line_color="gray",
                  annotation_text="2019년 수준", annotation_position="top right")
    fig.update_yaxes(range=[0, 115])
    st.plotly_chart(style(fig, "2019년 = 100%").update_layout(hovermode="closest", bargap=0.45))
    st.caption(f"회복률 = {year}년 {metric.replace('평균관람횟수', '평균 관람 횟수')} ÷ 2019년 값 × 100. "
               "위의 '극장 지표'를 바꾸면 횟수 기준으로도 볼 수 있습니다.")

# ───────────────────────── 차트 3, 4: OTT ─────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("③ OTT 이용률은 어떻게 변했나")
    fig = go.Figure()
    age_lines(fig, ott, "연도", "OTT이용률", ages, "%")
    fig.update_xaxes(tickmode="array", tickvals=list(range(2021, 2026)))
    st.plotly_chart(style(fig, "최근 3개월 OTT 이용 경험(%)"))
    st.caption("출처: 한국미디어패널조사(KISDI). 2021년 이전 자료는 없습니다.")

with right:
    st.subheader(f"④ {plat} 이용률: 2022년 → 2025년")
    p = platform[(platform["플랫폼"] == plat) & platform["연령대"].isin(ages)]
    wide = p.pivot(index="연령대", columns="연도", values="이용률").reindex(ages)
    fig = go.Figure()
    for a, row in wide.iterrows():  # 연령대마다 2022년 점과 2025년 점을 선으로 잇는다
        fig.add_trace(go.Scatter(x=[row[2022], row[2025]], y=[a, a], mode="lines",
                                 line=dict(color=COLOR[GROUP[a]], width=2),
                                 showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=wide[2022], y=wide.index, mode="markers", name="2022년",
                             marker=dict(size=10, color="white", line=dict(width=2, color="gray")),
                             hovertemplate="%{y} 2022년: %{x}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=wide[2025], y=wide.index, mode="markers+text", name="2025년",
                             marker=dict(size=10, color=[COLOR[GROUP[a]] for a in wide.index],
                                         line=dict(width=2, color="white")),
                             text=[f"{v - o:+.1f}%p" for v, o in zip(wide[2025], wide[2022])],
                             textposition="middle right",
                             hovertemplate="%{y} 2025년: %{x}%<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, None).update_layout(hovermode="closest").update_xaxes(
        title="이용률(%)", showgrid=True, gridcolor="rgba(128,128,128,0.2)",
        range=[0, wide[[2022, 2025]].max().max() * 1.2]))
    st.caption("출처: 한국방송광고진흥공사. 빈 점 = 2022년, 색이 있는 점 = 2025년, 옆의 숫자 = 증가 폭.")

# ───────────────────────── 차트 5: 둘을 함께 ─────────────────────────
st.subheader(f"⑤ 극장이 덜 회복된 연령대일수록 {plat} 이용이 더 늘었나?")
p = platform[platform["플랫폼"] == plat].pivot(index="연령대", columns="연도", values="이용률")
both = pd.DataFrame({
    "연령대": ages,
    "극장 회복률": [value(movie, a, year, metric) / value(movie, a, BASE_YEAR, metric) * 100 for a in ages],
    "OTT 증가": [p.loc[a, 2025] - p.loc[a, 2022] for a in ages],
})
fig = go.Figure()
for g in ["10대", "청년층", "중년층", "고령층"]:
    d = both[both["연령대"].map(GROUP) == g]
    if d.empty:
        continue
    fig.add_trace(go.Scatter(
        x=d["극장 회복률"], y=d["OTT 증가"], mode="markers+text", name=g,
        text=d["연령대"], textposition="top center",
        marker=dict(size=14, color=COLOR[g], line=dict(width=2, color="white")),
        hovertemplate="%{text}<br>극장 회복률 %{x:.0f}%<br>" + plat + " 증가 %{y:+.1f}%p<extra></extra>",
    ))
fig.update_xaxes(title=f"극장 회복률 (2019 → {year}, %)", showgrid=True, gridcolor="rgba(128,128,128,0.2)")
st.plotly_chart(style(fig, f"{plat} 이용률 증가 (2022 → 2025, %p)", height=420).update_layout(hovermode="closest"))
st.caption("점 하나가 연령대 하나입니다. 왼쪽 위에 있을수록 '극장은 덜 돌아오고 OTT는 많이 늘어난' 연령대입니다. "
           "단, 연령대 단위의 비교라서 같은 사람이 극장 대신 OTT를 봤다는 뜻은 아닙니다.")

# ───────────────────────── 결론과 한계 ─────────────────────────
st.divider()
a, b = st.columns(2)
with a:
    st.subheader("결론")
    md(
        "- **20~30대**: 극장 관람률은 2019년의 80% 이상으로 돌아왔지만, 횟수는 절반 이하로 줄었다. "
        "OTT는 2021년에 이미 97% 이상이라 'OTT가 새로 생겨서'로는 설명하기 어렵다.\n"
        "- **40~50대**: 극장 관람률 회복이 60~70%에 그쳤고, 같은 기간 넷플릭스 이용률이 가장 크게 늘었다. "
        "OTT로 옮겨갔을 가능성이 가장 큰 연령대다.\n"
        "- **60대 이상**: 극장 회복률이 가장 낮지만 OTT 플랫폼 이용도 낮다. "
        "OTT로 옮겨간 것이 아니라 영화 관람 자체가 줄었다."
    )
with b:
    st.subheader("한계")
    md(
        "- 세 자료 모두 **설문조사**라서 실제 관객 수나 가입자 수가 아니다.\n"
        "- 같은 시기에 함께 변했다는 것만 보여줄 수 있고, **인과관계는 증명할 수 없다.**\n"
        "- OTT 자료는 2021년(미디어패널), 2022년(플랫폼)부터 있어서 코로나 이전과 비교할 수 없다.\n"
        "- 조사마다 10대 구간이 다르다(15~19세 / 만10~19세 / 13~19세). 결론은 20대 이상으로 냈다.\n"
        "- 영화 조사는 '지난 1년', OTT 조사는 '최근 3개월' 기준이다."
    )

with st.expander("📋 데이터 표와 출처 보기"):
    st.markdown("**극장 영화 관람** · 국민문화예술활동조사(문화체육관광부) · "
                "[KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=113&tblId=DT_113_STBL_1026895)")
    st.dataframe(movie[movie["연령대"].isin(ages + ["전체"])], hide_index=True)
    st.markdown("**OTT 이용 경험** · 한국미디어패널조사(정보통신정책연구원) · "
                "[KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=405&tblId=DT_405001_I095)")
    st.dataframe(ott[ott["연령대"].isin(ages + ["전체"])], hide_index=True)
    st.markdown("**OTT 플랫폼별 이용률** · 한국방송광고진흥공사 · "
                "[공공데이터포털](https://www.data.go.kr/data/15147384/fileData.do)")
    st.dataframe(platform[(platform["플랫폼"] == plat) & platform["연령대"].isin(ages)], hide_index=True)
