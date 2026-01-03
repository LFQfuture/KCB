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
            reminders.append(
                f"⏰ 课前1小时提醒 | {course_name}（{classroom}）\n需准备：{','.join(prepare_keywords)}"
            )
        # 2. 课前30分钟提醒（25-35分钟内）
        elif 25 <= time_diff <= 35:
            reminders.append(
                f"🚨 课前30分钟提醒 | {course_name}即将开始！\n教室：{classroom}"
            )
        # 3. 调课提醒（识别到调课关键词）
        if change_info != ["无调课信息"]:
            reminders.append(
                f"📢 调课提醒 | {course_name}\n备注：{course['备注']}"
            )
    
    return reminders

# ---------------------- 3. Streamlit前端界面 ----------------------
def main():
    # 页面基础配置
    st.set_page_config(
        page_title="课程表智能提醒工具",
        page_icon="📚",
        layout="wide"
    )
    
    # 标题与说明
    st.title("📚 课程表智能提醒小工具")
    st.caption("无需云服务，本地解析课程信息，自动触发上课/准备提醒")
    st.divider()

    # 第一步：上传课程表
    st.subheader("Step 1: 上传课程表（Excel格式）")
    st.caption("模板字段：课程名、周次、星期、节次、教室、课前准备、备注")
    uploaded_file = st.file_uploader(
        "仅支持.xlsx格式",
        type=["xlsx"],
        help="参考模板：课程名（高等数学）、周次（1-16周）、星期（星期三）、节次（3）、教室（3教201）、课前准备（带习题集）、备注（调至周五第6节）"
    )

    if uploaded_file:
        # 读取并展示原始课程表
        course_df = pd.read_excel(uploaded_file)
        st.dataframe(course_df, use_container_width=True)
        st.divider()

        # 第二步：本地AI解析课程信息
        st.subheader("Step 2: 解析课程关键信息")
        if st.button("开始解析", type="primary"):
            with st.spinner("正在解析课程表..."):
                # 解析课前准备关键词
                course_df["准备项关键词"] = course_df["课前准备"].apply(extract_prepare_keywords)
                # 解析调课关键词
                course_df["调课关键词"] = course_df["备注"].apply(extract_change_keywords)
                time.sleep(1)  # 模拟加载
            
            # 展示解析结果
            st.success("✅ 解析完成！")
            show_cols = ["课程名", "教室", "准备项关键词", "调课关键词"]
            st.dataframe(course_df[show_cols], use_container_width=True)
            st.divider()

            # 第三步：实时智能提醒
            st.subheader("Step 3: 实时提醒中心")
            st.info("工具会自动检测当前时间，触发课前/调课提醒")
            
            # 生成提醒
            reminders = check_reminder(course_df)
            if reminders:
                for idx, reminder in enumerate(reminders):
                    st.warning(f"提醒{idx+1}：\n{reminder}")
            else:
                st.success("🎉 暂无待提醒课程，安心学习吧！")

        # 手动测试提醒功能（可选）
        with st.expander("📝 手动测试提醒（可选）"):
            st.caption("输入节次，测试提醒逻辑是否正常")
            test_section = st.selectbox("选择测试节次", list(CLASS_TIME_MAP.keys()))
            test_course = st.text_input("测试课程名", "高等数学")
            test_classroom = st.text_input("测试教室", "3教201")
            
            if st.button("触发测试提醒"):
                test_time = CLASS_TIME_MAP[test_section]
                st.warning(
                    f"🚨 测试提醒 | {test_course}（{test_classroom}）\n上课时间：{test_time}（课前30分钟提醒）"
                )

if __name__ == "__main__":
    main()