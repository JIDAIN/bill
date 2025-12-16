import pandas as pd
import plotly.express as px
import streamlit as st

# =====================
# 数据读取与预处理
# =====================
@st.cache_data
def load_data(file_path):
    """加载数据并进行预处理，使用缓存避免重复读取"""
    df = pd.read_excel(file_path)
    df['日期'] = pd.to_datetime(df['日期'])
    df['年份'] = df['日期'].dt.year
    # 使用 'YYYY-MM' 格式的月份，确保排序正确
    df['月份'] = df['日期'].dt.to_period('M').astype(str) 
    df['金额_abs'] = df['金额'].abs()

    income_df = df[df['收支类型'] == '收入']
    expense_df = df[df['收支类型'] == '支出']
    
    return df, income_df, expense_df

try:
    # 假设文件名为 '账单.xlsx' 或 'mybill.xlsx' (如果您已重命名)
    df, income_df, expense_df = load_data("账单.xlsx") 
    latest_year = df['年份'].max()
except FileNotFoundError:
    st.error("⚠️ 错误：找不到文件 '账单.xlsx'。请确保文件与脚本在同一目录下。")
    st.stop()
except Exception as e:
    st.error(f"⚠️ 数据加载或预处理失败: {e}")
    st.stop()

# =====================
# Streamlit 布局与图表函数
# =====================

st.set_page_config(layout="wide", page_title="个人账单可视化仪表盘")

st.title("💰 个人账单可视化仪表盘")
st.markdown("---")

# --- 辅助函数：创建饼图 ---
def create_pie_chart(data, names_col, mode, title):
    """
    创建并优化饼状图，使其同时显示金额/占比和类型。
    """
    # 汇总数据
    d_agg = data.groupby(names_col)['金额_abs'].sum().reset_index()

    # 创建饼图
    fig = px.pie(
        d_agg, 
        values='金额_abs', 
        names=names_col, 
        hole=0.4,
        # 设置鼠标悬停数据
        hover_data=['金额_abs']
    )
    
    # 优化 trace 文本显示
    fig.update_traces(
        # 确定显示的内容：类型 (label) 和 值 (value)
        textinfo='label+value',
        # 定制显示文本的格式
        texttemplate="<b>%{label}</b><br>%{value:.2f}",
        marker=dict(line=dict(color='#000000', width=1))
    )

    # 如果选择 "占比" 模式，则覆盖文本模板，显示百分比和类型
    if mode == '占比':
        fig.update_traces(
            textinfo='label+percent',
            texttemplate="<b>%{label}</b><br>%{percent}"
        )
    
    # 进一步优化布局和标题
    fig.update_layout(
        margin=dict(t=50, b=0, l=0, r=0),
        title_text=title,
        title_x=0.5
    )
    return fig


# --- 第一部分：收入/支出概览 ---
st.header("1. 概览：收入与支出构成")

col1, col2 = st.columns(2)

with col1:
    st.subheader("总收入构成")
    income_mode = st.radio("选择显示模式 (收入)", ['金额', '占比'], key='income_mode', horizontal=True)
    
    fig_income = create_pie_chart(income_df, '一级分类', income_mode, "总收入构成")
    st.plotly_chart(fig_income, use_container_width=True)

with col2:
    st.subheader("总支出构成（一级分类）")
    expense_mode = st.radio("选择显示模式 (支出)", ['金额', '占比'], key='expense_mode', horizontal=True)

    fig_expense = create_pie_chart(expense_df, '一级分类', expense_mode, "总支出构成")
    st.plotly_chart(fig_expense, use_container_width=True)

st.markdown("---")


# --- 第二部分：支出明细 / 标签占比 ---
st.header("2. 细分：明细与标签分析")

col3, col4 = st.columns(2)

# --- 支出明细分析 ---
with col3:
    st.subheader("🔍 支出明细分析 (二级分类)")
    
    detail_main = st.selectbox("选择一级分类", expense_df['一级分类'].unique(), key='detail_main')
    
    # 根据一级分类更新二级分类的选项
    subs_options = expense_df[expense_df['一级分类'] == detail_main]['二级分类'].unique()
    detail_sub = st.multiselect("选择二级分类 (多选)", subs_options, default=list(subs_options), key='detail_sub')
    
    detail_mode = st.radio("选择显示模式 (明细)", ['金额', '占比'], key='detail_mode', horizontal=True)
    
    if detail_sub:
        d_detail = expense_df[(expense_df['一级分类'] == detail_main) & (expense_df['二级分类'].isin(detail_sub))]
        # 调用优化后的函数
        fig_detail = create_pie_chart(d_detail, '二级分类', detail_mode, f"[{detail_main}]明细")
        st.plotly_chart(fig_detail, use_container_width=True)
    else:
        st.warning("请至少选择一个二级分类。")


# --- 支出标签占比 ---
with col4:
    st.subheader("🏷️ 支出标签占比 (年度)")
    
    tag_year = st.selectbox("选择年份", sorted(df['年份'].unique()), index=len(df['年份'].unique()) - 1, key='tag_year')
    tag_mode = st.radio("选择显示模式 (标签)", ['金额', '占比'], key='tag_mode', horizontal=True)
    
    d_tag = expense_df[expense_df['年份'] == tag_year]
    # 调用优化后的函数
    fig_tag = create_pie_chart(d_tag, '标签', tag_mode, f"{tag_year}年支出标签占比")
    st.plotly_chart(fig_tag, use_container_width=True)

st.markdown("---")


# --- 第三部分：月度趋势 (折线图显示金额数据) ---
st.header("3. 趋势：各一级分类 · 月度支出趋势")

order = ['吃喝玩乐','人情','生活用品','服饰美妆','自我提升','My love','旅游','餐饮','固定支出','交通','其他']

cols = st.columns(2) 

for i, cat in enumerate(order):
    col = cols[i % 2] 
    
    with col:
        with st.spinner(f"正在加载 {cat} 趋势图..."):
            d_trend = expense_df[expense_df['一级分类'] == cat].groupby('月份')['金额_abs'].sum().reset_index()
            
            # --- 折线图显示金额数据优化 ---
            fig_trend = px.line(
                d_trend, 
                x='月份', 
                y='金额_abs', 
                title=cat,
                # 关键：添加 text 参数，将金额绑定到数据点
                text='金额_abs', 
                markers=True # 显示数据点
            )
            
            # 关键：更新 traces，设置文本格式和位置
            fig_trend.update_traces(
                texttemplate='%{text:.0f}', # 文本格式为不带小数的金额
                textposition='top center', # 文本位置在数据点上方
                line=dict(width=3) # 稍微加粗线条，增强显示效果
            )
            
            # 优化轴标签
            fig_trend.update_layout(
                yaxis_title="金额",
                xaxis_title="月份"
            )
            # --- 优化结束 ---

            st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")
st.caption("基于 Streamlit & Plotly 生成")