import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# ------------------------
# ページ設定
# ------------------------

st.set_page_config(page_title="Study Tracker Pro", layout="wide")
st.title("📚 勉強記録トラッカー")

st.info("""
**ℹ️ データの保存について** 
このアプリはサーバーに一切のデータを保存しません。  
終了前に必ずCSVをダウンロードしてください。
再開する場合は、保存したCSVをサイドバーからアップロードして復元してください。
""")

# ------------------------
# データ初期化
# ------------------------

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["date", "subject", "hours"])

# ------------------------
# データ読み込み（サイドバー）
# ------------------------

with st.sidebar:
    st.header("⚙️ データ読み込み")

    uploaded_file = st.file_uploader("CSVのアップロード", type="csv")
    if uploaded_file is not None:
        df_uploaded = pd.read_csv(uploaded_file)
        df_uploaded["date"] = pd.to_datetime(df_uploaded["date"]).dt.date
        st.session_state.data = pd.concat(
            [st.session_state.data, df_uploaded]
        ).drop_duplicates().reset_index(drop=True)
        st.success("読み込み完了！")

    if st.button("データクリア"):
        st.session_state.data = pd.DataFrame(columns=["date", "subject", "hours"])
        st.rerun()

# ------------------------
# 入力エリア
# ------------------------

st.header("📝 記録を追加")
col1, col2, col3 = st.columns(3)

with col1:
    date = st.date_input("日付", datetime.date.today())

with col2:
    subjects = st.session_state.data["subject"].dropna().unique().tolist()
    subject = st.selectbox("科目", subjects + ["新規入力"])
    if subject == "新規入力":
        subject = st.text_input("科目名")

with col3:
    hours = st.number_input("時間", min_value=0.0, step=0.5)

if st.button("追加"):
    if subject and hours > 0:
        new = pd.DataFrame([[date, subject, hours]], columns=["date", "subject", "hours"])
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.success("追加しました")
        st.rerun()
    else:
        st.warning("入力を確認してください")

st.divider()

# ------------------------
# データ表示
# ------------------------

if not st.session_state.data.empty:
    df = st.session_state.data.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # ------------------------
    # 日付フィルタ
    # ------------------------

    st.subheader("📅 日付フィルタ")
    colf1, colf2 = st.columns(2)

    with colf1:
        start = st.date_input("開始日", df["date"].min())
    with colf2:
        end = st.date_input("終了日", df["date"].max())

    df = df[(df["date"] >= start) & (df["date"] <= end)]

    # ------------------------
    # 分析
    # ------------------------

    st.subheader("📊 サマリー")
    m1, m2, m3, m4 = st.columns(4)

    total = df["hours"].sum()
    days = df["date"].nunique()

    m1.metric("総時間", f"{total:.1f} h")
    m2.metric("日数", f"{days}")
    m3.metric("平均/日", f"{(total/days):.1f} h" if days > 0 else "0")

    if not df.empty:
        top_subject = df.groupby("subject")["hours"].sum().idxmax()
        m4.metric("最多科目", top_subject)

    # ------------------------
    # グラフ
    # ------------------------

    tab1, tab2 = st.tabs(["日別", "科目別"])

    with tab1:
        df_daily = df.groupby(["date", "subject"])["hours"].sum().reset_index()
        fig = px.bar(df_daily, x="date", y="hours", color="subject", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_sub = df.groupby("subject")["hours"].sum().reset_index()
        fig2 = px.pie(df_sub, values="hours", names="subject")
        st.plotly_chart(fig2, use_container_width=True)

    # ------------------------
    # 編集・削除
    # ------------------------

    st.subheader("✏️ データ編集・削除")

    df_display = df.reset_index()
    selected = st.selectbox("編集する行を選択", df_display.index)

    row = df_display.loc[selected]

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        new_date = st.date_input("日付変更", row["date"], key="edit_date")
    with col_e2:
        new_subject = st.text_input("科目変更", row["subject"])
    with col_e3:
        new_hours = st.number_input("時間変更", value=float(row["hours"]), step=0.5)

    colb1, colb2 = st.columns(2)

    with colb1:
        if st.button("更新"):
            idx = row["index"]
            st.session_state.data.loc[idx] = [new_date, new_subject, new_hours]
            st.success("更新しました")
            st.rerun()

    with colb2:
        if st.button("削除"):
            idx = row["index"]
            st.session_state.data = st.session_state.data.drop(idx).reset_index(drop=True)
            st.success("削除しました")
            st.rerun()

    # ------------------------
    # 保存
    # ------------------------

    st.subheader("💾 保存")
    csv = st.session_state.data.to_csv(index=False).encode("utf-8")

    st.download_button(
        "CSVダウンロード",
        csv,
        f"study_{datetime.date.today()}.csv",
        "text/csv",
        use_container_width=True
    )

    st.dataframe(st.session_state.data)

else:
    st.info("データを追加してください")