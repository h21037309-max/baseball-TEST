import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid

st.set_page_config(
    page_title="⚾打擊數據系統",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ADMINS=["洪仲平"]

USER_FILE="users.csv"
STATS_FILE="stats.csv"

# ======================
# 初始化資料
# ======================

if not os.path.exists(USER_FILE):

    df=pd.DataFrame([{
        "帳號":"admin",
        "密碼":"admin123",
        "姓名":"洪仲平",
        "球隊":"ADMIN",
        "背號":0
    }])

    df.to_csv(USER_FILE,index=False)

if not os.path.exists(STATS_FILE):

    columns=[
    "紀錄ID","日期","球隊","背號","姓名","對戰球隊",
    "打席","打數","得分","打點","安打",
    "single","double","triple","HR",
    "BB","SF","SH","SB"
    ]

    pd.DataFrame(columns=columns).to_csv(STATS_FILE,index=False)

# 讀取資料
user_df=pd.read_csv(USER_FILE)
df=pd.read_csv(STATS_FILE)

df=df.fillna(0)

# ======================
# 登入 / 註冊
# ======================

mode=st.sidebar.radio("帳號",["登入","註冊"])

if mode=="註冊":

    st.header("建立帳號")

    acc=st.text_input("帳號")
    pw=st.text_input("密碼",type="password")
    real=st.text_input("姓名")
    team=st.text_input("球隊")
    num=st.number_input("背號",0)

    if st.button("建立帳號"):

        if acc in user_df["帳號"].astype(str).values:

            st.error("帳號存在")

        else:

            new=pd.DataFrame([{
                "帳號":acc,
                "密碼":pw,
                "姓名":real.strip(),
                "球隊":team,
                "背號":num
            }])

            user_df=pd.concat([user_df,new],ignore_index=True)

            user_df.to_csv(USER_FILE,index=False)

            st.success("註冊成功")

    st.stop()

# ======================
# 登入
# ======================

username=st.sidebar.text_input("帳號")
password=st.sidebar.text_input("密碼",type="password")

login=user_df[
(user_df["帳號"].astype(str)==username)&
(user_df["密碼"].astype(str)==password)
]

if login.empty:

    st.warning("請登入")
    st.stop()

login_name=str(login.iloc[0]["姓名"]).strip()
team_default=login.iloc[0]["球隊"]
number_default=int(login.iloc[0]["背號"])

IS_ADMIN=login_name in ADMINS

# ======================
# ADMIN球員選擇
# ======================

if IS_ADMIN:

    st.sidebar.markdown("### 👤球員選擇")

    player_list=user_df["姓名"].tolist()

    selected_player=st.sidebar.selectbox(
        "選擇球員",
        player_list
    )

    player_name=selected_player

    info=user_df[user_df["姓名"]==player_name].iloc[0]

    team_default=info["球隊"]
    number_default=int(info["背號"])

else:

    player_name=login_name

# ======================
# 功能選單
# ======================

menu=[
"個人數據",
"新增紀錄",
"單場紀錄",
"聯盟排行榜"
]

if IS_ADMIN:
    menu.append("帳號管理")

page=st.sidebar.radio("功能選單",menu)

# ======================
# 個人數據
# ======================

if page=="個人數據":

    st.header(f"📊 {player_name} 個人累積統計")

    player_df=df[df["姓名"]==player_name]

    if player_df.empty:

        st.info("目前沒有紀錄")

    else:

        total=player_df.sum(numeric_only=True)

        AB=total["打數"]
        H=total["安打"]
        BB=total["BB"]
        SF=total["SF"]

        TB=(
        total["single"]
        +total["double"]*2
        +total["triple"]*3
        +total["HR"]*4
        )

        AVG=round(H/AB,3) if AB>0 else 0
        OBP=round((H+BB)/(AB+BB+SF),3) if (AB+BB+SF)>0 else 0
        SLG=round(TB/AB,3) if AB>0 else 0
        OPS=round(OBP+SLG,3)

        c1,c2,c3,c4,c5,c6=st.columns(6)

        c1.metric("打數",int(total["打數"]))
        c2.metric("安打",int(H))
        c3.metric("AVG",AVG)
        c4.metric("OBP",OBP)
        c5.metric("SLG",SLG)
        c6.metric("OPS",OPS)

# ======================
# 新增紀錄
# ======================

if page=="新增紀錄":

    st.header(f"新增紀錄（{player_name}）")

    game_date=st.date_input("比賽日期",datetime.today())

    c1,c2,c3=st.columns(3)

    with c1:
        opponent=st.text_input("對戰球隊")

    with c2:
        PA=st.number_input("打席",0)
        AB=st.number_input("打數",0)
        R=st.number_input("得分",0)
        RBI=st.number_input("打點",0)

    with c3:
        single=st.number_input("1B",0)
        double=st.number_input("2B",0)
        triple=st.number_input("3B",0)
        HR=st.number_input("HR",0)
        BB=st.number_input("BB",0)
        SF=st.number_input("SF",0)
        SH=st.number_input("SH",0)
        SB=st.number_input("SB",0)

    H=single+double+triple+HR

    if st.button("新增紀錄"):

        new=pd.DataFrame([{
            "紀錄ID":str(uuid.uuid4()),
            "日期":game_date.strftime("%Y-%m-%d"),
            "球隊":team_default,
            "背號":number_default,
            "姓名":player_name,
            "對戰球隊":opponent,
            "打席":PA,
            "打數":AB,
            "得分":R,
            "打點":RBI,
            "安打":H,
            "single":single,
            "double":double,
            "triple":triple,
            "HR":HR,
            "BB":BB,
            "SF":SF,
            "SH":SH,
            "SB":SB
        }])

        df=pd.concat([df,new],ignore_index=True)

        df.to_csv(STATS_FILE,index=False)

        st.success("新增成功")
        st.rerun()

# ======================
# 單場紀錄
# ======================

if page=="單場紀錄":

    st.header("📅 單場紀錄")

    player_df=df[df["姓名"]==player_name]

    for _,row in player_df.sort_values("日期",ascending=False).iterrows():

        st.markdown(f"### 📅 {row['日期']} vs {row['對戰球隊']}")

        c1,c2,c3,c4=st.columns(4)

        c1.metric("打席",int(row["打席"]))
        c2.metric("打數",int(row["打數"]))
        c3.metric("得分",int(row["得分"]))
        c4.metric("打點",int(row["打點"]))

        col1,col2=st.columns(2)

        if col1.button("❌ 刪除",key=row["紀錄ID"]):

            df=df[df["紀錄ID"]!=row["紀錄ID"]]

            df.to_csv(STATS_FILE,index=False)

            st.rerun()

# ======================
# 聯盟排行榜
# ======================

if page=="聯盟排行榜":

    st.header("🏆 聯盟排行榜")

    players = df.groupby(
    ["球隊","背號","姓名"],
    as_index=False
    ).sum(numeric_only=True)

    TB = (
    players["single"]
    + players["double"]*2
    + players["triple"]*3
    + players["HR"]*4
    )

    AB = players["打數"]
    H = players["安打"]
    BB = players["BB"]
    SF = players["SF"]

    players["AVG"]=(H/AB).replace([float("inf")],0).round(3)
    players["OPS"]=((H+BB)/(AB+BB+SF)+TB/AB).replace([float("inf")],0).round(3)

    st.dataframe(players.sort_values("OPS",ascending=False),use_container_width=True)

# ======================
# ADMIN 帳號管理
# ======================

if page=="帳號管理" and IS_ADMIN:

    st.header("帳號管理")

    st.dataframe(user_df,use_container_width=True)

    delete_acc=st.selectbox(
    "選擇刪除帳號",
    user_df["帳號"].tolist()
    )

    if st.button("刪除帳號"):

        if delete_acc!="admin":

            user_df=user_df[user_df["帳號"]!=delete_acc]

            user_df.to_csv(USER_FILE,index=False)

            st.success("帳號已刪除")
            st.rerun()
