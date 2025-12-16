# Streamlit 账单可视化仪表盘（V2：收入/支出支持按年筛选）
# 运行方式：streamlit run mybill.py

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide", page_title="个人账单可视化仪表盘")

# =====================
# 数据读取与预处理
# =====================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    df['日期'] = pd.to_datetime(df['日期'])
    df['年份'] = df['日期'].dt.year
    df['月份'] = df['日期'].dt.to_period('M').astype(str)
    df['金额_abs'] = df['金额'].abs()
    return df

try:
    df = load_data("账单.xlsx")
except FileNotFoundError:
    st.error("⚠️ 找不到文件 账单.xlsx，请确认与脚本在同一目录")
    st.stop()

income_df = df[df['收支类型'] == '收入']
expense_df = df[df['收支类型'] == '支出']

all_years = sorted(df['年份'].unique())
latest_year = all_years[-1]

st.title("💰 个人账单可视化仪表盘")
st.divider()

# =====================
# 通用饼图函数
# =====================
def create_pie_chart(data, names_col, mode, title):
    d_agg = data.groupby(names_col)['金额_abs'].sum().reset_index()

    fig = px.pie(
        d_agg,
        values='金额_abs',
        names=names_col,
        hole=0.4
    )

    if mode == '占比':
        fig.update_traces(textinfo='label+percent')
    else:
        fig.update_traces(textinfo='label+value', texttemplate='%{label}<br>%{value:.0f}')

    fig.update_layout(title=title, title_x=0.5, margin=dict(t=50, b=0, l=0, r=0))
    return fig

# =====================
# 第一部分：收入 / 支出构成（支持按年）
# =====================
st.header("1. 概览：收入与支出构成（按年）")

col1, col2 = st.columns(2)

with col1:
    st.subheader("总收入构成")
    income_year = st.selectbox("选择年份（收入）", all_years, index=len(all_years)-1, key='income_year')
    income_mode = st.radio("显示方式", ['金额', '占比'], horizontal=True, key='income_mode')

    d_income = income_df[income_df['年份'] == income_year]
    fig_income = create_pie_chart(d_income, '类别', income_mode, f"{income_year} 年收入构成")
    st.plotly_chart(fig_income, use_container_width=True)

with col2:
    st.subheader("总支出构成（类别）")
    expense_year = st.selectbox("选择年份（支出）", all_years, index=len(all_years)-1, key='expense_year')
    expense_mode = st.radio("显示方式", ['金额', '占比'], horizontal=True, key='expense_mode')

    d_expense = expense_df[expense_df['年份'] == expense_year]
    fig_expense = create_pie_chart(d_expense, '类别', expense_mode, f"{expense_year} 年支出构成")
    st.plotly_chart(fig_expense, use_container_width=True)

st.divider()

# =====================
# 第二部分：支出明细 / 标签占比
# =====================
st.header("2. 细分：支出明细与标签分析")

col3, col4 = st.columns(2)

with col3:
    st.subheader("🔍 支出明细分析（二级分类）")
    main_cat = st.selectbox("类别", expense_df['类别'].unique())
    sub_opts = expense_df[expense_df['类别'] == main_cat]['二级分类'].unique()
    sub_sel = st.multiselect("二级分类", sub_opts, default=list(sub_opts))
    detail_mode = st.radio("显示方式", ['金额', '占比'], horizontal=True, key='detail_mode')

    if sub_sel:
        d_detail = expense_df[(expense_df['类别'] == main_cat) & (expense_df['二级分类'].isin(sub_sel))]
        fig_detail = create_pie_chart(d_detail, '二级分类', detail_mode, f"[{main_cat}] 支出明细")
        st.plotly_chart(fig_detail, use_container_width=True)
    else:
        st.warning("请至少选择一个二级分类")

with col4:
    st.subheader("🏷️ 支出标签占比（年度）")
    tag_year = st.selectbox("选择年份（标签）", all_years, index=len(all_years)-1, key='tag_year')
    tag_mode = st.radio("显示方式", ['金额', '占比'], horizontal=True, key='tag_mode')

    d_tag = expense_df[expense_df['年份'] == tag_year]
    fig_tag = create_pie_chart(d_tag, '标签', tag_mode, f"{tag_year} 年支出标签占比")
    st.plotly_chart(fig_tag, use_container_width=True)

st.divider()

# =====================
# 第三部分：月度趋势
# =====================
st.header("3. 各类别 · 月度支出趋势")

order = ['吃喝玩乐','人情','生活用品','服饰美妆','自我提升','My love','旅游','餐饮','固定支出','交通','其他']

for i in range(0, len(order), 2):
    c1, c2 = st.columns(2)
    for col, cat in zip([c1, c2], order[i:i+2]):
        with col:
            d_trend = expense_df[expense_df['类别'] == cat].groupby('月份')['金额_abs'].sum().reset_index()
            fig = px.line(d_trend, x='月份', y='金额_abs', title=cat, markers=True)
            fig.update_layout(xaxis_title='月份', yaxis_title='金额')
            st.plotly_chart(fig, use_container_width=True)

st.caption("基于 Streamlit & Plotly · 个人账单分析")
