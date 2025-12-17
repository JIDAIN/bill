import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_javascript import st_javascript

# =====================
# 页面设置
# =====================
st.set_page_config(
    layout="wide",
    page_title="个人账单可视化仪表盘",
)

# =====================
# 设备识别（关键）
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
    type=["xlsx"],
    key="file_uploader"
)

if uploaded_file is None:
    st.info("请先上传账单文件（Excel）")
    st.stop()

# =====================
# 数据读取与预处理
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
def create_pie_chart(data, names_col, mode, title):
    d = data.groupby(names_col)["金额_abs"].sum().reset_index()
    fig = px.pie(d, values="金额_abs", names=names_col, hole=0.4)

    if mode == "占比":
        fig.update_traces(textinfo="label+percent")
    else:
        fig.update_traces(
            textinfo="label+value",
            texttemplate="%{label}<br>%{value:.0f}"
        )

    fig.update_layout(title=title, title_x=0.5)
    return fig

# =====================
# 第一部分：收入 / 支出构成
# =====================
st.header("1️⃣ 收入 / 支出构成（按年）")

income_year = st.selectbox("收入年份", all_years, index=len(all_years)-1)
income_mode = st.radio("收入显示方式", ["金额", "占比"], horizontal=True)

expense_year = st.selectbox("支出年份", all_years, index=len(all_years)-1)
expense_mode = st.radio("支出显示方式", ["金额", "占比"], horizontal=True)

fig_income = create_pie_chart(
    income_df[income_df["年份"] == income_year],
    "类别",
    income_mode,
    f"{income_year} 年收入构成"
)

fig_expense = create_pie_chart(
    expense_df[expense_df["年份"] == expense_year],
    "类别",
    expense_mode,
    f"{expense_year} 年支出构成"
)

# =====================
# 第二部分：支出明细 / 标签
# =====================
main_cat = st.selectbox("支出类别", expense_df["类别"].unique())
sub_opts = expense_df[expense_df["类别"] == main_cat]["二级分类"].unique()
sub_sel = st.multiselect("二级分类", sub_opts, default=list(sub_opts))
detail_mode = st.radio("明细显示方式", ["金额", "占比"], horizontal=True)

detail_df = expense_df[
    (expense_df["类别"] == main_cat) &
    (expense_df["二级分类"].isin(sub_sel))
]

fig_detail = create_pie_chart(
    detail_df,
    "二级分类",
    detail_mode,
    f"[{main_cat}] 支出明细"
)

tag_year = st.selectbox("标签年份", all_years, index=len(all_years)-1)
tag_mode = st.radio("标签显示方式", ["金额", "占比"], horizontal=True)

fig_tag = create_pie_chart(
    expense_df[expense_df["年份"] == tag_year],
    "标签",
    tag_mode,
    f"{tag_year} 年支出标签占比"
)

# =====================
# 第三部分：趋势图
# =====================
order = [
    "吃喝玩乐", "人情", "生活用品", "服饰美妆", "自我提升",
    "My love", "旅游", "餐饮", "固定支出", "交通", "其他"
]

trend_figs = []
for cat in order:
    d_trend = (
        expense_df[expense_df["类别"] == cat]
        .groupby("月份")["金额_abs"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        d_trend,
        x="月份",
        y="金额_abs",
        title=cat,
        markers=True,
        text="金额_abs"
    )
    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="top center",
        line=dict(width=3)
    )
    trend_figs.append(fig)

# =====================
# 📱 / 💻 布局切换
# =====================
st.divider()

if not is_mobile:
    # ===== 桌面端 =====
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_income, use_container_width=True)
    c2.plotly_chart(fig_expense, use_container_width=True)

    c3, c4 = st.columns(2)
    c3.plotly_chart(fig_detail, use_container_width=True)
    c4.plotly_chart(fig_tag, use_container_width=True)

    st.header("📈 月度趋势")
    for i in range(0, len(trend_figs), 2):
        cc1, cc2 = st.columns(2)
        cc1.plotly_chart(trend_figs[i], use_container_width=True)
        if i + 1 < len(trend_figs):
            cc2.plotly_chart(trend_figs[i+1], use_container_width=True)

else:
    # ===== 手机端 =====
    st.header("📱 手机端账单概览")

    st.plotly_chart(fig_income, use_container_width=True)
    st.plotly_chart(fig_expense, use_container_width=True)

    with st.expander("🔍 支出明细"):
        st.plotly_chart(fig_detail, use_container_width=True)

    with st.expander("🏷️ 标签占比"):
        st.plotly_chart(fig_tag, use_container_width=True)

    with st.expander("📈 月度趋势"):
        for fig in trend_figs:
            st.plotly_chart(fig, use_container_width=True)

st.caption("🔐 安全模式 · 数据仅存在当前会话")
