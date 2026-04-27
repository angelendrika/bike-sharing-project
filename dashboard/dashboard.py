import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set style seaborn
sns.set(style='dark')

# --- Helper Functions ---
def get_total_count_by_hour_df(hour_df):
    hour_count_df = hour_df.groupby(by="hours").agg({"count_cr": "sum"}).reset_index()
    return hour_count_df

def count_by_day_df(day_df):
    return day_df

def total_registered_df(day_df):
    reg_df = day_df.groupby(by="dteday").agg({"registered": "sum"}).reset_index()
    reg_df.rename(columns={"registered": "register_sum"}, inplace=True)
    return reg_df

def total_casual_df(day_df):
    cas_df = day_df.groupby(by="dteday").agg({"casual": "sum"}).reset_index()
    cas_df.rename(columns={"casual": "casual_sum"}, inplace=True)
    return cas_df

def sum_order(hour_df):
    sum_order_items_df = hour_df.groupby("hours").count_cr.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def macem_season(day_df): 
    season_df = day_df.groupby(by="season").count_cr.sum().reset_index() 
    return season_df

def create_rfm_recap(hour_df):
    rfm_df = hour_df.groupby(by="hours", as_index=False).agg({
        "dteday": "max",
        "instant": "nunique",
        "count_cr": "sum"
    })
    rfm_df.columns = ["hours", "last_order_date", "order_count", "revenue"]
    rfm_df["last_order_date"] = pd.to_datetime(rfm_df["last_order_date"]).dt.date
    recent_date = pd.to_datetime(hour_df["dteday"]).dt.date.max()
    rfm_df["recency"] = rfm_df["last_order_date"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("last_order_date", axis=1, inplace=True)
    return rfm_df

# --- Load Data ---
# Pastikan file csv berada di folder yang benar
days_df = pd.read_csv("dashboard/day_clean.csv")
hours_df = pd.read_csv("dashboard/hour_clean.csv")

datetime_columns = ["dteday"]
for column in datetime_columns:
    days_df[column] = pd.to_datetime(days_df[column])
    hours_df[column] = pd.to_datetime(hours_df[column])

# --- Sidebar ---
min_date = days_df["dteday"].min()
max_date = days_df["dteday"].max()

with st.sidebar:
    st.image("https://storage.googleapis.com/gweb-uniblog-publish-prod/original_images/image1_hH9B4gs.jpg")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# --- Main Data Filtering ---
main_df_days = days_df[(days_df["dteday"] >= pd.to_datetime(start_date)) & 
                       (days_df["dteday"] <= pd.to_datetime(end_date))]

main_df_hour = hours_df[(hours_df["dteday"] >= pd.to_datetime(start_date)) & 
                        (hours_df["dteday"] <= pd.to_datetime(end_date))]

# Get Data Recaps
day_df_recap = count_by_day_df(main_df_days)
reg_df = total_registered_df(main_df_days)
cas_df = total_casual_df(main_df_days)
sum_order_items_df = sum_order(main_df_hour)
season_df = macem_season(main_df_days)
rfm_recap_df = create_rfm_recap(main_df_hour)

# --- Dashboard Layout ---
st.header('Bike Sharing Analytics Dashboard :sparkles:')

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Sharing Bike", value=f"{day_df_recap.count_cr.sum():,}")
with col2:
    st.metric("Total Registered", value=f"{reg_df.register_sum.sum():,}")
with col3:
    st.metric("Total Casual", value=f"{cas_df.casual_sum.sum():,}")

# --- Visualisasi 1: Tren Bulanan ---
st.subheader("Tren Pertumbuhan Total Penyewaan Sepeda (2011-2012)")
# Resample bulanan sesuai notebook
monthly_trend_df = main_df_days.resample(rule='ME', on='dteday').agg({"count_cr": "sum"}).reset_index()

fig, ax = plt.subplots(figsize=(15, 6))
ax.plot(
    monthly_trend_df['dteday'],
    monthly_trend_df['count_cr'],
    marker='o',
    linewidth=2,
    color="#005461"
)
ax.set_title("Tren Pertumbuhan Total Penyewaan Sepeda (2011-2012)", fontsize=18)
ax.set_xlabel("Tahun & Bulan", fontsize=12)
ax.set_ylabel("Total Penyewaan", fontsize=12)
ax.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig)

# --- Visualisasi 2: Jam Puncak & Terendah ---
st.subheader("Puncak dan Titik Terendah Permintaan Sewa Sepeda Berdasarkan Jam")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(30, 12))

# Jam Terbanyak
sns.barplot(
    x="hours", 
    y="count_cr", 
    data=sum_order_items_df.head(5),
    hue="hours",
    palette=["#D3D3D3", "#D3D3D3", "#005461", "#D3D3D3", "#D3D3D3"],
    legend=False,
    ax=ax[0]
)
ax[0].set_ylabel("Total Penyewaan", fontsize=20)
ax[0].set_xlabel("Jam (PM)", fontsize=25)
ax[0].set_title("Jam dengan Penyewa Terbanyak", fontsize=30)
ax[0].tick_params(axis='both', labelsize=20)

# Jam Terendah
sns.barplot(
    x="hours", 
    y="count_cr", 
    data=sum_order_items_df.sort_values(by="count_cr", ascending=True).head(5),
    hue="hours",
    palette=["#D3D3D3", "#D3D3D3", "#D3D3D3", "#005461", "#D3D3D3"],
    legend=False,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Jam (AM)", fontsize=25)
ax[1].set_title("Jam dengan Penyewa Terendah", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].tick_params(axis='both', labelsize=20)
st.pyplot(fig)

# --- Visualisasi 3: Berdasarkan Musim ---
st.subheader("Tingkat Penggunaan Layanan Sewa Sepeda Berdasarkan Musim")
colors_season = ["#D3D3D3", "#018790", "#005461", "#00B7B5"]

fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(
    y="count_cr", 
    x="season",
    data=season_df.sort_values(by="season", ascending=False),
    hue="season",
    palette=colors_season,
    ax=ax,
    legend=False
)
ax.set_title("Grafik Antar Musim", loc="center", fontsize=50)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='x', labelsize=35)
ax.tick_params(axis='y', labelsize=30)
st.pyplot(fig)

# --- Visualisasi 4: RFM Overview ---
st.subheader('RFM Overview Berdasarkan Jam Operasional')
col_rfm1, col_rfm2, col_rfm3 = st.columns(3)

with col_rfm1:
    fig, ax = plt.subplots(figsize=(10, 6))
    top_recency = rfm_recap_df.sort_values(by="recency", ascending=True).head(5)
    sns.barplot(data=top_recency, x="hours", y="recency", color='#00B7B5', ax=ax)
    ax.set_title("Recency (days)", fontsize=18)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='both', labelsize=15)
    st.pyplot(fig)

with col_rfm2:
    fig, ax = plt.subplots(figsize=(10, 6))
    top_frequency = rfm_recap_df.sort_values(by="order_count", ascending=False).head(5)
    sns.barplot(data=top_frequency, x="hours", y="order_count", color='#00B7B5', ax=ax)
    ax.set_title("Frequency", fontsize=18)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='both', labelsize=15)
    st.pyplot(fig)

with col_rfm3:
    fig, ax = plt.subplots(figsize=(10, 6))
    top_monetary = rfm_recap_df.sort_values(by="revenue", ascending=False).head(5)
    sns.barplot(data=top_monetary, x="hours", y="revenue", color='#00B7B5', ax=ax)
    ax.set_title("Monetary", fontsize=18)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='both', labelsize=15)
    st.pyplot(fig)

st.caption('Copyright (c) Angel Endrika 2026')
