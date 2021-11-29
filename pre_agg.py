import address
import ndb
import pandas as pd
import sys, getopt

"""
    Type 1: 지역코드 / 거래 / 


"""

###############################################################################
#  test
###############################################################################
# imp.reload(address)
# imp.reload(ndb)
# address.get_address_cds()
# address.get_address_nms()
# address.get_address_cdnms()


###############################################################################
#  필요 함수들
###############################################################################
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

class PreAgg:
    ###########################################################################
    #  AGG1
    ###########################################################################
    def AGG1(self):
        print('This is AGG1')
        AGG_COLLECTION = 'AGG1'
        DATATYPES = ['매매', '전세', '월세']
        for data_type in DATATYPES:
            for area_cd in address.get_address_cds()['short_cd']:
                LOAD_COND = {'지역코드': area_cd}
                if data_type == '매매':
                    LOAD_TABLE = 'BS'
                    LOAD_PRICE = '거래금액'
                    LOAD_COND.update({'해제여부':''})
                elif data_type == '전세':
                    LOAD_TABLE = 'JS'
                    LOAD_PRICE = '보증금액'
                    LOAD_COND.update({'월세금액': '0'})
                else:
                    LOAD_TABLE = 'JS'
                    LOAD_PRICE = '월세금액'
                    LOAD_COND.update({'월세금액': {'$ne':'0'}})

                LOAD_COLUMNS = [LOAD_PRICE] + ['년','월','일','전용면적']
                SELECTED_DF = pd.DataFrame(ndb.find_item(db_name = 'BUDONGSAN',
                                                         collection_name = LOAD_TABLE,
                                                         condition = LOAD_COND,
                                                         fields = {col:1 for col in LOAD_COLUMNS}))
                
                if not SELECTED_DF.empty:
                    SELECTED_DF['YYMMDD'] = SELECTED_DF['년'] + \
                                            SELECTED_DF['월'].astype(int).apply(number_to_character) + \
                                            SELECTED_DF['일'].astype(int).apply(number_to_character)
                    SELECTED_DF['YYMMDD'] = pd.to_datetime(SELECTED_DF['YYMMDD'], format='%Y%m%d')
                    SELECTED_DF['WEEKNUM'] = SELECTED_DF['YYMMDD'].dt.strftime("%Y%U").astype(int)
                    SELECTED_DF = SELECTED_DF[['WEEKNUM', LOAD_PRICE, '전용면적']]
                    SELECTED_DF = SELECTED_DF.rename(columns={LOAD_PRICE: '거래가격'})

                    SELECTED_GRP = SELECTED_DF.groupby('WEEKNUM')[['거래가격', '전용면적']].apply(lambda x: x.astype(float).sum())
                    SELECTED_GRP['거래건수'] = SELECTED_DF.groupby('WEEKNUM').size()
                    SELECTED_GRP['전용면적'] = SELECTED_GRP['전용면적'].astype(float)
                    SELECTED_GRP['평균금액'] = SELECTED_GRP['거래가격'] / SELECTED_GRP['전용면적']
                    SELECTED_GRP = SELECTED_GRP[['평균금액','거래건수']]
                    SELECTED_GRP['지역코드'] = area_cd
                    SELECTED_GRP['거래종류'] = data_type

                    ndb.delete_item(db_name = 'BUDONGSAN', 
                                    collection_name = AGG_COLLECTION,
                                    condition = {'지역코드': area_cd,
                                                '거래종류': data_type})
                    ndb.insert_item_many(db_name = 'BUDONGSAN', 
                                         collection_name = AGG_COLLECTION,
                                         datas = SELECTED_GRP.reset_index().to_dict('records'))
                    print(f"{area_cd}의 {data_type} 데이터 집계 완료!")



# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    getattr(PreAgg, sys.argv[1])(PreAgg)