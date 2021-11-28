import pandas as pd
import ndb


###############################################################################
#  법정동 코드 DB저장
###############################################################################
def init_lawd_cd():
    LAWD_CD = pd.read_csv('./data/bjdcd.txt', sep='\t')
    LAWD_CD = LAWD_CD[LAWD_CD.폐지여부 == '존재']
    LAWD_CD['level2'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: x[0] + ' ' + x[1] if len(x) > 1 else x[0])
    LAWD_CD['len'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: len(x))
    LAWD_CD['short_cd'] = LAWD_CD['법정동코드'].astype(str).str[:5]
    ndb.insert_item_many(LAWD_CD.to_dict('records'), 'BUDONGSAN', 'LAWDCD')



###############################################################################
#  법정동 코드 검색기
###############################################################################
def get_lawd_cd_all(nm):
    return pd.DataFrame(ndb.find_item(db_name='BUDONGSAN',
                                      collection_name='LAWDCD',
                                      condition={'법정동명': {'$regex': nm, '$options' : 'i'}}))
def get_searchable_lawd_cd(nm):
    return pd.DataFrame(ndb.find_item(db_name='BUDONGSAN',
                                      collection_name='LAWDCD',
                                      condition={'법정동명': {'$regex': nm, '$options' : 'i'}, 'len':2}))
# get_lawd_cd_all('수서')
# get_searchable_lawd_cd('수서')




###############################################################################
#  바로 실행
###############################################################################
if __name__ == '__main__':
    # 기존 자료 먼저 삭제
    ndb.delete_item(db_name='BUDONGSAN', 
                    collection_name='LAWDCD', 
                    condition={'폐지여부': '존재'})
    print("Old data deleted!")
    init_lawd_cd()
    print("New data Saved!")

