import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
#from query import *
import time
import datetime

st.set_page_config(page_title="Dashboard",page_icon="🌍",layout="wide")
st.subheader("🔔  Analytics Dashboard")
st.markdown("##")

theme_plotly = None # None or streamlit

# Style
with open('/home/ec2-user/environment/apps/style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

#fetch data
#result = view_all_data()
#df=pd.DataFrame(result,columns=["Policy","Expiry","Location","State","Region","Investment","Construction","BusinessType","Earthquake","Flood","Rating","id"])

 
#load excel file
df=pd.read_excel('/home/ec2-user/environment/apps/data1.xlsx', sheet_name='Sheet1')

#side bar
st.sidebar.image("/home/ec2-user/environment/apps/logo1.png",caption="Developed and Maintaned by: samir: +255675839840")

#switcher
st.sidebar.header("Please filter")
region=st.sidebar.multiselect(
    "Select 분기",
     options=df["월"].unique(),
     default=df["월"].unique(),
)
location=st.sidebar.multiselect(
    "Select Location",
     options=df["Location"].unique(),
     default=df["Location"].unique(),
)
construction=st.sidebar.multiselect(
    "Select Construction",
     options=df["Construction"].unique(),
     default=df["Construction"].unique(),
)

df_selection=df.query(
    "월==@region & Location==@location & Construction ==@construction"
)

def Home():
    st.title("Personal Health Information")
    first, last = st.columns(2)
    first.text_input("Name")
    last.text_input("Gender")
    email, mob = st.columns(2)
    email.text_input("Height")
    mob.text_input("Weight")
    user, pw, pw2 = st.columns(3)
    user.text_input("Age")
    ch, bl, sub = st.columns(3)
    
    today=st.date_input("날짜를 선택하세요.", datetime.datetime.now())
    the_time=st.time_input("시간을 입력하세요.", datetime.time())

    st.markdown("""---""")

#graphs

def graphs():
    #total_investment=int(df_selection["Investment"]).sum()
    #averageRating=int(round(df_selection["Rating"]).mean(),2)
    
    #simple bar graph
    investment_by_business_type=(
        df_selection.groupby(by=["식품군"]).count()[["Calories"]].sort_values(by="Calories")
    )
    fig_investment=px.bar(
       investment_by_business_type,
       x="Calories",
       y=investment_by_business_type.index,
       orientation="h",
       title="<b> Main Intake Group </b>",
       color_discrete_sequence=["#0083B8"]*len(investment_by_business_type),
       template="plotly_white",
    )


    fig_investment.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False))
     )

        #simple line graph
    investment_state=df_selection.groupby(by=["월"]).count()[["Calories"]]
    fig_state=px.line(
       investment_state,
       x=investment_state.index,
       y="Calories",
       orientation="v",
       title="<b>분기별 평균 칼로리</b>",
       color_discrete_sequence=["#0083b8"]*len(investment_state),
       template="plotly_white",
    )
    fig_state.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False))
     )

    left,right,center=st.columns(3)
    left.plotly_chart(fig_state,use_container_width=True)
    right.plotly_chart(fig_investment,use_container_width=True)
    
    with center:
      #pie chart
      fig = px.pie(df_selection, values='Rating', names='영양성분', title='Daily Nutrient Ratio')
      fig.update_layout(legend_title="영양성분", legend_y=0.9)
      fig.update_traces(textinfo='percent+label', textposition='inside')
      st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
     
#def Progressbar():
     ##showData=st.multiselect('Filter: ',df_selection.columns,default=["Policy","Expiry","Location","State","Region","Investment","Construction","BusinessType","Earthquake","Flood","Rating"])
        #st.dataframe(df_selection[showData],use_container_width=True)


def sideBar():

 with st.sidebar:
    selected=option_menu(
        menu_title="Main Menu",
        options=["Home","Progress"],
        icons=["house","eye"],
        menu_icon="cast",
        default_index=0
    )
 if selected=="Home":
    #st.subheader(f"Page: {selected}")
    Home()
    graphs()
 if selected=="Progress":
    #st.subheader(f"Page: {selected}")
    Progressbar()
    graphs()

sideBar()



#theme
hide_st_style=""" 

<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
</style>
"""
