import streamlit as st
import pandas as pd
import datetime
import time

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
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
    }
    
    .step-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #e1e5f7 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 1px solid #d1d9f0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .alert-hour {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #f39c12;
        border-left: 5px solid #f39c12;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(243, 156, 18, 0.2);
    }
    
    .alert-half {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #e74c3c;
        border-left: 5px solid #e74c3c;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.2);
        animation: pulse 2s infinite;
    }
    
    .alert-change {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #3498db;
        border-left: 5px solid #3498db;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        color: #155724;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        transition: transform 0.3s ease;
    }
    
    .stats-card:hover {
        transform: scale(1.02);
    }
    
    .emoji-large {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: #28a745;
        animation: pulse 2s infinite;
    }
    
    .status-warning {
        background-color: #ffc107;
        animation: pulse 2s infinite;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e1e5f7 50%, #f8f9ff 100%);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #e1e5f7 0%, #f8f9ff 50%, #e1e5f7 100%);
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .custom-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 8px;
        color: white;
        padding: 0.8rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .custom-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .tab-content {
        padding: 1rem 0;
    }
    
    .progress-indicator {
        width: 100%;
        height: 4px;
        background: #e9ecef;
        border-radius: 2px;
        margin: 1rem 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 顶部标题区域
    now = datetime.datetime.now()
    current_weekday = now.weekday() + 1
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    st.markdown(f"""
    <div class="main-header">
        <div class="emoji-large">🎓</div>
        <h1>智能课程表管理系统</h1>
        <p>本地AI解析 · 实时智能提醒 · 无需云服务</p>
        <div style="margin-top: 1rem;">
            <span class="status-indicator status-online"></span>
            <strong>运行中</strong> · 
            <span style="margin-left: 1rem;">📅 {now.strftime("%Y年%m月%d日")}</span> · 
            <span style="margin-left: 1rem;">🕐 {now.strftime("%H:%M:%S")}</span> · 
            <span style="margin-left: 1rem;">📚 {weekday_names[current_weekday-1]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏 - 功能导航
    with st.sidebar:
        st.markdown("## 🧭 功能导航")
        
        # 当前状态卡片
        st.markdown(f"""
        <div class="stats-card">
            <h3>📅 今日概览</h3>
            <p><strong>今天是：</strong> {weekday_names[current_weekday-1]}</p>
            <p><strong>当前时间：</strong> {now.strftime('%H:%M')}</p>
            <div class="progress-indicator">
                <div class="progress-bar" style="width: {(now.hour * 60 + now.minute) / (24 * 60) * 100}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 快速功能按钮
        if st.button("🚀 快速开始", use_container_width=True):
            st.session_state.active_tab = "upload"
            
        st.markdown("---")
        st.markdown("## 📋 系统状态")
        
        # 状态指示器
        if 'course_df' in st.session_state:
            st.success("✅ 课程表已加载")
            course_count = len(st.session_state.course_df)
            st.info(f"📊 共 {course_count} 门课程")
        else:
            st.info("⏳ 等待上传课程表")
        
        st.markdown("---")
        st.markdown("## 📚 帮助信息")
        
        # 课程表字段说明
        with st.expander("📋 课程表格式说明", expanded=False):
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
        
        with st.expander("🔔 提醒规则", expanded=False):
            st.markdown("""
            **提醒机制：**
            - ⏰ 课前1小时：准备物品提醒
            - 🚨 课前30分钟：上课提醒
            - 📢 调课信息：特殊安排提醒
            """)
    
    # 主内容区域 - 选项卡设计
    tab1, tab2, tab3, tab4 = st.tabs(["📤 上传课程表", "🧠 AI智能解析", "🔔 实时提醒", "📊 数据概览"])
    
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📤 上传课程表")
        st.markdown("支持Excel格式，系统会自动识别课程信息并进行智能解析")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 文件上传区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="upload-area">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3>拖拽文件到此处或点击选择</h3>
                <p>支持 .xlsx 格式</p>
            </div>
            """, unsafe_allow_html=True)
            
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
                <br>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📥 下载示例课程表", type="secondary", use_container_width=True):
                # 创建示例数据
                sample_data = {
                    '课程名': ['高等数学', '大学英语', '计算机基础', '线性代数', '概率论'],
                    '周次': ['1-16周', '1-16周', '1-16周', '1-16周', '1-16周'],
                    '星期': ['星期三', '星期三', '星期四', '星期五', '星期五'],
                    '节次': [3, 5, 2, 1, 3],
                    '教室': ['3教201', '语音室1', '机房5', '2教301', '1教102'],
                    '课前准备': [
                        '带微积分习题集+完成P20作业',
                        '带英语课本+听力耳机',
                        '带U盘+完成实验报告1',
                        '带教材+练习本',
                        '带计算器+完成课后题'
                    ],
                    '备注': [
                        '-',
                        '本周调至星期五第6节',
                        '-',
                        '考试周停课',
                        '-'
                    ]
                }
                sample_df = pd.DataFrame(sample_data)
                
                # 创建下载链接
                import io
                buffer = io.BytesIO()
                sample_df.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                
                st.download_button(
                    "📥 下载Excel文件",
                    data=buffer.getvalue(),
                    file_name="课程表示例.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
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
                st.markdown("**请检查您的课程表是否包含以下字段：**")
                for col in required_columns:
                    if col in missing_columns:
                        st.warning(f"- {col}")
            else:
                st.success("✅ 课程表格式验证通过！")
                
                # 快速统计
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总课程数", len(course_df))
                with col2:
                    st.metric("不重复课程", course_df['课程名'].nunique())
                with col3:
                    st.metric("使用教室", course_df['教室'].nunique())
                with col4:
                    week_count = course_df['星期'].nunique()
                    st.metric("上课天数", week_count)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.session_state.course_df = course_df
            
            # 解析按钮
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 开始AI智能解析", type="primary", use_container_width=True):
                    st.session_state.active_tab = "analysis"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if 'course_df' not in st.session_state:
            st.info("👆 请先上传课程表")
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📤</div>
                <h3>等待上传课程表</h3>
                <p>请先在"上传课程表"选项卡中上传您的课程表文件</p>
            </div>
            """, unsafe_allow_html=True)
            return
            
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
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
                st.balloons()
        
        # 解析结果展示
        if 'course_df' in st.session_state and '准备项关键词' in st.session_state.course_df.columns:
            st.markdown("## 📊 解析结果")
            
            # 创建三个展示区域
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### 📚 课程总览")
                st.metric("总课程数", len(st.session_state.course_df))
                
                # 课程分布显示
                course_count = st.session_state.course_df['课程名'].value_counts()
                if len(course_count) > 0:
                    st.markdown("**课程分布：**")
                    for course, count in course_count.head(5).items():
                        st.write(f"• {course}: {count}节")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### 🕒 时间分布")
                week_distribution = st.session_state.course_df['星期'].value_counts()
                if len(week_distribution) > 0:
                    st.markdown("**每日课程数量：**")
                    for day, count in week_distribution.items():
                        st.write(f"• {day}: {count}节")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### ⚠️ 注意事项")
                changes = st.session_state.course_df[st.session_state.course_df['调课关键词'] != ['无调课信息']]
                st.metric("调课数量", len(changes))
                
                if len(changes) > 0:
                    st.markdown("**调课信息：**")
                    for _, change in changes.iterrows():
                        st.warning(f"📢 {change['课程名']}: {change['备注']}")
                else:
                    st.info("暂无调课信息")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 详细解析表格
            st.markdown("### 📋 详细解析结果")
            display_cols = ['课程名', '教室', '星期', '节次', '准备项关键词', '调课关键词']
            if '调课关键词' in st.session_state.course_df.columns:
                st.dataframe(
                    st.session_state.course_df[display_cols],
                    use_container_width=True
                )
            
            # 进入提醒中心
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔔 查看实时提醒", type="primary", use_container_width=True):
                    st.session_state.active_tab = "reminder"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        if 'course_df' not in st.session_state:
            st.info("👆 请先完成课程表上传和解析")
            return
            
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("🔔 实时提醒中心")
        st.markdown("基于当前时间自动生成课程提醒信息")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 刷新按钮和自动刷新
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 刷新提醒", type="primary"):
                    st.rerun()
            with col_b:
                auto_refresh = st.checkbox("🔄 自动刷新", value=True)
        
        # 自动刷新逻辑
        if auto_refresh:
            time.sleep(1)
            st.rerun()
        
        # 提醒内容
        reminders = check_reminder(st.session_state.course_df)
        
        if reminders:
            st.markdown("### 🎯 当前提醒")
            for i, reminder in enumerate(reminders):
                if reminder["type"] == "hour_before":
                    st.markdown(f'<div class="alert-hour">{reminder["content"]}</div>', unsafe_allow_html=True)
                elif reminder["type"] == "half_hour_before":
                    st.markdown(f'<div class="alert-half">{reminder["content"]}</div>', unsafe_allow_html=True)
                elif reminder["type"] == "change":
                    st.markdown(f'<div class="alert-change">{reminder["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-box">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
                <h3>太棒了！</h3>
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
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        if 'course_df' not in st.session_state:
            st.info("👆 请先完成课程表上传和解析")
            return
            
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📊 数据概览")
        st.markdown("课程安排的全面数据分析和统计")
        st.markdown('</div>', unsafe_allow_html=True)
        
        course_df = st.session_state.course_df
        
        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stats-card">
                <div style="font-size: 2rem;">📚</div>
                <h2>{}</h2>
                <p>总课程数</p>
            </div>
            """.format(len(course_df)), unsafe_allow_html=True)
        
        with col2:
            unique_courses = course_df['课程名'].nunique()
            st.markdown("""
            <div class="stats-card">
                <div style="font-size: 2rem;">📖</div>
                <h2>{}</h2>
                <p>不重复课程</p>
            </div>
            """.format(unique_courses), unsafe_allow_html=True)
        
        with col3:
            unique_classrooms = course_df['教室'].nunique()
            st.markdown("""
            <div class="stats-card">
                <div style="font-size: 2rem;">🏫</div>
                <h2>{}</h2>
                <p>使用教室</p>
            </div>
            """.format(unique_classrooms), unsafe_allow_html=True)
        
        with col4:
            changes = course_df[course_df['调课关键词'] != ['无调课信息']]
            change_count = len(changes)
            st.markdown("""
            <div class="stats-card">
                <div style="font-size: 2rem;">📢</div>
                <h2>{}</h2>
                <p>调课次数</p>
            </div>
            """.format(change_count), unsafe_allow_html=True)
        
        # 详细分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📅 每日课程分布")
            week_dist = course_df['星期'].value_counts().sort_index()
            
            # 按星期顺序排序
            week_order = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
            week_dist = week_dist.reindex([day for day in week_order if day in week_dist.index])
            
            if len(week_dist) > 0:
                st.markdown("**课程分布：**")
                for day, count in week_dist.items():
                    st.write(f"• {day}: {count}节")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🕐 节次分布")
            section_dist = course_df['节次'].value_counts().sort_index()
            
            if len(section_dist) > 0:
                st.markdown("**各节次课程：**")
                for section, count in section_dist.items():
                    time_info = CLASS_TIME_MAP.get(str(section), "")
                    st.write(f"• 第{section}节 ({time_info}): {count}节")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 教室使用情况
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🏫 教室使用频率")
        classroom_dist = course_df['教室'].value_counts().head(10)
        
        if len(classroom_dist) > 0:
            for classroom, count in classroom_dist.items():
                st.write(f"• {classroom}: {count}节")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 准备事项分析
        if '准备项关键词' in course_df.columns:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📋 准备事项统计")
            
            # 统计所有准备关键词
            all_preps = []
            for prep_list in course_df['准备项关键词']:
                if isinstance(prep_list, list):
                    all_preps.extend(prep_list)
            
            if all_preps:
                prep_count = pd.Series(all_preps).value_counts()
                st.markdown("**高频准备事项：**")
                for prep, count in prep_count.head(10).items():
                    st.write(f"• {prep}: {count}次")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()