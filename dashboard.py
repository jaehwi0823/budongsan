import streamlit as st
import pandas as pd
import numpy as np
import platform
import matplotlib.pyplot as plt
import analysis_trend as at
# import imp
import address
import ndb


###############################################################################
#  Inputs
###############################################################################
# 년월
def number_to_character(v):
        if v < 10:
            return '0'+str(v)
        else:
            return str(v)

def get_ready(mydf):
    # 아파트 연식 구간
    def bldg_old(v):
        v = int(v)
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
    mydf['old'] = mydf['건축년도'].apply(bldg_old)
    mydf['old'].value_counts().sort_index()

    # 아파트 전용면적 구간
    def bldg_area(v):
        v = float(v)
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
    mydf['area'] = mydf['전용면적'].apply(bldg_area)
    mydf['area'].value_counts().sort_index()

    # 년월일
    mydf['YYMMDD'] = mydf['년'] + \
                     mydf['월'].astype(int).apply(number_to_character) + \
                     mydf['일'].astype(int).apply(number_to_character)
    mydf['YYMMDD'] = pd.to_datetime(mydf['YYMMDD'], format='%Y%m%d')
    mydf['WEEKNUM'] = mydf['YYMMDD'].dt.strftime("%Y%U").astype(int)

    # 건축년도 
    mydf = mydf[(mydf['old'] >= 1) & (mydf['old'] <= 7)]

    # 필요 형번환
    mydf['old'] = mydf['old'].astype(str)
    mydf['area'] = mydf['area'].astype(str)

    return mydf

# 트렌드 그래프
def show_trend(indat, varn, lgd=None, price='거래금액', rolling=0):
    # groupby 컬럼
    indat[price] = indat[price].astype(int)
    indat['전용면적'] = indat['전용면적'].astype(float)
    # print(indat[[price,'전용면적']].dtypes)

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


def get_sub_regions(rg):
    if rg == '강북':
        return ['도봉구','강북구','성북구','노원구']
    elif rg == '동서울':
        return ['동대문구','중랑구','성동구','광진구']
    elif rg == '강동':
        return ['강동구','송파구']
    elif rg == '강남':
        return ['서초구','강남구']
    elif rg == '남서울':
        return ['동작구','관악구','금천구']
    elif rg == '강서':
        return ['강서구','양천구','영등포구','구로구']
    elif rg == '서서울':
        return ['은평구','마포구','서대문구']
    elif rg == '도심':
        return ['종로구','중구','용산구']
    else:
        return ['기타']

def detail_cd(d, bjd):
    if d == '상세 지역':
        return 'bjd_cd', bjd
    elif d == '아파트 연식':
        return 'old', ['2016 이내','2011 이내','2006 이내','2001 이내','1996 이내','1991 이내','1986 이내'],
    elif d == '아파트 면적':
        return 'area', ['40m2 미만','60m2 미만','80m2 미만','90m2 미만','120m2 미만','120m2 이상'],
    else:
        return 'bjd_cd', bjd



###############################################################################
#  test
###############################################################################
# imp.reload(address)
# imp.reload(ndb)
# address.get_address_cds()
# address.get_address_nms()
# address.get_address_cdnms()







###############################################################################
#  Layout
###############################################################################
# 제목
st.title("Hello, 부동산 Weekly 실거래!")
st.write("Weekly 전용면적 당 거래금액의 평균을 거래량과 함께 보여줍니다.")


###############################################################################
#  조건 (사이드바)
###############################################################################
# # 거래 종류
# data_type = st.sidebar.selectbox(
#     '관심 거래?',
#     ('매매','전세','월세')
# )
# # 지역코드
# interesting_nm = st.sidebar.selectbox(
#     '관심 지역?',
#     address.get_address_nms().sort_values(by='법정동명')
# )
# all_cds = address.get_address_cdnms()
# interesting_cd = all_cds.loc[all_cds['법정동명'] == interesting_nm, 'short_cd']
# # 그래프 종류
# # detail = st.sidebar.selectbox(
# #     '가격 세분화 기준',
# #     ('상세 지역','아파트 연식','아파트 면적')
# # )
# # 저층 제외
# lowFloor = st.sidebar.selectbox(
#     '0: 저층 미제외, 1: 1층 제외, 2: 2층 제외',
#     ('0','1','2')
# )
# # 이동평균 기준
# roll = st.sidebar.selectbox(
#     '이동평균 가격 기준',
#     ('1','2','3','4','5','8','10','12')
# )
# # 데이터 기간
# # periods = st.sidebar.slider(
# #     '기간 선택',
# #     2016, 2021, (2020, 2021)
# # )



# ###############################################################################
# #  데이터 준비
# ###############################################################################
# LOAD_TABLE = 'BS'
# LOAD_COND = {'지역코드':interesting_cd.values[0], 
#              '층':{'$gt':lowFloor}}
# LOAD_COLUMNS = ['지역코드','건축년도','년','월','일','법정동','아파트','층','전용면적']
# if data_type == '매매':
#     LOAD_PRICE = '거래금액'
#     LOAD_COND.update({'해제여부':''})
#     LOAD_COLUMNS = [LOAD_PRICE] + LOAD_COLUMNS
# else:
#     LOAD_TABLE = 'JS'
#     LOAD_COLUMNS = ['보증금액', '월세금액'] + LOAD_COLUMNS
#     LOAD_PRICE = '보증금액'
#     if data_type == '월세':
#         LOAD_PRICE = '월세금액'
#         LOAD_COND.update({'월세금액':{'$ne':'0'}})

# SELECTED_DF = pd.DataFrame(ndb.find_item(db_name = 'BUDONGSAN',
#                                          collection_name = LOAD_TABLE,
#                                          condition = LOAD_COND,
#                                          fields = {col:1 for col in LOAD_COLUMNS}))
# # 상세 지역 표시
# # st.write(region, " 지역은 ", get_sub_regions(region))
# st.write("[" + interesting_nm + "] 데이터")

# # 그래프
# # tmp = get_gubun_df(raw_v, region)
# # bjd = list(map(lambda x: SEOUL_DICT[x], np.sort(tmp.bjd_cd.unique())))
# # varn, lgd = detail_cd(detail, bjd)
# tmp = get_ready(SELECTED_DF)
# st.pyplot(show_trend(tmp,
#                      varn = '지역코드',
#                      lgd = [interesting_nm],
#                      price = LOAD_PRICE,
#                      rolling = int(roll)))


# # 상세
# # st.write("RAW 데이터 확인 (임시)")
# # st.write(SELECTED_DF)

# outro
st.write("데이터 출처: 국토교통부 실거래 API")
st.write("연락처: iamhwii@gmail.com")