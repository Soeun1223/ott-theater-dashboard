"""원본 CSV 3개(data/raw)를 정리해서 data/processed에 저장한다.

실행: python clean_data.py

정리 내용
- 원본은 CP949 인코딩 → UTF-8로 저장
- 세 조사의 연령 구간 이름을 하나로 통일 (10대, 20대, ..., 70대 이상)
- KOSIS 표는 '연도 × 항목'이 가로로 펼쳐져 있어서 세로(긴 형태)로 바꿈
"""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

AGE_ORDER = ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"]


def clean_movie() -> pd.DataFrame:
    """국민문화예술활동조사: 연령대별 극장 영화 관람률과 평균 관람 횟수."""
    raw = pd.read_csv(RAW / "kosis_movie_attendance.csv", encoding="cp949", header=[0, 1])
    rows = []
    for _, r in raw.iterrows():
        group, label = str(r.iloc[0]).strip(), str(r.iloc[1]).strip()
        for (year, item), value in zip(raw.columns[2:], r.iloc[2:]):
            rows.append((group, label, int(str(year)[:4]), item.strip(), value))
    long = pd.DataFrame(rows, columns=["group", "label", "year", "item", "value"])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")  # '-'는 빈 값

    long = long[long["group"].isin(["전체", "연령별"])]
    wide = long.pivot_table(index=["label", "year"], columns="item", values="value").reset_index()

    # 관람률 = '경험 있음'(2024~) 또는 100 - '관람 경험 없음'(~2022).
    # 2023년은 관람자에게만 횟수를 물어서 관람률을 계산할 수 없음 → 빈 값으로 둠.
    rate = wide.get("경험 있음")
    wide["관람률"] = rate.where(rate.notna(), 100 - wide["관람 경험 없음"]).round(1)
    wide["평균관람횟수"] = wide["전체평균"]

    age_map = {"소계": "전체", "15~19세": "10대", "70세이상": "70대 이상"}
    wide["연령대"] = wide["label"].replace(age_map)
    out = wide[["연령대", "year", "관람률", "평균관람횟수", "표본수"]].rename(columns={"year": "연도"})
    return out.sort_values(["연령대", "연도"]).reset_index(drop=True)


def clean_ott() -> pd.DataFrame:
    """한국미디어패널조사: 연령대별 최근 3개월 OTT 이용 경험률."""
    raw = pd.read_csv(RAW / "kosis_ott_experience.csv", encoding="cp949", header=[0, 1])
    raw = raw[raw.iloc[:, 0].str.strip().isin(["전체", "연령"])]
    age_map = {
        "소계": "전체", "만10-19세": "10대", "만20-29세": "20대", "만30-39세": "30대",
        "만40-49세": "40대", "만50-59세": "50대", "만60-69세": "60대", "만70세이상": "70대 이상",
    }
    rows = []
    for _, r in raw.iterrows():
        label = str(r.iloc[1]).strip()
        if label not in age_map:  # 만10대미만은 다른 조사와 비교할 수 없어서 제외
            continue
        for year in range(2021, 2026):
            rows.append((age_map[label], year, float(r[(str(year), "이용경험 있음 (%)")])))
    return pd.DataFrame(rows, columns=["연령대", "연도", "OTT이용률"])


def clean_platform() -> pd.DataFrame:
    """한국방송광고진흥공사: 연령대별 OTT 플랫폼 이용률 (긴 형태)."""
    raw = pd.read_csv(RAW / "ott_platform_kobaco.csv", encoding="cp949")
    raw["구분1"] = raw["구분1"].str.strip()
    raw["구분2"] = raw["구분2"].str.strip()  # '60대 '처럼 뒤에 공백이 붙은 값이 있음
    raw = raw[raw["구분1"] == "연령별"].copy()
    raw["연령대"] = raw["구분2"].replace({"13-19세": "10대"})
    platforms = [c for c in raw.columns if c not in ("연도", "구분1", "구분2", "사례수", "연령대")]
    long = raw.melt(id_vars=["연령대", "연도"], value_vars=platforms, var_name="플랫폼", value_name="이용률")
    return long.reset_index(drop=True)


if __name__ == "__main__":
    for name, df in [("movie", clean_movie()), ("ott", clean_ott()), ("platform", clean_platform())]:
        unknown = set(df["연령대"]) - set(AGE_ORDER) - {"전체"}
        assert not unknown, f"{name}: 연령대 이름이 통일되지 않음 {unknown}"
        df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name}.csv: {len(df)}행")
