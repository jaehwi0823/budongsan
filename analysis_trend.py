import pandas as pd
import matplotlib.pyplot as plt
import StrategyGround as SG
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
            #!wget "https://www.wfonts.com/download/data/2016/06/13/malgun-gothic/malgun.ttf"
            #!mv malgun.ttf /usr/share/fonts/truetype/
            #import matplotlib.font_manager as fm 
            #fm._rebuild() 
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


if __name__ == '__main__':

    ###############################################################################
    #  법정동 코드 정비
    ###############################################################################
    # 법정동 코드
    LAWD_CD = pd.read_csv('./data/법정동코드 전체자료.txt', sep='\t')
    LAWD_CD['level2'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: x[0] + ' ' + x[1] if len(x) > 1 else x[0])
    LAWD_CD['short_cd'] = LAWD_CD['법정동코드'].astype(str).str[:5]
    LAWD_CD2 = LAWD_CD.loc[LAWD_CD.폐지여부 == '존재', ['short_cd','level2']].drop_duplicates()

    # 법정동 코드 검색기
    def get_lawd_cd(nm):
        return LAWD_CD2.loc[(LAWD_CD2.level2.str.contains(nm))]
    def get_lawd_cd_all(nm):
        return LAWD_CD[LAWD_CD.법정동명.str.contains(nm) & (LAWD_CD.폐지여부 == '존재')]

    # 서울 지역구분
    SEOUL = get_lawd_cd('서울특별시').copy()
    SEOUL['area'] = SEOUL['level2'].str.replace('서울특별시 ', '')
    SEOUL['gubun'] = SEOUL['area'].apply(seoul_area)
    SEOUL_DICT = SEOUL.set_index('short_cd').to_dict()['area']

    # 지역구분 코드 검색기
    def get_gubun_cd(nm):
        return SEOUL.loc[SEOUL.gubun.str.contains(nm), 'short_cd']
    def get_gubun_df(mydf, nm):
        return mydf[mydf.bjd_cd.isin(get_gubun_cd(nm))]

    get_lawd_cd('수서')
    get_lawd_cd_all('수서')
    get_gubun_cd('수서')



    ###############################################################################
    #  전세
    ###############################################################################
    # 서울 전세
    raw = pd.read_csv('./data/seoul_apt_junse_2020.csv',
                    encoding='CP949', low_memory=False)
    raw_v = get_ready(raw, type='js')
    # raw_v.head()
    # raw_v.WEEKNUM.value_counts().sort_index().plot.bar(figsize=(20, 10))

    # 지역별
    tmp = raw_v[(raw_v.bjd_cd=='11500') & (raw_v.월세금액==0)]
    show_trend(tmp,
            varn='bjd_cd',
            lgd=['강서구'],
            price='보증금액',
            rolling=5)
    # 연령별
    show_trend(tmp, varn='old', 
            lgd=['2016 이내','2011 이내','2006 이내','2001 이내','1996 이내','1991 이내','1986 이내'],
            price='보증금액',
            rolling=2)
    # 면적별
    show_trend(tmp, 
            varn='area', 
            lgd=['40m2 미만','60m2 미만','80m2 미만','90m2 미만','120m2 미만','120m2 이상'],
            price='보증금액',
            rolling=5)



    ###############################################################################
    #  매매
    ###############################################################################
    # 서울 매매
    raw = pd.read_csv('./data/seoul_apt_buysell_2020.csv',
                    encoding='CP949', low_memory=False)
    raw_v = get_ready(raw, type='bs')


    # 지역별: '도심', '동서울', '강북', '서서울', '강서', '남서울', '강남', '강동'
    tmp = get_gubun_df(raw_v, '강서')
    show_trend(tmp,
            varn='bjd_cd',
            lgd=list(map(lambda x: SEOUL_DICT[x], np.sort(tmp.bjd_cd.unique()))),
            rolling=5)
    # 연령별
    show_trend(tmp, 
            varn='old', 
            lgd=['2016 이내','2011 이내','2006 이내','2001 이내','1996 이내','1991 이내','1986 이내'],
            rolling=5)
    # 면적별
    show_trend(tmp, 
            varn='area', 
            lgd=['40m2 미만','60m2 미만','80m2 미만','90m2 미만','120m2 미만','120m2 이상'],
            rolling=5)



    # 법정동코드 찾기
    interesting_name = '수서'
    get_lawd_cd_all(interesting_name)
    # 법정동코드 별
    tmp = raw_v[raw_v.bjd_cd=='11680']
    show_trend(tmp,
            varn='bjd_cd',
            lgd=[interesting_name],
            rolling=5)
    # 연령별
    show_trend(tmp, 
            varn='old', 
            lgd=['2016 이내','2011 이내','2006 이내','2001 이내','1996 이내','1991 이내','1986 이내'],
            rolling=5)
    # 면적별
    show_trend(tmp, 
            varn='area', 
            lgd=['40m2 미만','60m2 미만','80m2 미만','90m2 미만','120m2 미만','120m2 이상'],
            rolling=5)
