import streamlit as st
import pandas as pd
import numpy as np
# import platform
import matplotlib.pyplot as plt
import address
import ndb


###############################################################################
#  Inputs
###############################################################################
# 트렌드 그래프
def show_trend(indat, price='평균금액', cnt='거래건수', lgd=None, pltsize = (40, 15)):
    # 한글 폰트 깨짐
    # plt.rc('font', family='AppleGothic')
    # if platform.system() == 'Darwin': #맥
    #         plt.rc('font', family='AppleGothic') 
    # elif platform.system() == 'Windows': #윈도우
    #         plt.rc('font', family='Malgun Gothic') 
    # elif platform.system() == 'Linux': #리눅스 (구글 콜랩)
    #         plt.rc('font', family='Malgun Gothic') 
    # plt.rcParams['axes.unicode_minus'] = False #한글 폰트 사용시 마이너스 폰트 깨짐 해결

    # 나머지 그래프
    plt.figure(figsize=pltsize)
    fig, ax1 = plt.subplots(figsize=pltsize)
    ax2 = ax1.twinx()
    ax1.plot(indat.WEEKNUM, indat[price])
    ax2.bar(indat.WEEKNUM, indat[cnt], alpha=0.2)
    plt.xticks(indat.WEEKNUM, indat.WEEKNUM)

    if lgd:
        ax1.legend(lgd, loc='upper left')
    # else:
    #     ax1.legend(vList, loc='upper left')
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
#  Header
###############################################################################
# 설정
st.set_page_config(page_title="Weekly 아파트 실거래",
                   layout='wide')

# 제목
st.title("Weekly 아파트 실거래 트렌드!")
st.write("Weekly '전용면적' 당 '거래금액'의 평균을 거래량과 함께 보여줍니다. (단위: 만원/제곱미터)")


###############################################################################
#  조건 (사이드바)
###############################################################################
# 거래 종류
data_type = st.sidebar.selectbox(
    '관심 거래?',
    ('매매','전세','월세')
)
# 지역코드
interesting_nm = st.sidebar.selectbox(
    '관심 지역? (글자를 지우면 검색 가능)',
    address.get_address_nms().sort_values(by='법정동명')
)
all_cds = address.get_address_cdnms()
interesting_cd = all_cds.loc[all_cds['법정동명'] == interesting_nm, 'short_cd'].values[0]
# 그래프 종류
# detail = st.sidebar.selectbox(
#     '가격 세분화 기준',
#     ('상세 지역','아파트 연식','아파트 면적')
# )
# 저층 제외
# lowFloor = st.sidebar.selectbox(
#     '0: 저층 미제외, 1: 1층 제외, 2: 2층 제외',
#     ('0','1','2')
# )
# 이동평균 기준
# roll = st.sidebar.selectbox(
#     '이동평균 가격 기준',
#     ('1','2','3','4','5','8','10','12')
# )
# 데이터 기간
# periods = st.sidebar.slider(
#     '기간 선택',
#     2016, 2021, (2020, 2021)
# )



###############################################################################
#  데이터 준비
###############################################################################
SELECTED_DF = pd.DataFrame(ndb.find_item(db_name = 'BUDONGSAN',
                                         collection_name = 'AGG1',
                                         condition = {'지역코드': interesting_cd,
                                                      '거래종류': data_type},
                                         fields = {'_id':0}))

# 상세 지역 표시
# st.write(region, " 지역은 ", get_sub_regions(region))
st.write("[" + interesting_nm + "] 데이터")

# 그래프
st.pyplot(show_trend(SELECTED_DF))

# 상세
# st.write("RAW 데이터 확인 (임시)")
# st.write(SELECTED_DF)

# outro
st.write("데이터: 국토교통부 실거래 API")
st.write("문의: iamhwii@gmail.com")