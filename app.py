import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid

st.set_page_config(layout="wide")

st.title("⚾打擊數據系統")

DATA_FILE="data.csv"
USER_FILE="users.csv"


ADMINS=["洪仲平","楊振銓","張管理員"]


# ======================
# users 初始化
# ======================

if not os.path.exists(USER_FILE):

    pd.DataFrame([{

    "帳號":"admin",
    "密碼":"admin123",
    "姓名":"洪仲平",
    "球隊":"ADMIN",
    "背號":0

    }]).to_csv(USER_FILE,index=False)


user_df=pd.read_csv(USER_FILE)



# ======================
# 登入 / 註冊
# ======================

mode=st.sidebar.radio("帳號",["登入","註冊"])


# ========= 註冊 =========

if mode=="註冊":

    st.header("建立帳號")

    acc=st.text_input("帳號")

    pw=st.text_input("密碼",type="password")

    real=st.text_input("姓名")

    team=st.text_input("球隊")

    num=st.number_input("背號",0)

    if st.button("建立帳號"):

        if acc in user_df["帳號"].values:

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

            st.success("✅ 註冊成功")

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


login_name=str(login.iloc[0]["姓名"]).strip()

team_default=login.iloc[0]["球隊"]

number_default=int(login.iloc[0]["背號"])

IS_ADMIN=login_name in ADMINS



# ======================
# CSV
# ======================

columns=[

"紀錄ID","日期","球隊","背號","姓名",
"對戰球隊","投手",
"打席","打數","得分","打點","安打",
"1B","2B","3B","HR",
"BB","SF","SH","SB"

]

if os.path.exists(DATA_FILE):

    df=pd.read_csv(DATA_FILE)

else:

    df=pd.DataFrame(columns=columns)


for c in columns:

    if c not in df.columns:

        df[c]=0

df["姓名"]=df["姓名"].astype(str).str.strip()

df=df.fillna(0)



# ======================
# ADMIN 球員中心
# ======================

if IS_ADMIN:

    st.header("🏆 球員管理中心")

    select_player=st.selectbox(

    "選擇球員",

    user_df["姓名"]

    )

    info=user_df[user_df["姓名"]==select_player].iloc[0]

    player_name=select_player

    team_default=info["球隊"]

    number_default=int(info["背號"])



    # ⭐ 全部球員排行榜

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


        summary["打擊率"]=(summary["安打"]/summary["打數"]).round(3).fillna(0)

        summary["上壘率"]=(
        (summary["安打"]+summary["BB"])/
        (summary["打數"]+summary["BB"]+summary["SF"])
        ).round(3).fillna(0)

        summary["長打率"]=(TB/summary["打數"]).round(3).fillna(0)

        summary["OPS"]=(
        summary["上壘率"]+summary["長打率"]
        ).round(3)


        st.dataframe(

        summary.sort_values("OPS",ascending=False),

        use_container_width=True)

else:

    player_name=login_name



# ======================
# 個人累積統計
# ======================

st.header("📊 個人累積統計")

player_df=df[df["姓名"]==player_name]


if player_df.empty:

    st.info("尚無資料")

else:

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

c1,c2,c3=st.columns(3)

with c1:

    opponent=st.text_input("對戰球隊")

    pitcher=st.selectbox("投手",["左投","右投"])

with c2:

    PA=st.number_input("打席",0)

    AB=st.number_input("打數",0)

    R=st.number_input("得分",0)

    RBI=st.number_input("打點",0)

    H=st.number_input("安打",0)

with c3:

    single=st.number_input("1B",0)

    double=st.number_input("2B",0)

    triple=st.number_input("3B",0)

    HR=st.number_input("HR",0)

    BB=st.number_input("BB",0)

    SF=st.number_input("SF",0)

    SH=st.number_input("SH",0)

    SB=st.number_input("SB",0)



if st.button("新增紀錄"):

    new=pd.DataFrame([{

    "紀錄ID":str(uuid.uuid4()),

    "日期":datetime.now().strftime("%Y-%m-%d"),

    "球隊":team_default,

    "背號":number_default,

    "姓名":player_name,

    "對戰球隊":opponent,

    "投手":pitcher,

    "打席":PA,
    "打數":AB,
    "得分":R,
    "打點":RBI,
    "安打":H,

    "1B":single,
    "2B":double,
    "3B":triple,
    "HR":HR,

    "BB":BB,
    "SF":SF,
    "SH":SH,
    "SB":SB

    }])

    df=pd.concat([df,new],ignore_index=True)

    df.to_csv(DATA_FILE,index=False)

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

vs {row['對戰球隊']} ｜ {row['投手']}

PA {int(row['打席'])} ｜ AB {int(row['打數'])} ｜ H {int(row['安打'])}

1B {int(row['1B'])} ｜ 2B {int(row['2B'])} ｜ 3B {int(row['3B'])} ｜ HR {int(row['HR'])}

BB {int(row['BB'])} ｜ SF {int(row['SF'])} ｜ SH {int(row['SH'])} ｜ SB {int(row['SB'])}

---
""")

    with colB:

        if st.button("❌",key=row["紀錄ID"]):

            df=df[df["紀錄ID"]!=row["紀錄ID"]]

            df.to_csv(DATA_FILE,index=False)

            st.rerun()



# ======================
# ADMIN 帳號管理
# ======================

if IS_ADMIN:

    st.divider()

    st.header("👤 帳號管理")

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

            delete_name=user_df[
            user_df["帳號"]==delete_acc
            ].iloc[0]["姓名"]

            user_df=user_df[
            user_df["帳號"]!=delete_acc
            ]

            user_df.to_csv(USER_FILE,index=False)

            df=df[df["姓名"]!=delete_name]

            df.to_csv(DATA_FILE,index=False)

            st.success("帳號與全部紀錄已刪除")

            st.rerun()
