import requests
from xml.etree import ElementTree
import pandas as pd


# get key
encodingKey = ''
decodingKey = ''
with open("./account/datago.txt", "r") as f:
            encodingKey = f.readline()
            decodingKey = f.readline()
encodingKey = encodingKey.replace('\n', '')

# 년월
def number_to_character(v):
        if v < 10:
            return '0' + str(v)
        else:
            return str(v)

# make url
def apt_buysell_url(lawd_cd, deal_ymd, pageNo, rowNum):
    # make url
    url = 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev'
    queryParams = '?serviceKey=' + encodingKey + \
                  '&LAWD_CD=' + str(lawd_cd) + \
                  '&DEAL_YMD=' + str(deal_ymd) + \
                  '&pageNo=' + str(pageNo) + \
                  '&numOfRows=' + str(rowNum)
    return url + queryParams
def apt_junse_url(lawd_cd, deal_ymd, pageNo, rowNum):
    # make url
    url = 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent'
    queryParams = '?serviceKey=' + encodingKey + \
                  '&LAWD_CD=' + str(lawd_cd) + \
                  '&DEAL_YMD=' + str(deal_ymd) + \
                  '&pageNo=' + str(pageNo) + \
                  '&numOfRows=' + str(rowNum)
    return url + queryParams

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
            # print(f"nRows: {nRows}, total: {total}, last: {last}, page: {page}")
        
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

def get_month_by_code(urlFn, mycd: list, myYM):
    rslt = pd.DataFrame()
    for cd in mycd:
        rslt = rslt.append(get_page_by_code(urlFn, cd, myYM))
    return rslt

def get_year_by_codes(urlFn, year, rng: int, mycd: list):
    rslt = pd.DataFrame()
    for YYYY in range(year, year+rng):
        for MM in range(1, 13):
            YYYYMM = str(YYYY) + number_to_character(MM)
            for cd in mycd:
                rslt = rslt.append(get_page_by_code(urlFn, cd, YYYYMM))
    return rslt

# 법정동 코드
LAWD_CD = pd.read_csv('./data/법정동코드 전체자료.txt', sep='\t')
LAWD_CD = LAWD_CD[LAWD_CD.폐지여부 == '존재']
LAWD_CD['level2'] = LAWD_CD['법정동명'].str.split(' ').apply(lambda x: x[0] + x[1] if len(x) > 1 else x[0])
LAWD_CD['short_cd'] = LAWD_CD['법정동코드'].astype(str).str[:5]
LAWD_CD2 = LAWD_CD[['short_cd','level2']].drop_duplicates()

def get_lawd_cd(nm):
    return LAWD_CD2.loc[(LAWD_CD2.level2.str.contains(nm))]
def get_lawd_cd_all(nm):
    return LAWD_CD[LAWD_CD.법정동명.str.contains(nm) & (LAWD_CD.폐지여부 == '존재')]


#####################################################################
#  데이터 수집
#####################################################################
# 서울 법정동코드
SEOUL_CODES = list(get_lawd_cd('서울특별시').short_cd)[1:]
GYUNGGI_CODES = list(get_lawd_cd('경기도').short_cd)[1:]

# params
year = 2020
rng = 1

# 서울/경기, 매매/전세
for cds, locs in zip([SEOUL_CODES, GYUNGGI_CODES], ['seoul', 'gyunggi']):
    for func, dtype in zip([apt_buysell_url, apt_junse_url], ['buysell', 'junse']):
        raw_out = pd.DataFrame()
        raw_out = get_year_by_codes(func, year, rng, cds)
        raw_out.to_csv(f'./data/{locs}_apt_{dtype}_{year}.csv', 
                            encoding='CP949', index=False)



# # 서울 아파트 매매
# seoul_apt_buysell = pd.DataFrame()
# seoul_apt_buysell = get_year_by_codes(apt_buysell_url, year, rng, SEOUL_CODES)
# seoul_apt_buysell.to_csv('./data/seoul_apt_buysell_2021.csv', 
#                        encoding='CP949', index=False)

# # 서울 아파트 전월세
# seoul_apt_junse = pd.DataFrame()
# seoul_apt_junse = get_year_by_codes(apt_junse_url, year, rng, SEOUL_CODES)
# seoul_apt_junse.to_csv('./data/seoul_apt_junse_2021.csv', 
#                        encoding='CP949', index=False)

# # 수지 아파트 전월세
# suji_apt_junse = pd.DataFrame()
# suji_apt_junse = get_year_by_codes(apt_junse_url, year, rng, ['41465'])
# suji_apt_junse.to_csv('./data/suji_apt_junse_2021.csv', 
#                       encoding='CP949', index=False)

# # 수지 아파트 전월세
# suji_apt_junse = pd.DataFrame()
# suji_apt_junse = get_year_by_codes(apt_junse_url, year, rng, ['41465'])
# suji_apt_junse.to_csv('./data/suji_apt_junse_2021.csv', 
#                       encoding='CP949', index=False)
