import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas.api.types import is_string_dtype, is_numeric_dtype
from typing import Optional

# pd.options.display.float_format = '{:.4f}'.format





""" To-do  &  Considerations

[ON PROGRESS]
    - matrix binning features (o)
    - matrix with target counter ()
    - multi-target validation ()
    - 

[Considerations]
    - subset도 필요하겠지만, 색인만 하고 넘어가는것도 필요할 듯. 
      (ex) high/low side ovveride
    - 운영: Batch mode, Online mode 분리해야 하는지?


[IDEA]
    모든 것은 Process
    Process 는 Function으로 구성
    Process는 filtering, cutoff, 승인, 오버라이드, 한도, 금리 등
    Process/Function 모두 Attribute
    Attribute은 성과, 차트, Format, 최적화

    segmentation은 특수 Func
    구조가 분기됨
    성과 Summary 순서 필요
    Report level limit 필요

    Func의 Format
    단변량분석: cutout, fineclassing, 등급화
    다변량분석: cross-matrix, PCA, 차원축소, 회귀분석, 평점표, water-fall

"""




#####################################################################
#  Dataset <- pandas.DataFrame
#####################################################################
class Dataset(pd.DataFrame):
    """ 신용평가 및 유사 분석을 위한 데이터 클래스
    
    주요기능: Target설정, 개발/검증/.../검증n, Type 확인 및 변환, 
            집계조건 설정(실행 등), FC
    주요설정: 항목 및 조건을 모두 설정해야 함

    두 개 항목 구성비 동시에
    두 개 항목 FC 결과 동시에 - 개발검증을 위해 필요할수도

    Attributes:
        _DATASET_TARGETS (list): 데이터셋의 관리 목표 항목명 리스트
        _CUSTOM_COLUMNS (list): 임의로 생성한 항목명 리스트
        _KEYS (list): 데이터셋의 유일 기준 항목명 리스트
        _DEVVAL (list): 데이터셋의 개발/검증 구분 항목명 리스트
    """

    def __init__(self, data, index=None, columns=None, 
                 dtype=None, copy=None):
        super().__init__(data=data, index=index, columns=columns, 
                         dtype=dtype, copy=copy)
        self._DATASET_TARGETS = None
        self._GRD_DTYPE = pd.CategoricalDtype(list(range(1,11)) + [0],
                                              ordered=True)
    
    #################################################################
    # KEYS
    def set_keys(self, keys: list):
        """ Dataset의 Unique key 정의 """
        if len(self.dup_rows(keys)) == 0:
            self._KEYS = keys
        else:
            print("KEYS 조합은 Dataset 내에서 UNIQUE 조합이어야 합니다")

    def get_keys(self):
        return self._KEYS
    
    def dup_rows(self, varl: list, keep_cd=False):
        """ 주어진 항목들 기준으로 중복 데이터 반환

        보통 key columns에서 중복된 rows를 확인하기 위해 활용
        
        Args:
            varl: 기준 항목 리스트
            drop:
                - 'first': 첫번째 관측치만 빼고 리턴
                - 'last': 마지막 관측치만 빼고 리턴
                - False: 전부 다 리턴
        """
        selected_df = super().__getitem__(varl)
        return Dataset(selected_df[selected_df.duplicated(keep=keep_cd)])
    
    def column_has_na(self):
        """ null 값이 있는 컬럼의 null 갯수 """
        subdf = self.isna().sum()
        return Dataset(subdf[subdf != 0])

    #################################################################
    # TARGETS
    def set_targets(self, targets) -> None:
        """ Dataset의 Targets 정의 """
        if isinstance(targets, str):
            self._DATASET_TARGETS = [targets]
        elif isinstance(targets, list):
            self._DATASET_TARGETS = targets
        else:
            print("target은 string 또는 list로만 설정 가능")
    
    def get_targets(self):
        return self._DATASET_TARGETS

    #################################################################
    # GRADES
    def set_grade(self, varn: str, last_num: int = None) -> None:
        """ 등급 항목에서 0등급을 가장 마지막에 배치하는 데이터 타입으로 변경 """
        if last_num:
            self._GRD_DTYPE = pd.CategoricalDtype(
                                list(range(1,last_num+1)) + [0],
                                ordered=True
                              )
        if is_string_dtype(varn):
            self[varn].astype(int, copy=False)
        self[varn] = self[varn].astype(self._GRD_DTYPE)

    def reset_grade(self, varn: str, type):
        self[varn].astype(type, copy=False)

    #################################################################
    # DEV / VAL
    def set_devval(self) -> None:
        """ 개발검증 구분 필요성 고민중.. """
        pass

    #################################################################
    # BINNING
    def _percentile_binning(self, 
                            varn: str, 
                            nbins: int,
                            right: bool = False):
        """ 숫자형의 varn 항목을 nbins percentile 기준으로 구간으로 구간화 
        
        일반적인 신용평가개발 방법론에서 구간화하던 방식

        Args:
            varn: binning 항목명
            nbins: 최대 binning 개수
            right: True - 최대값 기준, False - 최소값 기준
        """
        selected_df = super().__getitem__([varn])

        pct_list = [round(x / nbins, 2) for x in range(nbins)]
        fc_num = selected_df[varn].quantile(q = pct_list, 
                                            interpolation = 'lower')\
                                  .drop_duplicates()
        
        if len(fc_num) == 1:
            bins = fc_num.values
            bins = list(bins)
        elif len(fc_num > 1):
            bins = sorted(np.float_(fc_num.values))
        else:
            bins = []
        
        # 최대값 기준
        if right:
            if not bins:
                bins = [np.inf]
            bins[0] = -np.inf
            labels =  bins[1:]
            return pd.cut(selected_df[varn], bins=bins, 
                          labels=labels, right=right)
        # 최소값 기준
        else:
            if not bins:
                bins = [-np.inf]
            bins = bins + [np.inf]
            labels =  bins[:-1]
            return pd.cut(selected_df[varn], bins=bins, 
                            labels=labels, right=right)

    #################################################################
    # COUNTERS
    def matrix_counter(self, 
                       by_varn: str, 
                       column_varn: str, 
                       by_bin: Optional[int] = None, 
                       column_bin: Optional[int] = None, 
                       matrix_target: str = None,
                       cond = None):
        """ 두 개의 항목 분포 집계 (Matrix format)

        pandas groupby에 categorical dtype의 경우 null 인식이 안되는 버그 존재.
        버그 때문에 counting 파트를 if else 부분으로 분리해서 계산... 후..

        Args:
            by_var: 행 기준 항목명
            column_var: 열 기준 항목명
            by_bin: 숫자형 변수의 경우 by_var을 by_bin만큼의 (균등) 구간화 가능
            column_bin: 숫자형 변수의 경우 column_var을 column_bin만큼의 
                        (균등) 구간화 가능
            cond: 조건 
        """
        selected_df = super().__getitem__([by_varn, column_varn]).copy()
        if cond:
            selected_df = selected_df[cond]

        if is_numeric_dtype(selected_df[by_varn]) and by_bin:
            selected_df['grp1'] = self._percentile_binning(by_varn, 
                                                           by_bin)
            by_varn = by_varn + '_grp1'
        if is_numeric_dtype(selected_df[column_varn]) and column_bin:
            selected_df['grp2'] = self._percentile_binning(column_varn, 
                                                           column_bin)
            column_varn = column_varn + '_grp2'

        # byvar 등급 타입이며 missing 있을 때,
        if (selected_df[by_varn].dtype.name == 'categorical' or \
            selected_df[column_varn].dtype.name == 'categorical') and \
           (selected_df[by_varn].isna().sum() > 0 or \
            selected_df[column_varn].isna().sum() > 0):
            
            # pandas 버그 때문에 어쩔 수 없이 python에서 일일히 값 비교
            tmpgrp = pd.DataFrame()
            for rowv in selected_df[by_varn].unique().sort_values():
                for colv in selected_df[column_varn].unique():
                    # row null 처리
                    if rowv == rowv:
                        cond1 = selected_df[by_varn] == rowv
                    else:
                        cond1 = selected_df[by_varn].isna()
                    # column null 처리
                    if colv == colv:
                        cond2 = selected_df[column_varn] == colv
                    else:
                        cond2 = selected_df[column_varn].isna()
                    tmpgrp.loc[rowv, colv] = len(selected_df[cond1 & cond2])
            return Dataset(tmpgrp)

        # 일반적인 경우는 simple!
        else:
            return Dataset(selected_df.groupby([by_varn, column_varn], 
                                            as_index=False, 
                                            dropna=False)\
                                    .size()\
                                    .pivot(
                        index=by_varn,
                        columns=column_varn
                ).fillna(0))

    def fineclassing_cnt(self, 
                         varn: str, 
                         nbins: int = 20, 
                         fc_target = None, 
                         target_value = None, 
                         cond = None,
                         sorting: bool = True, 
                         show: bool = False, 
                         right: bool = False):
        """ 숫자형은 nbins 구간, 문자형은 개별 값에 대한 분포를 target분포와 함께 요약

        Args:
            varn: 분석 항목명
            nbins: 숫자형 (균등) 구간 개수
            fc_target: target 변수. 미지정시 데이터셋 instance의 target 사용
            target_value: 관심있는 target 변수의 값 중 하나. 입력시 해당 값 정보만 요약
            cond: subset조건. 해당 조건에 부합하는 관측치의 결과만 요약
            sorting: 요약 결과 index 기준으로 정렬 여부
            show: fc결과 그래프
            right: 구간화 포함 방향
            IV: console에 IV 값 출력 여부
        """
        # start log
        print(">> Performance check: ", varn)

        # target not given
        if not fc_target:
            fc_target = self._DATASET_TARGETS
        elif isinstance(fc_target, str):
            fc_target = [fc_target]
        elif not isinstance(fc_target, list):
            print("target 지정은 list 또는 str만 가능합니다")
            return

        # check other errors
        if fc_target and varn in fc_target:
            print("[target은 fineclassing이 불가능합니다.]")
            return
        if varn not in self.columns:
            print(f"[{varn} 항목은 Dataset에 없는 column 이름 입니다.]")
            return

        # select column and prepare df
        if fc_target:
            selected_df = super().__getitem__([varn] + fc_target).copy()
        else:
            selected_df = super().__getitem__([varn]).copy()
        if cond:
            selected_df = selected_df[cond]

        # range
        if is_numeric_dtype(selected_df[varn]) and nbins > 1:
            selected_df['cuts'] = self._percentile_binning(varn, nbins, right=right)
        else:
            selected_df['cuts'] = selected_df[varn]
        
        # agg
        fc_rslt = selected_df['cuts'].value_counts(dropna=False).to_frame()
        fc_rslt = fc_rslt.rename(columns = {'cuts':'cnt'})

        # target value
        if fc_target:
            for tgt in fc_target:
                # value specified
                if target_value:
                    interesting_targets = [target_value]
                else:
                    interesting_targets = super().__getitem__(tgt).unique()
                # all results concat
                for tv in interesting_targets:
                    fc_rslt = pd.concat([fc_rslt,
                                        selected_df.loc[selected_df[tgt] == tv, 'cuts']\
                                            .value_counts(dropna=False).to_frame()\
                                            .rename(columns = {'cuts':f'{tgt}_{tv}'})], axis=1)

        # basic stats
        fc_rslt['cnt_pct'] = fc_rslt['cnt'] / sum(fc_rslt['cnt']) * 100
        if fc_target:
            for tgt in fc_target:
                for tv in interesting_targets:
                    fc_rslt[f'{tgt}_{tv}_rate'] = \
                        fc_rslt[f'{tgt}_{tv}'] / fc_rslt['cnt'] * 100

        # sort
        if sorting:
            fc_rslt = fc_rslt.sort_index()
        
        # index format
        try:
            fc_rslt.index = fc_rslt.index.to_series().round(2).astype(str)
        except:
            fc_rslt.index = fc_rslt.index.to_series().astype(str)

        # graph
        if show:
            plt.figure(figsize=(12, 4))
            fig, ax1 = plt.subplots()
            ax1.bar(fc_rslt.index, fc_rslt['cnt_pct'])
            if fc_target:
                ax2 = ax1.twinx()
                maxv = 0
                for tgt in fc_target:
                    for tv in interesting_targets:
                        target_name = f'{tgt}_{tv}_rate'
                        ax2.plot(fc_rslt.index, fc_rslt[target_name], 'ro-')
                        if max(fc_rslt[target_name]) not in [np.NaN, np.Inf]:
                            maxv = max(maxv, max(fc_rslt[target_name]))
                ax2.set_ylim([0, max(maxv, 1)*1.05])
            fig.tight_layout()
            plt.show()

        return Dataset(fc_rslt)

    def fineclassing_rate(self, 
                          varn: str, 
                          dividend: str, 
                          divisor: str, 
                          nbins: int, 
                          cond = None,
                          sorting = False, 
                          show = False, 
                          right = False):
        """ 숫자형은 nbins 구간, 문자형은 개별 값에 대한 분포를 target분포와 함께 요약

        Args:
            varn: 분석 항목명
            dividend: 결과 생성시 분자 항목명
            divisor: 결과 생성시 분모 항목명
            nbins: 숫자형 (균등) 구간 개수
            cond: subset조건. 해당 조건에 부합하는 관측치의 결과만 요약
            sorting: 요약 결과 index 기준으로 정렬 여부
            show: fc결과 그래프
            right: 구간화 포함 방향
        """
        print(">> Performance check: ", varn, " & (", dividend,"/",divisor,")")

        # errors
        if varn not in self.columns:
            print(f"[{varn} 항목은 Dataset에 없는 column 이름 입니다.]")
            return
        if is_string_dtype(super().__getitem__(dividend)) or \
           is_string_dtype(super().__getitem__(divisor)):
            print(f"[{varn} 항목은 Dataset에 없거나 숫자형이 아닙니다.]")
            return
        
        # data
        selected_df = super().__getitem__([varn, dividend, divisor]).copy()
        if cond:
            selected_df = selected_df[cond]

        # range
        if is_numeric_dtype(selected_df[varn]) and nbins > 1:
            selected_df['cuts'] = self._percentile_binning(varn, nbins, right=right)
        else:
            selected_df['cuts'] = selected_df[varn]
        
        # agg
        fc_rslt = selected_df['cuts'].value_counts(dropna=False).to_frame()
        fc_rslt = fc_rslt.rename(columns = {'cuts':'cnt'})

        # target agg
        fc_grp = selected_df.groupby(by='cuts', dropna=False)
        for num, div_var in enumerate([dividend, divisor]):
            fc_rslt = pd.concat([fc_rslt, 
                                 fc_grp[div_var].sum()\
                                                .rename(f'sum_{div_var}')
                                ],axis=1)

        # basic stats
        fc_rslt['cnt_pct'] = fc_rslt['cnt'] / sum(fc_rslt['cnt']) * 100
        fc_rslt['div_rate'] = fc_rslt[f'sum_{dividend}'] / fc_rslt[f'sum_{divisor}'] * 100

        # sort
        if sorting:
            fc_rslt = fc_rslt.sort_index()
        
        # index format
        try:
            fc_rslt.index = fc_rslt.index.to_series().round(2).astype(str)
        except:
            fc_rslt.index = fc_rslt.index.to_series().astype(str)

        # graph
        if show:
            plt.figure(figsize=(12, 4))
            fig, ax1 = plt.subplots()
            ax1.bar(fc_rslt.index, fc_rslt['cnt_pct'])
            ax2 = ax1.twinx()
            maxv = 0
            ax2.plot(fc_rslt.index, fc_rslt['div_rate'], 'ro-')
            if max(fc_rslt['div_rate']) not in [np.NaN, np.Inf]:
                maxv = max(maxv, max(fc_rslt['div_rate']))
            ax2.set_ylim([0, max(maxv, 1)*1.05])
            fig.tight_layout()
            plt.show()

        return Dataset(fc_rslt)


    #################################################################
    # UTILS
    def cal_IV(self, fc_rslt, varn, targetv) -> float:
        """ Fineclassing 결과 Dataset에서 IV 계산"""
        IVdf = fc_rslt.copy()
        
        IVdf['Non_TARGET'] = IVdf[varn] - IVdf[targetv]
        IVdf['TP']         = IVdf[targetv]/IVdf[targetv].sum()
        IVdf['NTP']        = IVdf['Non_TARGET']/IVdf['Non_TARGET'].sum()
        IVdf['IV_c1']      = IVdf['TP']-IVdf['NTP']
        IVdf['IV_c2']      = IVdf['TP']/IVdf['NTP']
        IVdf['IV_c3']      = np.log(IVdf['IV_c2'])
        IVdf['IV_c4']      = IVdf['IV_c1'] * IVdf['IV_c3']

        print("IV:", int(IVdf['IV_c4'].sum()*10000)/100,"%")
        return IVdf['IV_c4'].sum()
    
    # left join
    def leftjoin(self, dataA, dataB, keyv):
        return pd.merge(dataA, dataB, 
                        left_on=keyv, 
                        right_on=keyv, 
                        how='left')
    def leftjoin(self, dataB, keyv):
        return pd.merge(self, dataB, 
                        left_on=keyv, 
                        right_on=keyv, 
                        how='left')


class TimeseriesDataset(Dataset):
    def __init__(self, data, datetime_col, index=None, columns=None, dtype=None, copy=None):
        super().__init__(data, index=index, columns=columns, dtype=dtype, copy=copy)
        self.DATETIME_COLUMN = datetime_col


#####################################################################
#  Functions
#####################################################################
class Func:
    """ 공통 Function Class. [한 개]의 Dataset 처리 Step
    
    일단 아이디어
        1) Cutout
        2) Corss-matrix
        3) Filtering
        4) Scorecard
        5) Segmentation/Merge
        6) Modeling
    
    공통 클래스로 처리하지 못하는 기능은 상속 후 함수 override
    """
    FUNCTION_COUNTER = 0

    def __init__(self, 
                 name = None,
                 previous = None) -> None:
        """ Function 기본 정의

        Attributes:
            _FUNCTION_NAME: Function 이름
            _IN_CONDITION: Function 적용 사전요건
            _FUNC_RESULT: Function 적용 결과
        """
        Func.FUNCTION_COUNTER += 1
        if name:
            self._FUNCTION_NAME = name
        else:
            self._FUNCTION_NAME = self.__class__.__name__ + \
                                f'_{Func.FUNCTION_COUNTER}'
        self._IN_CONDITION = previous
        self._FUNC_RESULT = None
    
    # def __call__(self, dataset):
    #     return self.perform(dataset)
    # def __del__(self):
    #     pass
    
    def set_name(self, name):
        self._FUNCTION_NAME = name
    def get_name(self):
        return self._FUNCTION_NAME
    
    def perform(self, dataset):
        """ 결과 생성 함수 """
        dataset[self._FUNCTION_NAME] = self._FUNC_RESULT
        raise NotImplementedError

    def performance(self, dataset, value=None):
        """ Function의 결과를 요약하는 함수 """
        dataset[self._FUNCTION_NAME] = self._FUNC_RESULT
        perform_ds = dataset.loc[self._IN_CONDITION, 
                                [self._FUNCTION_NAME] + \
                                 dataset.get_targets()].copy()
        if value:
            return Dataset(
                perform_ds.fineclassing_cnt(self._FUNCTION_NAME, 
                                            nbins = 0, 
                                            target_value=value))
        else:
            return Dataset(
                perform_ds.fineclassing_cnt(self._FUNCTION_NAME, 
                                            nbins = 0))


class Cutout(Func):
    """ 단변량 조건식들로 분류
    """

    def __init__(self, condition="1=1") -> None:
        super().__init__()
        self._CONDITION = condition

    def set_cond(self, cond):
        self._CONDITION = cond
    def get_cond(self):
        return self._CONDITION

    def perform(self, dataset, cut_part=False):
        self._FUNC_RESULT = dataset.query("(" + self._CONDITION + ")")

    def performance(self, dataset):
        perform_ds = dataset[self._IN_CONDITION]

    
    def subset(self, dataset, recalc=True, cut=True):
        if recalc:
            self.perform(dataset)
        
        if cut:
            return Dataset(dataset[~self._CONDITION_RESULT])
        else: # remain
            return Dataset(dataset[self._CONDITION_RESULT])


class MatrixCondition(Func):
    def __init__(self, 
                 columns=['',''], 
                 column_bins=[None, None], 
                 cond=[]) -> None:
        """ Matrix Condition을 정의하는 클래스

        Matrix Condition을 정의하기 위해서는 X, Y 컬럼과 숫자형의 경우에는 컬럼 구분 기준,
        그리고 각 구간의 기준값이 필요

        Attributes:
            _COLUMNS (list): Matrix의 기준으로 활용할 컬럼명. 
                             _COLUMNS[0]:행, _COLUMNS[1]:열
            _BINS (list): 숫자형 컬럼의 경우에는 구간화된 구간정보. 
                           _INDEX[0]:행구간, _INDEX[1]:열구간
            _CONDITION (list): 각각 행열 구간에 대한 값. 
                               _CONDITION[행][열]=조건값
        """
        super().__init__()
        self._COLUMNS = columns
        self._BINS = column_bins
        self._CONDITION = cond
        

    def set_columns(self, varl):
        self._COLUMNS = varl
    def set_column(self, varn, index):
        self._COLUMNS[index] = varn
    
    def set_columns_bins(self, bins):
        self._BINS = bins
    def set_columns_bin(self, bin, index):
        """ 숫자형 컬럼의 경우에는 구간화를 위한 정보 저장 가능

        Args:
            bin: 컬럼 구간화 정보. pd.cut의 bins에 적용 가능해야 함
        """
        if self._COLUMNS[index]:
            self._BINS[index] = bin
        else:
            print("column 정의가 먼저 필요합니다.")
    
    def check_columns_filled(self) -> bool:
        check1 = (len(self._COLUMNS) == 2)
        check2 = self._COLUMNS[0] not in ['', None]
        check3 = self._COLUMNS[1] not in ['', None]
        return check1 and check2 and check3

    def check_bins_filled(self) -> bool:
        check1 = (len(self._BINS) == 2)
        check2 = self._BINS[0] not in ['', None]
        check3 = self._BINS[1] not in ['', None]
        return check1 and check2 and check3
    
    def perform(self):
        pass
    
    def performance(self):
        pass


class Proc(Func):
    """ Fuction 모음. 새로운 집계 기준
    """

        
    #     if self._FUNCTION_NAME in Func.FUNCTION_INSTANCES:
    #         print("Error: 중복된 Function 이름이 있습니다.")
    #     else:
    #         Func.FUNCTION_INSTANCES.append(self._FUNCTION_NAME)
    
    # def __call__(self, dataset):
    #     return self.perform(dataset)
    
    # def __del__(self):
    #     Func.FUNCTION_INSTANCES.remove(self._FUNCTION_NAME)
    
    # def set_name(self, name):
    #     self._FUNCTION_NAME = name
    #     Func.FUNCTION_INSTANCES[self.get_index()] = name
    # def get_name(self):
    #     return self._FUNCTION_NAME

    
    def __init__(self, funcs=[]) -> None:
        super().__init__()
        self._FUNCTIONS = funcs
    
    def set_proc_index(self, num):
        self.proc_index = num
    
    def append(self, fanc):
        self._FUNCTIONS.append(fanc)
    
    def perform(self, dataset):
        if self._FUNCTIONS:
            for f in self._FUNCTIONS:
                dataset = f.perform(dataset)
                print(len(dataset))
            return dataset
        else:
            return dataset
    
    def get_name(self):
        rslt = []
        for fanc in self._FUNCTIONS:
            rslt.append(fanc.get_name())
        return rslt
    
    def get_cond(self):
        rslt = []
        for fanc in self._FUNCTIONS:
            rslt.append(fanc.get_cond())
        return rslt

    def performance(self):
        rslt = pd.DataFrame()
        for idx, fanc in enumerate(self._FUNCTIONS):
            if idx == 0:
                rslt = fanc.perf()
                first_line = rslt.sum(axis=0)
                rslt = first_line.append(rslt, ignore_index=True)
            else:
                rslt = rslt.append(fanc.perf(), ignore_index=True)
        return rslt




#####################################################################
#  Model <- Functions
#####################################################################
class Model():
    def __init__(self) -> None:
        pass

    def predict(self, dataset):
        pass

    def get_inputs(self):
        pass

class ScoreCard(Model):
    """
    정보영역
    항목개수
    항목설명
    구간코드
    구간설명
    구간요건
    배점
    가중치
    """
    pass



#####################################################################
#  Strategy
#####################################################################
class Strategy():
    pass

class Hando(Strategy):
    pass


