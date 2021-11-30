from datetime import datetime, timedelta
import address
import ndb
import pandas as pd
import sys



###############################################################################
#  test
###############################################################################
# imp.reload(address)
# imp.reload(ndb)
# address.get_address_cds()
# address.get_address_nms()
# address.get_address_cdnms()

# SELECTED_DF = pd.DataFrame(ndb.find_item(db_name = 'BUDONGSAN',
#                                             collection_name = LOAD_TABLE,
#                                             condition = LOAD_COND.update({'년':'2021',
#                                                                           '월':'1',
#                                                                           '일':'1'}),
#                                             fields = {col:1 for col in LOAD_COLUMNS}))



###############################################################################
#  필요 함수들
###############################################################################
def number_to_character(v):
        if v < 10:
            return '0'+str(v)
        else:
            return str(v)

def get_weeknum(year, mon, day):
    return datetime(year, mon, day).strftime("%V")

def get_firstday(year, weekno):
    return datetime.strptime(f'{year}{weekno}-1', '%Y%W-%w').strftime("%Y%m%d")

def get_weekdays(year, weekno):
    dt = datetime.strptime(f'{year}{weekno}-1', '%Y%W-%w')
    weekdays = []
    for i in range(7):
        weekdays.append((dt + timedelta(days=i)).strftime("%Y%m%d"))
    return weekdays

def weekly_data_loader(days, LOAD_COND, LOAD_COLUMNS, LOAD_TABLE):
    rslt = pd.DataFrame()
    for yyyymmdd in days:
        yyyy = str(int(yyyymmdd[:4]))
        mm   = str(int(yyyymmdd[4:6]))
        dd   = str(int(yyyymmdd[6:]))
        LOAD_COND.update({'년':yyyy,
                          '월':mm,
                          '일':dd})
        rslt = rslt.append(pd.DataFrame(ndb.find_item(db_name = 'BUDONGSAN',
                                                      collection_name = LOAD_TABLE,
                                                      condition = LOAD_COND,
                                                      fields = {col:1 for col in LOAD_COLUMNS})))
    return rslt
# weekly_data_loader(get_weekdays(2021, 1), LOAD_COND, LOAD_COLUMNS, LOAD_TABLE)



class PreAgg:
    ###########################################################################
    #  AGG1
    ###########################################################################
    def AGG1(self):
        print('<This is AGG1>')
        AGG_COLLECTION = 'AGG1'
        for data_type in ['매매', '전세', '월세']:
            if data_type == '매매':
                LOAD_TABLE = 'BS'
                LOAD_PRICE = '거래금액'
                LOAD_COND = {'해제여부':''}
            elif data_type == '전세':
                LOAD_TABLE = 'JS'
                LOAD_PRICE = '보증금액'
                LOAD_COND = {'월세금액': '0'}
            else:
                LOAD_TABLE = 'JS'
                LOAD_PRICE = '월세금액'
                LOAD_COND = {'월세금액': {'$ne':'0'}}
            LOAD_COLUMNS = [LOAD_PRICE] + ['년','월','일','전용면적']

            for area_cd in address.get_address_cds()['short_cd']:
                LOAD_COND.update({'지역코드': area_cd})
                for year in [2021]:
                    for i in range(53):
                        SELECTED_DF = weekly_data_loader(get_weekdays(year, i), LOAD_COND, LOAD_COLUMNS, LOAD_TABLE)
                    
                        if not SELECTED_DF.empty:
                            # SELECTED_DF['YYMMDD'] = SELECTED_DF['년'] + \
                            #                         SELECTED_DF['월'].astype(int).apply(number_to_character) + \
                            #                         SELECTED_DF['일'].astype(int).apply(number_to_character)
                            # SELECTED_DF['YYMMDD'] = pd.to_datetime(SELECTED_DF['YYMMDD'], format='%Y%m%d')
                            # SELECTED_DF['WEEKNUM'] = SELECTED_DF['YYMMDD'].dt.strftime("%Y%U").astype(int)

                            weekno = int(str(year) + number_to_character(i))
                            SELECTED_DF['WEEKNUM'] = weekno
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
                                                        '거래종류': data_type,
                                                        'WEEKNUM': weekno})
                            ndb.insert_item_many(db_name = 'BUDONGSAN', 
                                                collection_name = AGG_COLLECTION,
                                                datas = SELECTED_GRP.reset_index().to_dict('records'))
                            print(f"{area_cd}지역, {year}.W{i}의 {data_type} 데이터 집계 완료!")



###############################################################################
#  main
###############################################################################
if __name__ == "__main__":
    getattr(PreAgg, sys.argv[1])(PreAgg)