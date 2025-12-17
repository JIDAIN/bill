import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_javascript import st_javascript

# =====================
# 页面设置
# =====================
st.set_page_config(layout="wide", page_title="个人账单可视化仪表盘")

# =====================
# 设备识别
# =====================
screen_width = st_javascript("window.innerWidth", key="screen_width")
is_mobile = screen_width is not None and screen_width < 768

st.title("💰 个人账单可视化仪表盘（安全版）")
st.caption("账单仅在当前会话内存中处理，不会上传或保存")
st.divider()

# =====================
# 上传账单（方案 A）
# =====================
uploaded_file = st.file_uploader(
    "📤 上传你的账单 Excel（仅当前会话使用）",
    type=["xlsx"]
)

if uploaded_file is None:
    st.stop()

# =====================
# 数据处理
# =====================
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df["日期"] = pd.to_datetime(df["日期"])
    df["年份"] = df["日期"].dt.year
    df["月份"] = df["日期"].dt.to_period("M").astype(str)
    df["金额_abs"] = df["金额"].abs()
    return df

df = load_data(uploaded_file)
income_df = df[df["收支类型"] == "收入"]
expense_df = df[df["收支类型"] == "支出"]
all_years = sorted(df["年份"].unique())

# =====================
# 通用饼图函数
# =====================
def pie(data, col, mode, title):
    d = data.groupby(col)["金额_abs"].sum().reset_index()
    fig = px.pie(d, values="金额_abs", names=col, hole=0.4)
    if mode == "金额":
        fig.update_traces(textinfo="label+value", texttemplate="%{value:.0f}")
    else:
        fig.update_traces(textinfo="label+percent")
    fig.update_layout(title=title, title_x=0.5)
    return fig

# ==================================================
# 第一部分：收入 / 支出构成
# ==================================================
st.header("1️⃣ 收入 / 支出构成（按年）")

if not is_mobile:
    c1, c2 = st.columns(2)
else:
    c1 = c2 = st.container()

with c1:
    st.subheader("💵 收入构成")
    y = st.selectbox("年份", all_years, index=len(all_years)-1, key="income_y")
    m = st.radio("显示方式", ["金额", "占比"], horizontal=True, key="income_m")
    st.plotly_chart(
        pie(income_df[income_df["年份"] == y], "类别", m, f"{y} 年收入构成"),
        use_container_width=True
    )

with c2:
    st.subheader("💸 支出构成")
    y = st.selectbox("年份 ", all_years, index=len(all_years)-1, key="expense_y")
    m = st.radio("显示方式 ", ["金额", "占比"], horizontal=True, key="expense_m")
    st.plotly_chart(
        pie(expense_df[expense_df["年份"] == y], "类别", m, f"{y} 年支出构成"),
        use_container_width=True
    )

st.divider()

# ==================================================
# 第二部分：支出明细 / 标签
# ==================================================
st.header("2️⃣ 支出明细与标签分析")

if not is_mobile:
    c3, c4 = st.columns(2)
else:
    c3 = c4 = st.container()

with c3:
    st.subheader("🔍 二级分类明细")
    cat = st.selectbox("类别", expense_df["类别"].unique())
    subs = expense_df[expense_df["类别"] == cat]["二级分类"].unique()
    sel = st.multiselect("二级分类", subs, default=list(subs))
    m = st.radio("显示方式  ", ["金额", "占比"], horizontal=True, key="detail_m")
    d = expense_df[
        (expense_df["类别"] == cat) &
        (expense_df["二级分类"].isin(sel))
    ]
    st.plotly_chart(pie(d, "二级分类", m, f"{cat} 支出明细"), use_container_width=True)

with c4:
    st.subheader("🏷️ 标签占比")
    y = st.selectbox("年份  ", all_years, index=len(all_years)-1, key="tag_y")
    m = st.radio("显示方式   ", ["金额", "占比"], horizontal=True, key="tag_m")
    st.plotly_chart(
        pie(expense_df[expense_df["年份"] == y], "标签", m, f"{y} 年标签占比"),
        use_container_width=True
    )

st.divider()

# ==================================================
# 第三部分：月度趋势
# ==================================================
st.header("3️⃣ 月度支出趋势")

order = [
    "吃喝玩乐", "人情", "生活用品", "服饰美妆",
    "自我提升", "My love", "旅游", "餐饮",
    "固定支出", "交通", "其他"
]

for cat in order:
    d = (
        expense_df[expense_df["类别"] == cat]
        .groupby("月份")["金额_abs"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        d, x="月份", y="金额_abs",
        markers=True, text="金额_abs", title=cat
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

st.caption("🔐 安全模式 · 数据仅存在当前会话")
