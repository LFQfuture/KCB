import streamlit as st
import pandas as pd
import datetime
import time
import plotly.express as px
import plotly.graph_objects as go

# ---------------------- 1. 本地关键词解析（替代百度NLP） ----------------------
# 课前准备关键词库（可自定义扩展）
PREPARE_KEYWORDS = ["课本", "习题集", "作业", "耳机", "U盘", "实验报告", "笔记本"]
# 调课关键词库
CHANGE_KEYWORDS = ["调至", "改为", "临时变更", "替换", "调整"]

# 本地解析课前准备关键词
def extract_prepare_keywords(text):
    if pd.isna(text) or text == "":
        return []
    text = str(text).lower()
    matched = [kw for kw in PREPARE_KEYWORDS if kw in text]
    return matched if matched else ["无明确准备项"]

# 本地解析调课信息
def extract_change_keywords(text):
    if pd.isna(text) or text == "":
        return []
    text = str(text).lower()
    matched = [kw for kw in CHANGE_KEYWORDS if kw in text]
    return matched if matched else ["无调课信息"]

# ---------------------- 2. 课程表解析与提醒逻辑 ----------------------
# 节次-上课时间映射（可按学校作息修改）
CLASS_TIME_MAP = {
    "1": "08:00", "2": "08:50", "3": "10:00", "4": "10:50",
    "5": "14:00", "6": "14:50", "7": "16:00", "8": "16:50",
    "9": "19:00", "10": "19:50", "11": "20:40"
}

# 计算当前时间与上课时间的差值（分钟）
def get_time_diff(class_time):
    now = datetime.datetime.now().strftime("%H:%M")
    now_h, now_m = map(int, now.split(":"))
    class_h, class_m = map(int, class_time.split(":"))
    # 计算时间差（正数=还没到上课时间，负数=已过）
    diff = (class_h - now_h) * 60 + (class_m - now_m)
    return diff

# 智能提醒判断
def check_reminder(course_df):
    reminders = []
    # 获取今天星期（1=周一，7=周日）
    today_week_num = datetime.datetime.now().weekday() + 1
    today_week_str = f"星期{today_week_num}"
    
    # 筛选今天的课程
    today_courses = course_df[course_df["星期"] == today_week_str].reset_index(drop=True)
    
    for idx, course in today_courses.iterrows():
        class_section = str(course["节次"])
        # 匹配上课时间
        class_time = CLASS_TIME_MAP.get(class_section, "")
        if not class_time:
            continue
        
        # 计算时间差，触发不同提醒
        time_diff = get_time_diff(class_time)
        course_name = course["课程名"]
        classroom = course["教室"]
        prepare_keywords = course["准备项关键词"]
        change_info = course["调课关键词"]
        
        # 1. 课前1小时提醒（55-65分钟内）
        if 55 <= time_diff <= 65:
            reminders.append({
                "type": "hour_before",
                "content": f"⏰ 课前1小时提醒 | {course_name}（{classroom}）\n需准备：{','.join(prepare_keywords)}",
                "course": course_name,
                "time": class_time
            })
        # 2. 课前30分钟提醒（25-35分钟内）
        elif 25 <= time_diff <= 35:
            reminders.append({
                "type": "half_hour_before",
                "content": f"🚨 课前30分钟提醒 | {course_name}即将开始！\n教室：{classroom}",
                "course": course_name,
                "time": class_time
            })
        # 3. 调课提醒（识别到调课关键词）
        if change_info != ["无调课信息"]:
            reminders.append({
                "type": "change",
                "content": f"📢 调课提醒 | {course_name}\n备注：{course['备注']}",
                "course": course_name,
                "time": class_time
            })
    
    return reminders

# ---------------------- 3. 现代化Streamlit界面 ----------------------
def main():
    # 页面基础配置
    st.set_page_config(
        page_title="智能课程表管理系统",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 自定义CSS样式
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .step-card {
        background: #f8f9ff;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid #e1e5f7;
    }
    
    .alert-hour {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-left: 4px solid #f39c12;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .alert-half {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .alert-change {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        color: #155724;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .emoji-large {
        font-size: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 顶部标题区域
    st.markdown("""
    <div class="main-header">
        <h1 class="emoji-large">🎓 智能课程表管理系统</h1>
        <p>本地AI解析 · 实时智能提醒 · 无需云服务</p>
        <p>📅 当前时间：{}</p>
    </div>
    """.format(datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")), unsafe_allow_html=True)
    
    # 侧边栏 - 功能导航
    with st.sidebar:
        st.markdown("## 🧭 功能导航")
        
        # 当前状态卡片
        now = datetime.datetime.now()
        current_weekday = now.weekday() + 1
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        st.markdown(f"""
        <div class="stats-card">
            <h3>📅 今日概览</h3>
            <p><strong>今天是：</strong> {weekday_names[current_weekday-1]}</p>
            <p><strong>当前时间：</strong> {now.strftime('%H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 快速功能按钮
        if st.button("🚀 快速开始", use_container_width=True):
            st.session_state.active_tab = "upload"
            
        st.markdown("---")
        st.markdown("## 📋 快速信息")
        
        # 课程表字段说明
        with st.expander("📚 课程表格式说明", expanded=False):
            st.markdown("""
            **必需字段：**
            - 课程名（如：高等数学）
            - 周次（如：1-16周）
            - 星期（如：星期三）
            - 节次（如：3）
            - 教室（如：3教201）
            - 课前准备（如：带习题集）
            - 备注（如：调至周五第6节）
            """)
    
    # 主内容区域 - 选项卡设计
    tab1, tab2, tab3, tab4 = st.tabs(["📤 上传课程表", "🧠 AI智能解析", "🔔 实时提醒", "📊 数据统计"])
    
    with tab1:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📤 上传课程表")
        st.markdown("支持Excel格式，系统会自动识别课程信息并进行智能解析")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 文件上传区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "选择课程表文件",
                type=["xlsx"],
                help="请上传包含完整课程信息的Excel文件",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("""
            <div class="card">
                <h4>📋 示例文件</h4>
                <p>如果没有课程表，可以下载示例文件：</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📥 下载示例课程表", type="secondary"):
                # 创建示例数据
                sample_data = {
                    '课程名': ['高等数学', '大学英语', '计算机基础'],
                    '周次': ['1-16周', '1-16周', '1-16周'],
                    '星期': ['星期三', '星期三', '星期四'],
                    '节次': [3, 5, 2],
                    '教室': ['3教201', '语音室1', '机房5'],
                    '课前准备': [
                        '带微积分习题集+完成P20作业',
                        '带英语课本+听力耳机',
                        '带U盘+完成实验报告1'
                    ],
                    '备注': [
                        '-',
                        '本周调至星期五第6节',
                        '-'
                    ]
                }
                sample_df = pd.DataFrame(sample_data)
                st.download_button(
                    "下载Excel文件",
                    data=sample_df.to_excel(index=False, engine='openpyxl'),
                    file_name="课程表示例.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        if uploaded_file:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 课程表预览")
            
            # 读取并展示课程表
            course_df = pd.read_excel(uploaded_file)
            
            # 格式化显示
            st.dataframe(
                course_df,
                use_container_width=True,
                column_config={
                    "课程名": st.column_config.TextColumn("课程名称", help="课程的具体名称"),
                    "教室": st.column_config.TextColumn("教室位置", help="上课的教室或实验室"),
                    "课前准备": st.column_config.TextColumn("准备事项", help="需要携带的物品或完成的作业"),
                }
            )
            
            # 数据验证
            required_columns = ['课程名', '周次', '星期', '节次', '教室', '课前准备', '备注']
            missing_columns = [col for col in required_columns if col not in course_df.columns]
            
            if missing_columns:
                st.error(f"❌ 缺少必需字段：{', '.join(missing_columns)}")
                return
            else:
                st.success("✅ 课程表格式验证通过！")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.session_state.course_df = course_df
            
            # 解析按钮
            if st.button("🚀 开始AI智能解析", type="primary", use_container_width=True):
                st.session_state.active_tab = "analysis"
    
    with tab2:
        if 'course_df' not in st.session_state:
            st.info("👆 请先上传课程表")
            return
            
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("🧠 AI智能解析")
        st.markdown("系统会自动识别课前准备要求和调课信息")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 解析按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔍 开始解析", type="primary", use_container_width=True):
                with st.spinner("🤖 AI正在解析课程信息..."):
                    # 模拟AI处理时间
                    time.sleep(2)
                    
                    # 执行解析
                    course_df = st.session_state.course_df.copy()
                    course_df["准备项关键词"] = course_df["课前准备"].apply(extract_prepare_keywords)
                    course_df["调课关键词"] = course_df["备注"].apply(extract_change_keywords)
                    
                    st.session_state.course_df = course_df
                
                st.success("✅ AI解析完成！")
        
        # 解析结果展示
        if 'course_df' in st.session_state and '准备项关键词' in st.session_state.course_df.columns:
            st.markdown("## 📊 解析结果")
            
            # 创建三个展示区域
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📚 课程总览")
                st.metric("总课程数", len(st.session_state.course_df))
                
                # 课程分布图
                course_count = st.session_state.course_df['课程名'].value_counts()
                if len(course_count) > 0:
                    fig = px.pie(values=course_count.values, names=course_count.index, 
                               title="课程分布")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🕒 时间分布")
                week_distribution = st.session_state.course_df['星期'].value_counts()
                if len(week_distribution) > 0:
                    fig = px.bar(x=week_distribution.index, y=week_distribution.values,
                               title="每日课程数量", labels={'x': '星期', 'y': '课程数量'})
                    st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                st.markdown("### ⚠️ 注意事项")
                changes = st.session_state.course_df[st.session_state.course_df['调课关键词'] != ['无调课信息']]
                st.metric("调课数量", len(changes))
                
                if len(changes) > 0:
                    for _, change in changes.iterrows():
                        st.warning(f"📢 {change['课程名']}: {change['备注']}")
            
            # 详细解析表格
            st.markdown("### 📋 详细解析结果")
            display_cols = ['课程名', '教室', '星期', '节次', '准备项关键词', '调课关键词']
            if '调课关键词' in st.session_state.course_df.columns:
                st.dataframe(
                    st.session_state.course_df[display_cols],
                    use_container_width=True
                )
    
    with tab3:
        if 'course_df' not in st.session_state:
            st.info("👆 请先完成课程表上传和解析")
            return
            
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("🔔 实时提醒中心")
        st.markdown("基于当前时间自动生成课程提醒信息")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 刷新按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 刷新提醒", type="primary", use_container_width=True):
                st.rerun()
        
        # 提醒内容
        reminders = check_reminder(st.session_state.course_df)
        
        if reminders:
            st.markdown("### 🎯 当前提醒")
            for reminder in reminders:
                if reminder["type"] == "hour_before":
                    st.markdown(f'<div class="alert-hour">{reminder["content"]}</div>', unsafe_allow_html=True)
                elif reminder["type"] == "half_hour_before":
                    st.markdown(f'<div class="alert-half">{reminder["content"]}</div>', unsafe_allow_html=True)
                elif reminder["type"] == "change":
                    st.markdown(f'<div class="alert-change">{reminder["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-box">
                <h3>🎉 太棒了！</h3>
                <p>当前暂无待提醒课程</p>
                <p>可以安心学习或休息啦～</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 测试功能
        with st.expander("🧪 测试提醒功能", expanded=False):
            st.markdown("### 手动测试提醒")
            
            col1, col2 = st.columns(2)
            with col1:
                test_section = st.selectbox("选择节次", list(CLASS_TIME_MAP.keys()), key="test_section")
                test_course = st.text_input("测试课程名", "高等数学", key="test_course")
            
            with col2:
                test_classroom = st.text_input("测试教室", "3教201", key="test_classroom")
                test_preparation = st.text_input("准备事项", "带习题集", key="test_prep")
            
            if st.button("🎯 触发测试提醒", type="secondary"):
                test_time = CLASS_TIME_MAP[test_section]
                st.markdown(f"""
                <div class="alert-half">
                    <strong>🚨 测试提醒</strong><br>
                    课程：{test_course}<br>
                    教室：{test_classroom}<br>
                    上课时间：{test_time}<br>
                    准备事项：{test_preparation}
                </div>
                """, unsafe_allow_html=True)
    
    with tab4:
        if 'course_df' not in st.session_state:
            st.info("👆 请先完成课程表上传和解析")
            return
            
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📊 数据统计分析")
        st.markdown("课程安排的全面数据分析和可视化")
        st.markdown('</div>', unsafe_allow_html=True)
        
        course_df = st.session_state.course_df
        
        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stats-card">
                <h3>📚</h3>
                <h2>{}</h2>
                <p>总课程数</p>
            </div>
            """.format(len(course_df)), unsafe_allow_html=True)
        
        with col2:
            unique_courses = course_df['课程名'].nunique()
            st.markdown("""
            <div class="stats-card">
                <h3>📖</h3>
                <h2>{}</h2>
                <p>不重复课程</p>
            </div>
            """.format(unique_courses), unsafe_allow_html=True)
        
        with col3:
            unique_classrooms = course_df['教室'].nunique()
            st.markdown("""
            <div class="stats-card">
                <h3>🏫</h3>
                <h2>{}</h2>
                <p>使用教室</p>
            </div>
            """.format(unique_classrooms), unsafe_allow_html=True)
        
        with col4:
            changes = course_df[course_df['调课关键词'] != ['无调课信息']]
            change_count = len(changes)
            st.markdown("""
            <div class="stats-card">
                <h3>📢</h3>
                <h2>{}</h2>
                <p>调课次数</p>
            </div>
            """.format(change_count), unsafe_allow_html=True)
        
        # 详细分析图表
        col1, col2 = st.columns(2)
        
        with col1:
            # 每日课程分布
            st.markdown("### 📅 每日课程分布")
            week_dist = course_df['星期'].value_counts().sort_index()
            
            # 按星期顺序排序
            week_order = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
            week_dist = week_dist.reindex([day for day in week_order if day in week_dist.index])
            
            fig = px.bar(x=week_dist.index, y=week_dist.values,
                        title="每日课程数量", 
                        labels={'x': '星期', 'y': '课程数量'},
                        color=week_dist.values,
                        color_continuous_scale='viridis')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 节次分布
            st.markdown("### 🕐 节次分布")
            section_dist = course_df['节次'].value_counts().sort_index()
            
            fig = px.bar(x=[f"第{section}节" for section in section_dist.index], 
                        y=section_dist.values,
                        title="各节次课程数量",
                        labels={'x': '节次', 'y': '课程数量'},
                        color=section_dist.values,
                        color_continuous_scale='plasma')
            st.plotly_chart(fig, use_container_width=True)
        
        # 教室使用情况
        st.markdown("### 🏫 教室使用频率")
        classroom_dist = course_df['教室'].value_counts().head(10)
        
        fig = px.treemap(values=classroom_dist.values, 
                        names=classroom_dist.index,
                        title="教室使用频率TOP10")
        st.plotly_chart(fig, use_container_width=True)
        
        # 准备事项分析
        if '准备项关键词' in course_df.columns:
            st.markdown("### 📋 准备事项统计")
            
            # 统计所有准备关键词
            all_preps = []
            for prep_list in course_df['准备项关键词']:
                if isinstance(prep_list, list):
                    all_preps.extend(prep_list)
            
            if all_preps:
                prep_count = pd.Series(all_preps).value_counts()
                
                fig = px.pie(values=prep_count.values, 
                            names=prep_count.index,
                            title="准备事项分布")
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()