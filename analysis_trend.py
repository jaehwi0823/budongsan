import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import platform


# 년월
def number_to_character(v):
        if v < 10:
            return '0'+str(v)
        else:
            return str(v)

def get_ready(mydf, type='bs'):
    # 컬럼 변환
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
    else:
        print("type 오류: \{bs, js\} 중 하나")
        return
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
    mydf_m['WEEKNUM'] = mydf_m['YYMMDD'].dt.strftime("%Y%U").astype(int)

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

# 트렌드 그래프
def show_trend(indat, varn, lgd=None, price='거래금액', rolling=0):
    # groupby 컬럼
    grp1 = indat.groupby(['WEEKNUM',varn])[['전용면적',price]].sum()
    grp1['prc_area'] = grp1[price] / grp1['전용면적']
    grp2 = indat.groupby(['WEEKNUM']).size()
    
    # 그래프 준비
    pltsize = (40, 15)
    plt.figure(figsize=pltsize)

    # 한글 폰트 깨짐
    # plt.rc('font', family='AppleGothic')
    if platform.system() == 'Darwin': #맥
            plt.rc('font', family='AppleGothic') 
    elif platform.system() == 'Windows': #윈도우
            plt.rc('font', family='Malgun Gothic') 
    elif platform.system() == 'Linux': #리눅스 (구글 콜랩)
            plt.rc('font', family='Malgun Gothic') 
    plt.rcParams['axes.unicode_minus'] = False #한글 폰트 사용시 마이너스 폰트 깨짐 해결

    # 나머지 그래프
    fig, ax1 = plt.subplots(figsize=pltsize)
    ax2 = ax1.twinx()

    vList = np.sort(indat[varn].unique())
    for cd in vList:
        subgrp = grp1.xs(cd, level=1).reset_index()
        if rolling > 0:
            ax1.plot(subgrp.WEEKNUM, 
                     subgrp.prc_area.rolling(rolling).mean())
        else:
            ax1.plot(subgrp.WEEKNUM, subgrp['prc_area'])
    WKNUM = grp1.reset_index()['WEEKNUM'].drop_duplicates()
    # print((len(WKNUM), len(grp2)))
    ax2.bar(WKNUM, grp2, alpha=0.2)
    plt.xticks(WKNUM, WKNUM)

    if lgd:
        ax1.legend(lgd, loc='upper left')
    else:
        ax1.legend(vList, loc='upper left')
    return fig

# 서울 지역 추가 정리
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
