# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 18:47:49 2021

@author: jacka
"""

from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import os
pd.set_option('display.max_columns', 20)
na = [np.nan]
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
}



#get REIT quote codes
url = "https://www.intelligentinvestor.com.au/indices/xpj/xpj"
source = requests.get(url, headers=headers).text
fqloc= source.find("<table")
quote=list(na*20)
qsource=source[fqloc:fqloc+50000]

for x in range(200):
    if qsource.find("</a") > qsource.find("<!-- //Content -->"):
        quote=quote[:x]
        break
    qloc = qsource.find("</a")
    qsource = qsource[qloc:]
    quote[x] = qsource[qsource.find('(')+1:qsource.find(')')]
    qsource= qsource[qsource.find(')'):]
    print(x)



#Practice making the script adaptable
BS_ARGS = ['Cash and cash equivalents','Net property, plant and equipment','Equity and other investments','Total assets','Current debt', 'Long-term debt']
IS_ARGS = ['Total revenue', 'Cost of revenue','Gross profit', 'Total operating expenses','Total other income/expenses net', 'Net income']




#Get all balance sheet info

source=0
dates = list(na*5)
for q in enumerate(quote):
    print(q[1])
    url = "".join(['https://au.finance.yahoo.com/quote/',q[1],'.AX/balance-sheet?p=',q[1],'.AX'])
    source = requests.get(url, headers=headers).text
    d_loc = source.find('Breakdown')
    cd_loc = source.find('Current debt')
    lt_loc = source.find('Long-term debt')
    cc_loc = source.find('Cash and cash equivalents')
    args = [d_loc, cd_loc, lt_loc, cc_loc]
   
    def bs_vals(loc):
        x=list(na*5)
        sub = source[loc:]
        for d in range(5):
            sub_loc = sub.find('Ta(c)')
            if sub.find('class="D(tbr)')<sub_loc:
                break
            sub= sub[sub_loc:]
            val= sub[sub.find('>')+1:sub.find('</')]
            x[d] = val
            if val == '':
                break
            if val[0]== '<':
                val=val[val.find('>')+1:]
                x[d] = val
            sub = sub[sub.find('</'):]
        return x
    var_names = ['Date', 'Current debt', 'Long-term debt', 'Cash']
    vars()[q[1]] = {}
    for i in enumerate(args):
        vars()[q[1]][var_names[i[0]]] = bs_vals(i[1])
    print(vars()[q[1]])
    vars()["".join(['BS_DF_',q[1]])]=pd.DataFrame(vars()[q[1]])
    


#Get all income statement info
dates = list(na*5)
for q in enumerate(quote):
    print(q[1])
    url = "".join(['https://au.finance.yahoo.com/quote/',q[1],'.AX/financials?p=',q[1],'.AX'])
    source = requests.get(url, headers=headers).text
    d_loc = source.find('Breakdown')
    tr_loc = source.find('Total revenue')
    ni_loc = source.find('Net income')
    args = [d_loc,tr_loc,ni_loc]
    
    def is_vals(loc):
        x=list(na*5)
        sub = source[loc:]
        for d in range(5):
            sub_loc = sub.find('Ta(c)')
            if sub.find('class="D(tbr)')<sub_loc:
                break
            sub= sub[sub_loc:]
            val= sub[sub.find('>')+1:sub.find('</')]
            x[d] = val
            if val == '':
                break
            if val[0]== '<':
                val=val[val.find('>')+1:]
                x[d] = val
            sub = sub[sub.find('</'):]
        return x
    var_names = ['Date', 'Total Revenue', 'Net Income']
    vars()[q[1]] = {}
    for i in enumerate(args):
        vars()[q[1]][var_names[i[0]]] = is_vals(i[1])
    print(vars()[q[1]])
    vars()["".join(['IS_DF_',q[1]])]=pd.DataFrame(vars()[q[1]])



#merge BS and IS info
for q in enumerate(quote):
    
    vars()["".join(['DF_',q[1]])]= pd.merge(
        vars()["".join(['BS_DF_',q[1]])],
        vars()["".join(['IS_DF_',q[1]])],
        how = "outer",
        on = "Date"
        )



#Get 4 years of Historical Prices from sept 1
for q in enumerate(quote):
    print(q[1])
    #get dates
    dates = vars()["".join(['DF_',q[1]])]['Date']
    dates = dates.drop([4,5])
    years = list(na*4)
    months= list(na*4)
    if type(vars()["".join(['DF_',q[1]])]['Date'][0]) != str:
        continue
    for d in enumerate(dates):
        years[d[0]] = d[1][-4:]
        months[d[0]] = d[1][-7:-5]
    
    url = "".join(['https://au.finance.yahoo.com/quote/',q[1],'.AX/history?period1=1474329600&period2=1632096000&interval=1mo&filter=history&frequency=1mo&includeAdjustedClose=true'])
    source = requests.get(url, headers=headers).text
    
    def p_vals(year):
        sub = source[year:]
        sub_loc=sub.find('.')
        sub = sub[sub_loc-4:]
        x = sub[sub.find('>')+1:sub.find('<')]
        return x
    
    history={'Date': years, 'Price': list(na*4)}
    history = pd.DataFrame(history)
    for d in enumerate(years):
        if months[d[0]] == '12':
            #add a year on
            x = source.find("".join(["31 Mar ",
                                     str(int(d[1])+1)]
                                    ))
            history['Price'][d[0]]=p_vals(x)
            vars()["".join(['PRICE_DF_',q[1]])] = history
            continue
            
        x = source.find("".join(["01 Sept ",d[1]]))
        print(p_vals(x))
        history['Price'][d[0]]=p_vals(x)
        vars()["".join(['PRICE_DF_',q[1]])] = history
        
        
#merge price data with df
for q in enumerate(quote):
    if "".join(['PRICE_DF_',q[1]]) in globals():
        vars()["".join(['DF_',q[1]])]= pd.concat(
            [vars()["".join(['DF_',q[1]])],
            vars()["".join(['PRICE_DF_',q[1]])]['Price']],
            axis = 1
            )
        print(q[1])
        print(vars()["".join(['DF_',q[1]])])






#Get all shares outstanding info
shareout=list(na*len(quote))
for q in enumerate(quote):
    print(q[1])
    url = "".join(["https://au.finance.yahoo.com/quote/",q[1],".AX/key-statistics?p=",q[1],".AX"])
    source = requests.get(url, headers=headers).text
    location = source.find('Shares outstanding')
    selection = source[location:]
    divider = selection.find('Fw(500) Ta(end) Pstart(10px) Miw(60px)')
    selection = selection[divider:]
    span = selection.find(">")
    selection = selection[span:]
    so=selection[selection.find('>')+1:selection.find('<')]
    if so == '':
             continue
    shareout[q[0]]=so
    print(shareout)
    
shareout = {'CODE':quote, 'Shares_Outstanding':shareout}
shareout = pd.DataFrame(shareout)


#save as csv
for q in quote:
    print(q)
    vars()["".join(['DF_',q])].to_csv("".join([#[your location],q,'.csv']), encoding='utf-8')


