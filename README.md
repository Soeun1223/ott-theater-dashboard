# 🎬 극장을 떠난 사람들은 OTT로 갔을까?

2026학년도 2학기 산업데이터시각화 개인 프로젝트

**질문**: 코로나 이후 극장에 누가 돌아오지 않았나? 그리고 그들은 OTT로 갔나?

- 배포 URL: (배포 후 추가)

## 데이터

| 데이터 | 출처 | 기간 |
|---|---|---|
| 직접 관람횟수 - 영화 | 문화체육관광부 국민문화예술활동조사, [KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=113&tblId=DT_113_STBL_1026895) | 2014, 2016, 2018~2025 |
| 최근 3개월 OTT서비스 이용 경험여부 | 정보통신정책연구원 한국미디어패널조사, [KOSIS](https://kosis.kr/statHtml/statHtml.do?orgId=405&tblId=DT_405001_I095) | 2021~2025 |
| 성별 연령별 OTT 서비스 이용 비율 | 한국방송광고진흥공사, [공공데이터포털](https://www.data.go.kr/data/15147384/fileData.do) | 2022~2025 |

자세한 집계 기준과 주의점은 [데이터_출처.md](데이터_출처.md)에 있습니다.

## 파일 구성

```
app.py            대시보드 (Streamlit)
clean_data.py     원본 CSV → 정리된 CSV
data/raw/         다운로드한 원본 (CP949)
data/processed/   정리된 데이터 (UTF-8, 대시보드가 읽는 파일)
requirements.txt  배포용 패키지 목록
```

## 실행 방법

```bash
pip install -r requirements.txt
python clean_data.py   # data/processed가 없을 때만
streamlit run app.py
```
