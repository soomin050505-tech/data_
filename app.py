# ===== 라이브러리 불러오기 =====
import pandas as pd
import streamlit as st
import plotly.express as px


# ===== 페이지 설정 (가장 먼저 실행되는 st 명령) =====
st.set_page_config(page_title="Titanic 대시보드", layout="wide")


# ===== 데이터 읽기 (한 번만 읽고 저장해 두기) =====
@st.cache_data
def load_data():
    # titanic.csv를 읽어서 반환하기
    return pd.read_csv("titanic.csv")


# ===== 필터 함수 =====
def filter_data(df, sexes, classes, age_range):
    # 나이 범위를 최소값, 최대값으로 나누기
    age_min, age_max = age_range

    # [수정] 슬라이더가 전체 범위(0~80)면 나이 조건을 걸지 않기 (나이 결측 승객도 포함)
    if (age_min, age_max) == (0, 80):
        age_ok = pd.Series(True, index=df.index)
    # [수정] 범위를 좁혔다면 그 범위 안의 승객만 고르기 (나이 결측 승객은 제외)
    else:
        age_ok = df["age"].between(age_min, age_max)

    # 세 조건(성별, 객실 등급, 나이)을 모두 만족하는 행만 고르기
    result = df[
        (df["sex"].isin(sexes))
        & (df["pclass"].isin(classes))
        & age_ok  # [수정] 위에서 만든 나이 조건 사용하기
    ]

    # 필터링된 데이터 반환하기
    return result


# ===== KPI 함수 =====
def kpi(df):
    # 데이터가 비어 있으면 (0, 0, 0) 반환하기
    if len(df) == 0:
        return (0, 0, 0)

    # 승객 수 구하기
    total = len(df)

    # 생존율(%) 구하기
    survival_rate = round(df["survived"].mean() * 100, 1)

    # 평균 나이 구하기 (결측치는 자동 제외)
    avg_age = round(df["age"].mean(), 1)

    # 세 값을 한꺼번에 반환하기
    return (total, survival_rate, avg_age)


# ===== 그래프 함수 =====
def class_rate_bar(df):
    # 객실 등급별 생존율(%) 계산하기
    rate = df.groupby("pclass")["survived"].mean().mul(100).round(1).reset_index()
    rate.columns = ["pclass", "survival_rate"]

    # 객실 등급을 문자로 바꿔서 x축을 깔끔하게 만들기
    rate["pclass"] = rate["pclass"].astype(str) + "등급"

    # 막대그래프 만들기 (막대 위에 값 표시)
    fig = px.bar(
        rate,
        x="pclass",
        y="survival_rate",
        text_auto=True,
        title="객실 등급별 생존율(%)",
        labels={"pclass": "객실 등급", "survival_rate": "생존율(%)"},
    )
    return fig


def age_hist(df):
    # 생존 여부(0/1)를 한글로 바꾼 복사본 만들기
    temp = df.copy()
    temp["생존여부"] = temp["survived"].map({0: "사망", 1: "생존"})

    # 히스토그램 만들기 (겹쳐 보기 + 투명도 0.6)
    fig = px.histogram(
        temp,
        x="age",
        color="생존여부",
        barmode="overlay",
        opacity=0.6,
        title="생존 여부별 승객 나이 분포",
        labels={"age": "나이"},
    )
    return fig


# ===== 페이지 제목 =====
st.title("타이타닉, 누가 살아남았나?")


# ===== 데이터 불러오기 =====
df = load_data()


# ===== 사이드바 필터 =====
st.sidebar.header("필터")

# 성별 선택 (기본값: 모두 선택)
sexes = st.sidebar.multiselect(
    "성별", options=["male", "female"], default=["male", "female"]
)

# 객실 등급 선택 (기본값: 모두 선택)
classes = st.sidebar.multiselect(
    "객실 등급", options=[1, 2, 3], default=[1, 2, 3]
)

# 나이 범위 선택 (0~80세, 기본값은 전체 범위)
age_range = st.sidebar.slider("나이 범위", 0, 80, (0, 80))


# ===== 입력 확인 =====
# [수정] 성별이나 객실 등급을 하나도 고르지 않았는지 확인하기
if len(sexes) == 0 or len(classes) == 0:
    # [수정] 안내 문구를 보여주고
    st.warning("성별과 객실 등급을 각각 하나 이상 선택해 주세요.")
    # [수정] 아래 코드는 실행하지 않고 멈추기
    st.stop()


# ===== 본문 =====
# 필터 조건에 맞는 승객만 골라내기
filtered = filter_data(df, sexes, classes, age_range)

# [수정] 필터 결과가 0명인지 확인하기
if len(filtered) == 0:
    # [수정] 안내 문구를 보여주고
    st.info("조건에 맞는 승객이 없습니다.")
    # [수정] 아래 코드는 실행하지 않고 멈추기
    st.stop()

# 필터된 데이터로 KPI 값 3개 계산하기
total, survival_rate, avg_age = kpi(filtered)

# 숫자 카드를 놓을 3칸 만들기
col1, col2, col3 = st.columns(3)

# 첫째 칸: 승객 수 카드
col1.metric("승객 수(명)", total)

# 둘째 칸: 생존율 카드
col2.metric("생존율(%)", survival_rate)

# 셋째 칸: 평균 나이 카드
col3.metric("평균 나이(세)", avg_age)


# ===== 차트 =====
# 차트를 놓을 2칸 만들기
left, right = st.columns(2)

# 왼쪽 칸: 객실 등급별 생존율 막대그래프
left.plotly_chart(class_rate_bar(filtered))

# 오른쪽 칸: 생존 여부별 나이 히스토그램
right.plotly_chart(age_hist(filtered))


# ===== 데이터 표 =====
# 접었다 펼 수 있는 "데이터 보기" 영역 만들기
with st.expander("데이터 보기"):
    # 필터된 승객 표를 보여주기
    st.dataframe(filtered)
