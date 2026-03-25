import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from supabase import create_client

st.set_page_config(layout="wide")
st.title("⚾ 打擊數據系統（雲端版）")

ADMINS=["洪仲平"]

# ======================
# 🔥 Supabase設定（已幫你放好）
# ======================

SUPABASE_URL = "https://tovsoxvpcfupjnhtdrzz.supabase.co"
SUPABASE_KEY = "sb_publishable_IFsfZ5zlOtGv8F5eU11kpw_uCHZA93d"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# 讀取資料
# ======================

user_df = pd.DataFrame(supabase.table("users").select("*").execute().data)
df = pd.DataFrame(supabase.table("stats").select("*").execute().data)

if not df.empty:
    df = df.fillna(0)

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

        supabase.table("users").insert({
            "帳號":acc,
            "密碼":pw,
            "姓名":real,
            "球隊":team,
            "背號":int(num)
        }).execute()

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

        H=(total["single"]+total["double"]+total["triple"]+total["HR"])
        AB=total["打數"]

        AVG=round(H/AB,3) if AB>0 else 0

        c1,c2,c3=st.columns(3)
        c1.metric("打數",int(AB))
        c2.metric("安打",int(H))
        c3.metric("AVG",AVG)

# ======================
# 新增紀錄
# ======================

if page=="新增紀錄":

    st.header(f"新增紀錄（{player_name}）")

    game_date=st.date_input("比賽日期",datetime.today())
    opponent=st.text_input("對戰球隊")

    AB=int(st.number_input("打數",0))
    single=int(st.number_input("1B",0))
    double=int(st.number_input("2B",0))
    triple=int(st.number_input("3B",0))
    HR=int(st.number_input("HR",0))
    BB=int(st.number_input("BB",0))
    SF=int(st.number_input("SF",0))

    if st.button("新增紀錄"):

        supabase.table("stats").insert({
            "紀錄ID":str(uuid.uuid4()),
            "日期":game_date.strftime("%Y-%m-%d"),
            "球隊":team_default,
            "背號":number_default,
            "姓名":player_name,
            "對戰球隊":opponent,
            "打數":AB,
            "single":single,
            "double":double,
            "triple":triple,
            "HR":HR,
            "BB":BB,
            "SF":SF
        }).execute()

        st.success("新增成功")
        st.rerun()

# ======================
# 單場紀錄
# ======================

if page=="單場紀錄":

    st.header("📅 單場紀錄")

    player_df=df[df["姓名"]==player_name]

    for _,row in player_df.iterrows():

        st.markdown(f"{row['日期']} vs {row['對戰球隊']}")

        col1,col2=st.columns(2)

        if col1.button("刪除",key=row["紀錄ID"]):

            supabase.table("stats").delete().eq("紀錄ID",row["紀錄ID"]).execute()
            st.rerun()

# ======================
# 聯盟排行榜
# ======================

if page=="聯盟排行榜":

    st.header("🏆 聯盟排行榜")

    players=df.groupby(["姓名"],as_index=False).sum(numeric_only=True)

    players["H"]=(players["single"]+players["double"]+players["triple"]+players["HR"])
    players["AVG"]=(players["H"]/players["打數"]).replace([float("inf")],0).round(3)

    st.dataframe(players.sort_values("AVG",ascending=False))

# ======================
# 帳號管理
# ======================

if page=="帳號管理" and IS_ADMIN:

    st.header("帳號管理")

    st.dataframe(user_df)

    delete_acc=st.selectbox("刪除帳號",user_df["帳號"])

    if st.button("刪除帳號"):

        supabase.table("users").delete().eq("帳號",delete_acc).execute()

        st.success("刪除成功")
        st.rerun()
