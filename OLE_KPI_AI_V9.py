import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Manufacturing KPI AI V9",layout="wide")
st.title("🚀 Manufacturing KPI AI V9")

uploaded=st.file_uploader("Upload OLE Workbook",type=["xlsm","xlsx"])

if uploaded:
    def ole(sheet):
        try:
            df=pd.read_excel(uploaded,sheet_name=sheet,header=None)
            for r in range(len(df)):
                try:
                    v=float(df.iloc[r,2])
                    if 0.8<=v<=1: return v
                except: pass
        except: pass
        return None

    plates=ole('Plates OLE')
    potting=ole('Potting OLE')
    supplements=ole('Supplements OLE')

    rank=pd.DataFrame({'Department':['Plates','Potting','Supplements'],'OLE':[plates,potting,supplements]}).dropna()

    a,b,c,d=st.columns(4)
    a.metric('Plates OLE',f'{plates:.1%}' if plates else 'N/A')
    b.metric('Potting OLE',f'{potting:.1%}' if potting else 'N/A')
    c.metric('Supplements OLE',f'{supplements:.1%}' if supplements else 'N/A')
    d.metric('Average OLE',f"{rank['OLE'].mean():.1%}" if not rank.empty else 'N/A')

    if not rank.empty:
        st.plotly_chart(px.bar(rank.sort_values('OLE',ascending=False),x='Department',y='OLE',color='OLE',title='Department OLE Ranking'),use_container_width=True)

    try:
        oee=pd.read_excel(uploaded,sheet_name='Supplements OEE',header=None)
        machines=pd.DataFrame({
            'Machine':['FD1','FD2','FD3','FD4'],
            'OEE':[float(oee.iloc[6,1]),float(oee.iloc[7,1]),float(oee.iloc[8,1]),float(oee.iloc[9,1])]
        })

        st.header('Freeze Dryer OEE')
        st.plotly_chart(px.bar(machines.sort_values('OEE',ascending=False),x='Machine',y='OEE',color='OEE'),use_container_width=True)

        best_machine=machines.sort_values('OEE',ascending=False).iloc[0]
        worst_machine=machines.sort_values('OEE').iloc[0]

        x,y,z=st.columns(3)
        x.metric('Best Machine',best_machine['Machine'])
        y.metric('Worst Machine',worst_machine['Machine'])
        z.metric('Average OEE',f"{machines['OEE'].mean():.1%}")
    except:
        pass

    comp=pd.read_excel(uploaded,sheet_name='Completed')
    comp['QtyF']=pd.to_numeric(comp['QtyF'],errors='coerce')
    comp['QtyO']=pd.to_numeric(comp['QtyO'],errors='coerce')

    wk=comp.groupby('Week',as_index=False).agg(Output=('QtyF','sum'),Waste=('QtyO','sum'))

    def wkkey(x):
        m=re.search(r'(\d{4})-W(\d+)',str(x))
        return int(m.group(1))*100+int(m.group(2)) if m else 0

    wk['Sort']=wk['Week'].apply(wkkey)
    wk=wk.sort_values('Sort').tail(5)

    latest=wk.iloc[-1]
    avg_output=wk['Output'].mean()
    avg_waste=wk['Waste'].mean()

    st.header('Last 5 Week Analysis')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Latest Output',f'{latest["Output"]:,.0f}')
    k2.metric('5 Week Avg',f'{avg_output:,.0f}')
    k3.metric('Latest Waste',f'{latest["Waste"]:,.0f}')
    k4.metric('5 Week Waste Avg',f'{avg_waste:,.0f}')

    st.plotly_chart(px.bar(wk,x='Week',y='Output',text='Output',color_discrete_sequence=['green'],title='Output Last 5 Weeks'),use_container_width=True)
    st.plotly_chart(px.bar(wk,x='Week',y='Waste',text='Waste',color_discrete_sequence=['red'],title='Waste Last 5 Weeks'),use_container_width=True)

    waste_pct=(comp['QtyO'].sum()/comp['QtyF'].sum()*100) if comp['QtyF'].sum()!=0 else 0
    variance=((latest['Output']-avg_output)/avg_output*100) if avg_output else 0
    score=max(0,min(100,round((rank['OLE'].mean()*100 if not rank.empty else 80)*0.7+max(0,20-waste_pct))))

    st.header('Statistical Analysis')
    st.write(f'Output variance vs 5-week average: {variance:.1f}%')
    st.write(f'Waste % of output: {waste_pct:.2f}%')
    st.write(f'Output standard deviation: {wk["Output"].std():,.0f}')
    st.metric('Overall KPI Score',f'{score}/100')

    st.subheader('Top 10 Waste Work Orders')
    st.dataframe(comp.groupby('WO',as_index=False)['QtyO'].sum().sort_values('QtyO',ascending=False).head(10),use_container_width=True)

    if not rank.empty:
        best=rank.sort_values('OLE',ascending=False).iloc[0]['Department']
        worst=rank.sort_values('OLE').iloc[0]['Department']
        st.subheader('AI Commentary')
        st.success(f'Best department: {best}. Lowest department: {worst}. Output variance is {variance:.1f}%. Waste is {waste_pct:.2f}% of output. KPI score is {score}/100.')
