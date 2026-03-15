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

conn = sqlite3.connect("database.db", check_same_thread=False)
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
1B INTEGER,
2B INTEGER,
3B INTEGER,
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

        cursor.execute(
        "SELECT * FROM users WHERE 帳號=?",(acc,)
        )

        if cursor.fetchone():

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

cursor.execute(
"SELECT * FROM users WHERE 帳號=? AND 密碼=?",
(username,password)
)

login=cursor.fetchone()

if not login:

    st.warning("請登入")
    st.stop()

login_name=login[2]
team_default=login[3]
number_default=login[4]

IS_ADMIN=login_name in ADMINS

# ======================
# 讀取數據
# ======================

df=pd.read_sql("SELECT * FROM stats",conn)

# ======================
# ADMIN球員中心
# ======================

if IS_ADMIN:

    st.header("🏆 球員管理中心")

    user_df=pd.read_sql("SELECT * FROM users",conn)

    user_df["顯示"]=user_df["帳號"]+"｜"+user_df["姓名"]

    select_player=st.selectbox(
    "選擇球員",
    user_df["顯示"]
    )

    select_acc=select_player.split("｜")[0]

    info=user_df[user_df["帳號"]==select_acc].iloc[0]

    player_name=info["姓名"]
    team_default=info["球隊"]
    number_default=int(info["背號"])

    if not df.empty:

        st.subheader("📊 全部球員累積排行榜")

        summary=df.groupby(
        ["球隊","背號","姓名"],
        as_index=False
        ).sum(numeric_only=True)

        TB=(
        summary["1B"]
        +summary["2B"]*2
        +summary["3B"]*3
        +summary["HR"]*4
        )

        AB=summary["打數"]
        H=summary["安打"]
        BB=summary["BB"]
        SF=summary["SF"]

        summary["打擊率"]=(H/AB).round(3).fillna(0)

        summary["上壘率"]=(
        (H+BB)/(AB+BB+SF)
        ).round(3).fillna(0)

        summary["長打率"]=(TB/AB).round(3).fillna(0)

        summary["OPS"]=(
        summary["上壘率"]+
        summary["長打率"]
        ).round(3)

        st.dataframe(
        summary.sort_values("OPS",ascending=False),
        use_container_width=True
        )

else:

    player_name=login_name

# ======================
# 個人累積
# ======================

st.header("📊 個人累積統計")

player_df=df[df["姓名"]==player_name]

if not player_df.empty:

    total=player_df.sum(numeric_only=True)

    AB=total["打數"]
    H=total["安打"]
    BB=total["BB"]
    SF=total["SF"]

    TB=(
    total["1B"]
    +total["2B"]*2
    +total["3B"]*3
    +total["HR"]*4
    )

    AVG=round(H/AB,3) if AB>0 else 0
    OBP=round((H+BB)/(AB+BB+SF),3) if (AB+BB+SF)>0 else 0
    SLG=round(TB/AB,3) if AB>0 else 0
    OPS=round(OBP+SLG,3)

    c1,c2,c3,c4,c5,c6=st.columns(6)

    c1.metric("打席",int(total["打席"]))
    c2.metric("安打",int(H))
    c3.metric("打擊率",AVG)
    c4.metric("上壘率",OBP)
    c5.metric("長打率",SLG)
    c6.metric("OPS",OPS)

# ======================
# 新增紀錄
# ======================

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
    player_name,
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

# ======================
# 單場紀錄
# ======================

st.header("📅 單場比賽紀錄")

for _,row in player_df.sort_values("日期",ascending=False).iterrows():

    colA,colB=st.columns([9,1])

    with colA:

        st.markdown(f"""
### 📅 {row['日期']} ｜ {row['球隊']} #{int(row['背號'])} {row['姓名']}
vs {row['對戰球隊']}
PA {int(row['打席'])} ｜ AB {int(row['打數'])} ｜ H {int(row['安打'])}
1B {int(row['1B'])} ｜ 2B {int(row['2B'])} ｜ 3B {int(row['3B'])} ｜ HR {int(row['HR'])}
BB {int(row['BB'])} ｜ SF {int(row['SF'])} ｜ SH {int(row['SH'])} ｜ SB {int(row['SB'])}
---
""")

    with colB:

        if st.button("❌",key=row["紀錄ID"]):

            cursor.execute(
            "DELETE FROM stats WHERE 紀錄ID=?",
            (row["紀錄ID"],)
            )

            conn.commit()

            st.rerun()

# ======================
# 帳號管理
# ======================

if IS_ADMIN:

    st.divider()

    st.header("👤 帳號管理")

    user_df=pd.read_sql("SELECT * FROM users",conn)

    st.dataframe(
    user_df[["帳號","姓名","球隊","背號"]],
    use_container_width=True
    )

    delete_acc=st.selectbox(
    "選擇刪除帳號",
    user_df["帳號"]
    )

    if st.button("❌ 刪除帳號"):

        if delete_acc!="admin":

            cursor.execute(
            "SELECT 姓名 FROM users WHERE 帳號=?",
            (delete_acc,)
            )

            delete_name=cursor.fetchone()[0]

            cursor.execute(
            "DELETE FROM users WHERE 帳號=?",
            (delete_acc,)
            )

            cursor.execute(
            "DELETE FROM stats WHERE 姓名=?",
            (delete_name,)
            )

            conn.commit()

            st.success("帳號與紀錄已刪除")

            st.rerun()

        else:

            st.warning("admin帳號不可刪除")
