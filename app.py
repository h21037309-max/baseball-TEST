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
# 讀取數據
# ======================

df=pd.read_sql("SELECT * FROM stats",conn)
df=df.fillna(0)

# ======================
# 個人數據
# ======================

if page=="個人數據":

    st.header(f"📊 {player_name} 個人累積統計")

    player_df=df[df["姓名"]==player_name]

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

        col1,col2,col3,col4,col5,col6=st.columns(6)

        col1.metric("打數",int(total["打數"]))
        col2.metric("安打",int(H))
        col3.metric("打擊率",AVG)
        col4.metric("上壘率",OBP)
        col5.metric("長打率",SLG)
        col6.metric("OPS",OPS)

        st.subheader("打擊細項")

        c1,c2,c3,c4,c5,c6,c7=st.columns(7)

        c1.metric("1B",int(total["single"]))
        c2.metric("2B",int(total["double"]))
        c3.metric("3B",int(total["triple"]))
        c4.metric("HR",int(total["HR"]))
        c5.metric("RBI",int(total["打點"]))
        c6.metric("BB",int(total["BB"]))
        c7.metric("SB",int(total["SB"]))

# ======================
# 新增紀錄
# ======================

if page=="新增紀錄":

    st.header(f"新增比賽紀錄（{player_name}）")

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

if page=="單場紀錄":

    st.header("📅 單場比賽紀錄")

    player_df=df[df["姓名"]==login_name]

    for _,row in player_df.sort_values("日期",ascending=False).iterrows():

        # 上方數據
        st.markdown(f"""
### {row['日期']} vs {row['對戰球隊']}

AB {row['打數']} ｜ H {row['安打']} ｜ HR {row['HR']} ｜ RBI {row['打點']}
""")

        # 下方操作按鈕（橫向）
        col1,col2=st.columns(2)

        with col1:
            if st.button("✏️ 修改",key="edit"+row["紀錄ID"]):
                st.session_state["edit_id"]=row["紀錄ID"]

        with col2:
            if st.button("❌ 刪除",key=row["紀錄ID"]):

                cursor.execute(
                "DELETE FROM stats WHERE 紀錄ID=?",
                (row["紀錄ID"],)
                )

                conn.commit()

                st.success("紀錄已刪除")

                st.rerun()

        st.divider()

# ======================
# 修改紀錄
# ======================

if "edit_id" in st.session_state:

    edit_id=st.session_state["edit_id"]

    edit_row=df[df["紀錄ID"]==edit_id].iloc[0]

    st.subheader("✏️ 修改紀錄")

    AB=st.number_input("打數",value=int(edit_row["打數"]))
    H=st.number_input("安打",value=int(edit_row["安打"]))
    HR=st.number_input("HR",value=int(edit_row["HR"]))
    RBI=st.number_input("打點",value=int(edit_row["打點"]))

    if st.button("儲存修改"):

        cursor.execute("""
        UPDATE stats
        SET 打數=?,安打=?,HR=?,打點=?
        WHERE 紀錄ID=?
        """,(AB,H,HR,RBI,edit_id))

        conn.commit()

        del st.session_state["edit_id"]

        st.success("修改完成")

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

    players["AVG"] = (H/AB).replace([float("inf")],0).round(3)
    players["OPS"] = ((H+BB)/(AB+BB+SF) + TB/AB).replace([float("inf")],0).round(3)

    st.dataframe(players.sort_values("OPS",ascending=False),use_container_width=True)

# ======================
# ADMIN 帳號管理
# ======================

if IS_ADMIN:

    st.divider()

    st.header("帳號管理")

    st.dataframe(
        user_df[["帳號","姓名","球隊","背號"]],
        use_container_width=True
    )

    delete_acc=st.selectbox(
        "選擇刪除帳號",
        user_df["帳號"].tolist()
    )

    if st.button("刪除帳號"):

        if delete_acc!="admin":

            delete_name=user_df[
                user_df["帳號"]==delete_acc
            ].iloc[0]["姓名"]

            cursor.execute(
            "DELETE FROM users WHERE 帳號=?",
            (delete_acc,)
            )

            cursor.execute(
            "DELETE FROM stats WHERE 姓名=?",
            (delete_name,)
            )

            conn.commit()

            st.success("帳號與數據已刪除")
            st.rerun()
