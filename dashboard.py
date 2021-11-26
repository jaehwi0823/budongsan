import streamlit as st
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import analysis_trend as at


###############################################################################
#  Inputs
###############################################################################
# 데이터
# def get_data(region, dtype, year, ):
#     return pd.read_csv(f'./data/{region}_apt_{dtype}_{year}.csv',
#                         encoding='CP949', low_memory=False)


# raw = pd.read_csv('./data/seoul_apt_buysell_2021.csv',
#                   encoding='CP949', low_memory=False)
# raw_v = at.get_ready(raw, type='bs')

# # 정보표출
# # 법정동 코드
# LAWD_CD = pd.read_csv('./data/bjdcd.txt', sep='\t')
# LAWD_CD['level2'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: x[0] + ' ' + x[1] if len(x) > 1 else x[0])
# LAWD_CD['short_cd'] = LAWD_CD['법정동코드'].astype(str).str[:5]
# LAWD_CD2 = LAWD_CD.loc[LAWD_CD.폐지여부 == '존재', ['short_cd','level2']].drop_duplicates()

# # 법정동 코드 검색기
# def get_lawd_cd(nm):
#     return LAWD_CD2.loc[(LAWD_CD2.level2.str.contains(nm))]
# def get_lawd_cd_all(nm):
#     return LAWD_CD[LAWD_CD.법정동명.str.contains(nm) & (LAWD_CD.폐지여부 == '존재')]

# # 서울 지역구분
# SEOUL = get_lawd_cd('서울특별시').copy()
# SEOUL['area'] = SEOUL['level2'].str.replace('서울특별시 ', '')
# SEOUL['gubun'] = SEOUL['area'].apply(at.seoul_area)
# SEOUL_DICT = SEOUL.set_index('short_cd').to_dict()['area']

# # 지역구분 코드 검색기
# def get_gubun_cd(nm):
#     return SEOUL.loc[SEOUL.gubun.str.contains(nm), 'short_cd']
# def get_gubun_df(mydf, nm):
#     return mydf[mydf.bjd_cd.isin(get_gubun_cd(nm))]

# def get_sub_regions(rg):
#     if rg == '강북':
#         return ['도봉구','강북구','성북구','노원구']
#     elif rg == '동서울':
#         return ['동대문구','중랑구','성동구','광진구']
#     elif rg == '강동':
#         return ['강동구','송파구']
#     elif rg == '강남':
#         return ['서초구','강남구']
#     elif rg == '남서울':
#         return ['동작구','관악구','금천구']
#     elif rg == '강서':
#         return ['강서구','양천구','영등포구','구로구']
#     elif rg == '서서울':
#         return ['은평구','마포구','서대문구']
#     elif rg == '도심':
#         return ['종로구','중구','용산구']
#     else:
#         return ['기타']

# def detail_cd(d, bjd):
#     if d == '상세 지역':
#         return 'bjd_cd', bjd
#     elif d == '아파트 연식':
#         return 'old', ['2016 이내','2011 이내','2006 이내','2001 이내','1996 이내','1991 이내','1986 이내'],
#     elif d == '아파트 면적':
#         return 'area', ['40m2 미만','60m2 미만','80m2 미만','90m2 미만','120m2 미만','120m2 이상'],
#     else:
#         return 'bjd_cd', bjd



###############################################################################
#  Layout
###############################################################################
# 제목
st.title("Hello, 부동산 실거래!")

# 사이드바
# data_type = st.sidebar.selectbox(
#     '관심 거래?',
#     ('매매','전세','월세')
# )
# region = st.sidebar.selectbox(
#     '관심 지역?',
#     ('강북','동서울','강동','강남','남서울','강서','서서울','도심','기타서울')
# )
# detail = st.sidebar.selectbox(
#     '가격 세분화 기준',
#     ('상세 지역','아파트 연식','아파트 면적')
# )
# roll = st.sidebar.selectbox(
#     '이동평균 가격 기준',
#     ('1','2','3','4','5','8','10','12')
# )
# periods = st.sidebar.slider(
#     '기간 선택',
#     2016, 2021, (2020, 2021)
# )

# # 상세 지역 표시
# st.write(region, " 지역은 ", get_sub_regions(region))

# # 그래프
# tmp = get_gubun_df(raw_v, region)
# bjd = list(map(lambda x: SEOUL_DICT[x], np.sort(tmp.bjd_cd.unique())))
# varn, lgd = detail_cd(detail, bjd)
# st.pyplot(at.show_trend(tmp,
#                         varn = varn,
#                         lgd = lgd,
#                         rolling = int(roll)))

