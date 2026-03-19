import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import uuid

st.set_page_config(layout="wide")

st.title("⚾ 打擊數據系統")

ADMINS=["洪仲平"]

# ======================
# SQLite資料庫
# ======================

conn = sqlite3.connect("database.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
帳號 TEXT PRIMARY KEY,
密碼 TEXT,
姓名 TEXT,
球隊 TEXT,
背號 INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats(
紀錄ID TEXT PRIMARY KEY,
日期 TEXT,
球隊 TEXT,
背號 INTEGER,
姓名 TEXT,
對戰球隊 TEXT,
打席 INTEGER,
打數 INTEGER,
得分 INTEGER,
打點 INTEGER,
single INTEGER,
double INTEGER,
triple INTEGER,
HR INTEGER,
BB INTEGER,
SF INTEGER,
SH INTEGER,
SB INTEGER
)
""")

conn.commit()

# ======================
# 初始化 admin
# ======================

cursor.execute("SELECT * FROM users WHERE 帳號='admin'")

if cursor.fetchone() is None:

    cursor.execute(
    "INSERT INTO users VALUES (?,?,?,?,?)",
    ("admin","admin123","洪仲平","ADMIN",0)
    )

    conn.commit()

# ======================
# 讀取資料
# ======================

user_df=pd.read_sql("SELECT * FROM users",conn)
df=pd.read_sql("SELECT * FROM stats",conn)

df=df.fillna(0)

# ======================
# 註冊 / 登入
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

        if acc in user_df["帳號"].values:

            st.error("帳號已存在")

        else:

            cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (acc,pw,real,team,num)
            )

            conn.commit()

            st.success("註冊成功")

            st.rerun()

    st.stop()

# ======================
# 登入
# ======================

username=st.sidebar.text_input("帳號")
password=st.sidebar.text_input("密碼",type="password")

login=user_df[
(user_df["帳號"]==username)&
(user_df["密碼"]==password)
]

if login.empty:

    st.warning("請登入")
    st.stop()

login_name=login.iloc[0]["姓名"]
team_default=login.iloc[0]["球隊"]
number_default=int(login.iloc[0]["背號"])

IS_ADMIN=login_name in ADMINS

# ======================
# ADMIN 選球員
# ======================

if IS_ADMIN:

    player_list=user_df["姓名"].tolist()

    player_name=st.sidebar.selectbox("選擇球員",player_list)

    info=user_df[user_df["姓名"]==player_name].iloc[0]

    team_default=info["球隊"]
    number_default=int(info["背號"])

else:

    player_name=login_name

# ======================
# 功能選單
# ======================

menu=["個人數據","新增紀錄","單場紀錄","聯盟排行榜"]

if IS_ADMIN:
    menu.append("帳號管理")

page=st.sidebar.radio("功能選單",menu)

# ======================
# 個人數據
# ======================

if page=="個人數據":

    st.header(f"📊 {player_name} 個人數據")

    player_df=df[df["姓名"]==player_name]

    if player_df.empty:

        st.info("目前沒有紀錄")

    else:

        total=player_df.sum(numeric_only=True)

        H=(
        total["single"]
        +total["double"]
        +total["triple"]
        +total["HR"]
        )

        AB=total["打數"]

        TB=(
        total["single"]
        +total["double"]*2
        +total["triple"]*3
        +total["HR"]*4
        )

        AVG=round(H/AB,3) if AB>0 else 0

        OPS=round(
        (H+total["BB"])/(AB+total["BB"]+total["SF"])
        +
        TB/AB
        ,3) if AB>0 else 0

        c1,c2,c3,c4=st.columns(4)

        c1.metric("打數",int(AB))
        c2.metric("安打",int(H))
        c3.metric("AVG",AVG)
        c4.metric("OPS",OPS)

# ======================
# 新增紀錄
# ======================

if page=="新增紀錄":

    st.header(f"新增紀錄（{player_name}）")

    game_date=st.date_input("比賽日期",datetime.today())
    opponent=st.text_input("對戰球隊")

    c1,c2,c3=st.columns(3)

    with c1:
        PA=int(st.number_input("打席",0))
        AB=int(st.number_input("打數",0))
        R=int(st.number_input("得分",0))
        RBI=int(st.number_input("打點",0))

    with c2:
        single=int(st.number_input("1B",0))
        double=int(st.number_input("2B",0))
        triple=int(st.number_input("3B",0))
        HR=int(st.number_input("HR",0))

    with c3:
        BB=int(st.number_input("BB",0))
        SF=int(st.number_input("SF",0))
        SH=int(st.number_input("SH",0))
        SB=int(st.number_input("SB",0))

    if st.button("新增紀錄"):

        cursor.execute("""
        INSERT INTO stats(
        紀錄ID,日期,球隊,背號,姓名,對戰球隊,
        打席,打數,得分,打點,
        single,double,triple,HR,
        BB,SF,SH,SB
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
        str(uuid.uuid4()),
        game_date.strftime("%Y-%m-%d"),
        team_default,
        number_default,
        player_name,
        opponent,
        PA,AB,R,RBI,
        single,double,triple,HR,
        BB,SF,SH,SB
        ))

        conn.commit()

        st.success("新增成功")

        st.rerun()

# ======================
# 單場紀錄
# ======================

if page=="單場紀錄":

    st.header("📅 單場紀錄")

    player_df=df[df["姓名"]==player_name]

    for _,row in player_df.sort_values("日期",ascending=False).iterrows():

        st.markdown(f"### {row['日期']} vs {row['對戰球隊']}")

        c1,c2,c3,c4=st.columns(4)

        c1.metric("打數",int(row["打數"]))
        c2.metric("HR",int(row["HR"]))
        c3.metric("打點",int(row["打點"]))
        c4.metric("BB",int(row["BB"]))

        col1,col2=st.columns(2)

        if col1.button("✏ 修改",key="edit"+row["紀錄ID"]):

            st.session_state["edit_id"]=row["紀錄ID"]

        if col2.button("❌ 刪除",key="del"+row["紀錄ID"]):

            cursor.execute(
            "DELETE FROM stats WHERE 紀錄ID=?",
            (row["紀錄ID"],)
            )

            conn.commit()

            st.rerun()

        st.divider()

# ======================
# 聯盟排行榜
# ======================

if page=="聯盟排行榜":

    st.header("🏆 聯盟排行榜")

    players=df.groupby(
    ["球隊","背號","姓名"],
    as_index=False
    ).sum(numeric_only=True)

    players["H"]=(
    players["single"]
    +players["double"]
    +players["triple"]
    +players["HR"]
    )

    players["AVG"]=(players["H"]/players["打數"]).replace([float("inf")],0).round(3)

    st.dataframe(players.sort_values("AVG",ascending=False),use_container_width=True)

# ======================
# 帳號管理
# ======================

if page=="帳號管理" and IS_ADMIN:

    st.header("帳號管理")

    st.dataframe(user_df)

    delete_acc=st.selectbox("刪除帳號",user_df["帳號"])

    if st.button("刪除帳號"):

        cursor.execute(
        "DELETE FROM users WHERE 帳號=?",
        (delete_acc,)
        )

        conn.commit()

        st.success("刪除成功")

        st.rerun()
