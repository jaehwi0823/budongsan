import pandas as pd
import matplotlib.pyplot as plt
import StrategyGround as SG
import numpy as np


# 년월
def number_to_character(v):
        if v < 10:
            return '0'+str(v)
        else:
            return str(v)

def get_ready(mydf, type='bs'):
    if type == 'bs':
        mydf_m = mydf[mydf['해제여부'] != 'O'].copy()
        mydf_m.rename(columns = {'도로명시군구코드' : 'bjd_cd'}, inplace = True)
        mydf_m = mydf_m[['년','월','일','bjd_cd','건축년도','전용면적','층','거래금액']]
        mydf_m['거래금액'] = mydf_m['거래금액'].str.replace(',','').astype(int)
    elif type == 'js':
        mydf_m = mydf.copy()
        mydf_m.rename(columns = {'지역코드' : 'bjd_cd'}, inplace = True)
        mydf_m = mydf_m[['년','월','일','bjd_cd','건축년도','전용면적','층','보증금액','월세금액']]
        mydf_m['보증금액'] = mydf_m['보증금액'].str.replace(',','').astype(int)
        mydf_m['월세금액'] = mydf_m['월세금액'].str.strip().fillna('0').str.replace(',','').astype(int)
    mydf_m = mydf_m[mydf_m['bjd_cd'].notna()]
    mydf_m['bjd_cd'] = mydf_m['bjd_cd'].astype(int).astype(str)
    
    # 아파트 연식 구간
    def bldg_old(v):
        if v >= 2021:
            return 0
        elif v >= 2016:
            return 1
        elif v >= 2011:
            return 2
        elif v >= 2006:
            return 3
        elif v >= 2001:
            return 4
        elif v >= 1996:
            return 5
        elif v >= 1991:
            return 6
        elif v >= 1986:
            return 7
        elif v >= 1981:
            return 8
        else:
            return 9
    mydf_m['old'] = mydf_m['건축년도'].apply(bldg_old)
    mydf_m['old'].value_counts().sort_index()

    # 아파트 전용면적 구간
    def bldg_area(v):
        if v < 40:
            return 0
        elif v < 60:
            return 1
        elif v < 80:
            return 2
        elif v < 90:
            return 3
        elif v <120:
            return 4
        else:
            return 5
    mydf_m['area'] = mydf_m['전용면적'].apply(bldg_area)
    mydf_m['area'].value_counts().sort_index()

    # 년월일
    mydf_m['YYMMDD'] = mydf_m['년'].astype(str) + \
                       mydf_m['월'].apply(number_to_character) + \
                       mydf_m['일'].apply(number_to_character)
    mydf_m['YYMMDD'] = pd.to_datetime(mydf_m['YYMMDD'], format='%Y%m%d')
    mydf_m['WEEKNUM'] = mydf_m['년'].astype(str) + \
                        mydf_m['YYMMDD'].dt.isocalendar().week\
                                        .apply(number_to_character).astype(str)

    # 이름 바꾸기
    mydf_m.head()

    # 1~2층 제외
    mydf_m = mydf_m[mydf_m['층'] > 2]

    # 건축년도 
    mydf_m = mydf_m[(mydf_m['old'] >= 1) & (mydf_m['old'] <= 7)]

    # 필요 형번환
    mydf_m['old'] = mydf_m['old'].astype(str)
    mydf_m['area'] = mydf_m['area'].astype(str)

    return mydf_m

def show_trend(indat, varn, lgd=None, price='거래금액'):
    grp1 = indat.groupby(['WEEKNUM',varn])[['전용면적',price]].sum()
    grp1['prc_area'] = grp1[price] / grp1['전용면적']
    grp2 = indat.groupby(['WEEKNUM']).size()
    plt.figure(figsize=(40, 15))
    vList = np.sort(indat[varn].unique())

    fig, ax1 = plt.subplots(figsize=(30, 15))
    ax2 = ax1.twinx()
    for cd in vList:
        subgrp = grp1.xs(cd, level=1).reset_index()
        ax1.plot(subgrp.WEEKNUM, subgrp['prc_area'])
    grp2.plot(kind='bar', ax=ax2, alpha=0.2)

    if lgd:
        ax1.legend(lgd, loc='upper left')
    else:
        ax1.legend(vList, loc='upper left')
    plt.show()



###############################################################################
#  법정동 코드 정비
###############################################################################
# 법정동 코드
LAWD_CD = pd.read_csv('./data/법정동코드 전체자료.txt', sep='\t')
LAWD_CD['level2'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: x[0] + x[1] if len(x) > 1 else x[0])
LAWD_CD['short_cd'] = LAWD_CD['법정동코드'].astype(str).str[:5]
LAWD_CD2 = LAWD_CD.loc[LAWD_CD.폐지여부 == '존재', ['short_cd','level2']].drop_duplicates()

# 법정동 코드 검색기
def get_lawd_cd(nm):
    return LAWD_CD2.loc[(LAWD_CD2.level2.str.contains(nm))]

# 서울 지역 정리
def seoul_area(cd):
    if cd in ['도봉구','강북구','성북구','노원구']:
        return '강북'
    elif cd in ['동대문구','중랑구','성동구','광진구']:
        return '동서울'
    elif cd in ['강동구','송파구']:
        return '강동'
    elif cd in ['서초구','강남구']:
        return '강남'
    elif cd in ['동작구','관악구','금천구']:
        return '남서울'
    elif cd in ['강서구','양천구','영등포구','구로구']:
        return '강서'
    elif cd in ['은평구','마포구','서대문구']:
        return '서서울'
    elif cd in ['종로구','중구','용산구']:
        return '도심'
    else:
        return '기타서울'

# 서울 지역구분
SEOUL = get_lawd_cd('서울특별시')
SEOUL['area'] = SEOUL['level2'].str.replace('서울특별시', '')
SEOUL['gubun'] = SEOUL['area'].apply(seoul_area)

# 지역구분 코드 검색기
def get_gubun_cd(nm):
    return SEOUL.loc[SEOUL.gubun.str.contains(nm), 'short_cd']

get_lawd_cd('강서')
get_gubun_cd('강서')

###############################################################################
#  데이터 준비
###############################################################################
# 서울 전세
df1 = pd.read_csv('./data/all_apt_buysell_2016_2019.csv', encoding='CP949')
df2 = pd.read_csv('./data/all_apt_buysell_2020.csv', encoding='CP949')
df3 = pd.read_csv('./data/all_apt_buysell_2021.csv', encoding='CP949')
df4 = pd.read_csv('./data/all_apt_buysell_202111.csv', encoding='CP949')
raw = df1.append([df2, df3, df4])

# ready
raw_v = get_ready(raw)
raw_v = raw_v[raw_v.WEEKNUM < '202150']

# 지역별
show_trend(raw_v, 'bjd_cd')
# 연령별
show_trend(raw_v, 'old', ['>=2016','>=2011','>=2006','>=2001','>=1996','>=1991','>=1986'])
# 면적별
show_trend(raw_v, 'area', ['<40m2','<60m2','<80m2','<90m2','<120m2','>=120m2'])

# 수지 =========
sj = pd.read_csv('./data/suji_apt_buysell_2020_2021.csv', encoding='CP949')
sj = sj.append(pd.read_csv('./data/suji_apt_buysell_2020_2021.csv', encoding='CP949'))
sj_v = get_ready(sj)
sj_v = sj_v[sj_v.WEEKNUM < 50]
show_trend(sj_v, 'old', ['<=2016','<=2011','<=2006','<=2001','<=1996','<=1991','<=1986'])
show_trend(sj_v, 'area', ['<40m2','<60m2','<80m2','<90m2','<120m2','>=120m2'])

# 수서 전세
ss = pd.read_csv('./export/seoul_apt_junse_2020.csv', encoding='CP949', low_memory=False)
ss_v = get_ready(ss, 'js')
# ss_v = ss_v[(ss_v.월세금액 == 0) & (ss_v.WEEKNUM < '202150') & (ss_v.WEEKNUM > '202060')]
ss_v = ss_v[(ss_v.월세금액 == 0) & (ss_v.WEEKNUM < '202150')]
print(ss_v.shape)
show_trend(ss_v, 'old', 
           ['<=2016','<=2011','<=2006','<=2001','<=1996','<=1991','<=1986'],
           price='보증금액')
show_trend(ss_v, 'area', 
           ['<40m2','<60m2','<80m2','<90m2','<120m2','>=120m2'],
           price='보증금액')








grp1 = raw_v.groupby(['WEEKNUM','old'])[['전용면적','거래금액']].sum()
grp1['prc_area'] = grp1['거래금액'] / grp1['전용면적']
grp1['size'] = raw_v.groupby(['WEEKNUM','old']).size()
grp1.xs('1', level=1)

len(grp1.xs('1', level=1)['prc_area']), len(grp1.xs('1', level=1)['size'])
grp1.xs('1', level=1)['prc_area']
grp1.xs('1', level=1)['size']
grp1.xs('1', level=1)['size'].plot(kind='bar', color='c', alpha=0.3)
grp1['size'].plot(kind='bar', color='c', alpha=0.3)

grp1.to_csv('./export/grp1.csv', encoding='CP949')

raw_v.groupby(['WEEKNUM'])['전용면적'].count()



grp2 = raw_v.groupby(['WEEKNUM','old'])[['전용면적','거래금액']].agg(['sum','count'])
grp2.to_csv('./export/grp2.csv', encoding='CP949')


for i in range(1, 3):
    grp1.xs(str(i), level=1)['size'].plot(kind='bar', color='c', alpha=0.3)
plt.show()


grp1.xs('1', level=1).index
grp2 = raw_v.groupby(['WEEKNUM']).size()
grp2.index == grp1.xs('1', level=1).index


fig, ax1 = plt.subplots(figsize=(30, 15))
subgrp = grp1.xs('1', level=1).reset_index()
ax1.plot(subgrp.index, subgrp['prc_area'])
ax2 = ax1.twinx()
grp2.plot(kind='bar', ax=ax2, alpha=0.2)
ax1.set_xlim([-1, 45])
print(ax1.get_xlim())
print(ax2.get_xlim())
print(subgrp.index == grp2.index)
fig.tight_layout()
plt.show()