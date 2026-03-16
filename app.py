import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import uuid

st.set_page_config(layout="wide")

st.title("⚾打擊數據系統")

ADMINS=["洪仲平"]

# ======================
# SQLite資料庫
# ======================

conn = sqlite3.connect("database.db",check_same_thread=False,timeout=30)
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
安打 INTEGER,
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
# admin初始化
# ======================

cursor.execute("SELECT * FROM users WHERE 帳號='admin'")
if cursor.fetchone() is None:

    cursor.execute(
    "INSERT INTO users VALUES (?,?,?,?,?)",
    ("admin","admin123","洪仲平","ADMIN",0)
    )

    conn.commit()

user_df=pd.read_sql("SELECT * FROM users",conn)

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

            cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (acc,pw,real.strip(),team,num)
            )

            conn.commit()

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
# 功能選單
# ======================

page=st.sidebar.radio(
"功能選單",
[
"個人數據",
"新增紀錄",
"單場紀錄",
"聯盟排行榜"
]
)

# ======================
# 讀取數據
# ======================

df=pd.read_sql("SELECT * FROM stats",conn)
df=df.fillna(0)

# ======================
# 個人數據
# ======================

if page=="個人數據":

    st.header("📊 個人累積統計")

    player_df=df[df["姓名"]==login_name]

    if player_df.empty:

        st.info("目前沒有任何比賽紀錄")

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

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;background:#f8f9fa;padding:15px;border-radius:10px">

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">打數</div>
        <div style="font-size:26px;font-weight:700">{int(total["打數"])}</div>
        </div>

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">安打</div>
        <div style="font-size:26px;font-weight:700">{int(H)}</div>
        </div>

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">打擊率</div>
        <div style="font-size:26px;font-weight:700">{AVG}</div>
        </div>

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">上壘率</div>
        <div style="font-size:26px;font-weight:700">{OBP}</div>
        </div>

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">長打率</div>
        <div style="font-size:26px;font-weight:700">{SLG}</div>
        </div>

        <div style="flex:1;text-align:center">
        <div style="font-size:12px;color:#666">OPS</div>
        <div style="font-size:26px;font-weight:700">{OPS}</div>
        </div>

        </div>
        """,unsafe_allow_html=True)

        # 打擊細項
        st.subheader("打擊細項")

        col1,col2,col3,col4,col5,col6,col7=st.columns(7)

        col1.metric("1B",int(total["single"]))
        col2.metric("2B",int(total["double"]))
        col3.metric("3B",int(total["triple"]))
        col4.metric("HR",int(total["HR"]))
        col5.metric("RBI",int(total["打點"]))
        col6.metric("BB",int(total["BB"]))
        col7.metric("SB",int(total["SB"]))

        # 安打分布圖
        st.subheader("安打分布")

        chart=pd.DataFrame({
        "Hit":["1B","2B","3B","HR"],
        "Count":[
        total["single"],
        total["double"],
        total["triple"],
        total["HR"]
        ]
        })

        st.bar_chart(chart.set_index("Hit"))

        # 最近10場
        st.subheader("最近10場")

        recent=player_df.sort_values("日期",ascending=False).head(10)

        st.dataframe(
        recent[[
        "日期","對戰球隊","打數","安打","HR","打點"
        ]],
        use_container_width=True
        )

        # 生涯紀錄
        st.subheader("生涯紀錄")

        st.write("單場最多安打：",player_df["安打"].max())
        st.write("單場最多全壘打：",player_df["HR"].max())
        st.write("單場最多打點：",player_df["打點"].max())

# ======================
# 新增紀錄
# ======================

if page=="新增紀錄":

    st.header("新增比賽紀錄")

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

        cursor.execute("""
        INSERT INTO stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
        str(uuid.uuid4()),
        game_date.strftime("%Y-%m-%d"),
        team_default,
        number_default,
        login_name,
        opponent,
        PA,
        AB,
        R,
        RBI,
        H,
        single,
        double,
        triple,
        HR,
        BB,
        SF,
        SH,
        SB
        ))

        conn.commit()

        st.success("新增成功")
        st.rerun()
