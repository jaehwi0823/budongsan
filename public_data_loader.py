import requests
import pandas as pd
import ndb
import address
from datetime import datetime
from xml.etree import ElementTree


# get data.go.kr key
encodingKey = ''
decodingKey = ''
with open("./account/datago.txt", "r") as f:
            encodingKey = f.readline()
            decodingKey = f.readline()
encodingKey = encodingKey.replace('\n', '')

# get db key
# dbId = ''
# dbPw = ''
# with open("./account/dynamo.txt", "r") as f:
#             dbId = f.readline()
#             dbPw = f.readline()
# dbId = dbId.replace('\n', '')

# 년월
def number_to_character(v, length=2):
        return (length - len(str(v))) * '0' + str(v)

# make url
def apt_buysell_url(lawd_cd, deal_ymd, pageNo, rowNum):
    url = 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev'
    queryParams = '?serviceKey=' + encodingKey + \
                  '&LAWD_CD=' + str(lawd_cd) + \
                  '&DEAL_YMD=' + str(deal_ymd) + \
                  '&pageNo=' + str(pageNo) + \
                  '&numOfRows=' + str(rowNum)
    return url + queryParams
def apt_junse_url(lawd_cd, deal_ymd, pageNo, rowNum):
    url = 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent'
    queryParams = '?serviceKey=' + encodingKey + \
                  '&LAWD_CD=' + str(lawd_cd) + \
                  '&DEAL_YMD=' + str(deal_ymd) + \
                  '&pageNo=' + str(pageNo) + \
                  '&numOfRows=' + str(rowNum)
    return url + queryParams

# 한 번 조회 후 결과 가져오기
def get_items_by_url(myurl):
    response = requests.get(myurl)
    root = ElementTree.fromstring(response.content)

    this_df = pd.DataFrame()
    for body in root.iter('body'):
        for items in body.iter('items'):
            for item in items:
                tmp_dict = {}
                for i in item:
                    tmp_dict[i.tag] = i.text
                    
                tmp_df = pd.DataFrame.from_records([tmp_dict])
                this_df = this_df.append(pd.DataFrame(tmp_df))
    return this_df, root

# paging하며 결과 전체 가져오기
def get_page_by_code(urlFn, myCD, myYM):
    repeater = True
    page = 1
    err = 0
    rslt_df = pd.DataFrame()
    while repeater:
        myurl = urlFn(myCD, myYM, page, 100)
        subDf, root = get_items_by_url(myurl)
        rslt_df = rslt_df.append(subDf)

        try:
            nRows = int(root[1][1].text)
            # pageN = int(root[1][2].text)
            total = int(root[1][3].text)
            last = (total // 100) + 1
        
            if page >= last:
                repeater = False
            else:
                page += 1

        except IndexError as e:
            print(root[0][0].text)
            print(root[0][1].text)
            print(f"TIME: {myYM}, CODE: {myCD}, Page: {page}")
            err += 1

            if err >= 5:
                repeater = False
    return rslt_df

# 월 고정 & 코드 리스트
def get_month_by_code(urlFn, mycd: list, myYM):
    rslt = pd.DataFrame()
    for cd in mycd:
        rslt = rslt.append(get_page_by_code(urlFn, cd, myYM))
    return rslt

# 연 단위 & 코드 리스트
def get_year_by_codes(urlFn, year, rng: int, mycd: list):
    rslt = pd.DataFrame()
    for YYYY in range(year, year+rng):
        for MM in range(1, 13):
            YYYYMM = str(YYYY) + number_to_character(MM)
            for cd in mycd:
                rslt = rslt.append(get_page_by_code(urlFn, cd, YYYYMM))
    return rslt

# 매매/전세 DB저장 전 전처리 함수
def prep_bds_data(bdstype, ind):
    mydf = ind.copy()
    if bdstype == 'BS':
        for col in mydf.columns:
            if col in ['']:
                pass
            else:
                mydf[col] = mydf[col].str.strip().str.replace(',', '')
    elif bdstype == 'JS':
        for col in mydf.columns:
            if col in ['']:
                pass
            else:
                mydf[col] = mydf[col].str.strip().str.replace(',', '')
    else:
        print("Nothing processed :(")
        return ind
    return mydf



#####################################################################
#  데이터 수집
#####################################################################
def update_bds_data(urlFn, code, yyyymm):
    rslt = pd.DataFrame()
    if urlFn == apt_buysell_url:
        myCollection = 'BS'
    elif urlFn == apt_junse_url:
        myCollection = 'JS'
    else:
        print("wrong url function")
        return 
    
    # download
    rslt = get_page_by_code(urlFn, code, yyyymm)
    yy = str(yyyymm)[:4]
    mm = str(yyyymm)[4:]
    
    # update
    if rslt.empty:
        print(f"{code} in {yy}.{mm}. data: Nothing downloaded :(")
    else:
        rslt = prep_bds_data(myCollection, rslt)
        
        ndb.delete_item(db_name='BUDONGSAN', 
                        collection_name=myCollection, 
                        condition={'지역코드': code,
                                '년': yy,
                                '월':mm})
        print(f"{code} in {yy}.{mm}. data deleted!")
        rsp = ndb.insert_item_many(rslt.to_dict('records'), 
                                db_name='BUDONGSAN', 
                                collection_name=myCollection)
        print(f"{code} in {yy}.{mm}. data inserted!")
        print("-"*10)
        return rslt
# update_bds_data(apt_buysell_url, '11110', '202111')
# update_bds_data(apt_junse_url, '11110', '202111')

def update_all_by_mon(year=datetime.today().year,
                      month=datetime.today().month):
    codes = address.get_searchable_lawd_cd('')['short_cd'].drop_duplicates()
    funcs = [apt_buysell_url, apt_junse_url]
    yyyymm = str(year) + number_to_character(month)
    for func in funcs:
        for code in codes:
            update_bds_data(func, code, yyyymm)
    print("="*10,f" {yyyymm} completed! ", "="*10, "\n")

def update_all_by_year(yr=2021):
    codes = address.get_searchable_lawd_cd('')['short_cd'].drop_duplicates()
    funcs = [apt_buysell_url, apt_junse_url]
    for rng in range(1, 13):
        yyyymm = str(yr) + number_to_character(rng)
        for func in funcs:
            for code in codes:
                update_bds_data(func, code, yyyymm)
        print("="*10,f" {yyyymm} completed! ", "="*10, "\n")

if __name__ == "__main__":
    update_all_by_year()
