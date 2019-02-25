import numpy as np
import pandas as pd
import glob
import os

import CONFIG
import csv

from Util.FinanceReportsFinder import *
from Util.Logger import myLogger

logger = myLogger("DataProcessor")
# LIMIT_PCT_CHG_RANGE = [-30, 30]

class DataProcessor():
    def __init__(self):
        self.data_path = CONFIG.PATH['DATA']

        self.df_opdays = None
        self.df_codeinfo = None

        self.dict_path = self.getDictPath()
        self.getOpDaysAndCodeInfo()

    def getDictPath(self):
        dict_path = {}
        data_folders = [folder[0] for folder in os.walk(self.data_path)]
        for folder in data_folders:
            if folder.endswith("BS"):
                # files = glob.glob(folder + "\\*.CSV")
                dict_path["BS"] = folder
            elif folder.endswith("IS"):
                # files = glob.glob(folder + "\\*.CSV")
                dict_path["IS"] = folder
            elif folder.endswith("CFS"):
                # files = glob.glob(folder + "\\*.CSV")
                dict_path["CFS"] = folder
            elif folder.endswith("INFO"):
                # files = glob.glob(folder + "\\*.CSV")
                dict_path["INFO"] = folder
        return dict_path

    def getOpDaysAndCodeInfo(self):
        files = glob.glob(self.dict_path['INFO'] + "\\*.CSV")
        for file in files:
            name = file.split("\\")[-1].split(".")[0]
            if name == "영업일":
                df_opdays_temp = pd.read_csv(file, engine='python')
                self.df_opdays = pd.to_datetime(df_opdays_temp.iloc[:,0])
            elif name == "종목정보":
                self.df_codeinfo = pd.read_csv(file, engine='python', index_col=0)
        logger.logger.debug("Read operating days and stock name/code info successfully.")

    def getOpDaysByRange(self, start_date, end_date, range_years):
        range = self.df_opdays[(self.df_opdays >= start_date) & (self.df_opdays <= end_date)]
        df_process = pd.DataFrame(index=range)
        df_process.loc[:, 'StartYearQuater'] = \
            list(map(lambda x : getRangeYearQuaterByDate(x, range_years,"start"), df_process.index))
        df_process.loc[:, 'EndYearQuater'] = \
            list(map(lambda x: getRangeYearQuaterByDate(x, range_years, "end"), df_process.index))
        return df_process

    def getSpotFinancialData(self, code, year_quater, FR_type, list_accounts):
        """
        code,

        :param FR_type: BS, IS, CFS
        :param year_quater: YYYY_NQ 스타일
        :param list_accounts: 계정명 (정확해야함)
        :return:
        """
        str_code = "A" + str(code)
        file = self.dict_path[FR_type] + "\\" + year_quater + ".CSV"
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file)

            result = []
            list_index = []
            list_cols = []
            for i, row in enumerate(csv_reader):
                if i == 0:
                    for idx, c in enumerate(row):
                        if c in list_accounts:
                            list_index.append(idx)
                            list_cols.append(c)
                elif row[0] == "A" + code:
                    for idx in list_index:
                        result.append(row[idx])
        df = pd.DataFrame(result)
        df = df.T
        df.columns = list_cols
        df.index = [year_quater]
        return df

    def getMappingDF(self, code, list_year_quater, dict_accounts):
        """
        :param code:
        :param list_year_quater:
        :param dict_accounts: {"BS":[accts],
                                "IS":[accts]} -> 이런식으로
        :return:
        """
        for FR_type in dict_accounts:
            loop_count = 0
            for year_quater in list_year_quater:
                df = self.getSpotFinancialData(code, year_quater, FR_type, dict_accounts[FR_type])
                if loop_count == 0:
                    df_result_temp = df
                else:
                    df_result_temp = pd.concat([df_result_temp, df])
                loop_count += 1
            try:
                df_result = pd.concat([df_result, df_result_temp], axis=1)
            except:
                df_result = df_result_temp

        return df_result

    def preprocessMappingDF(self, df_to_map, list_spot_accounts, list_range_accounts, range_years):
        # to int
        for c in df_to_map.columns:
            df_to_map.loc[:, c] = df_to_map.loc[:, c].str.replace(",", "")
            df_to_map.loc[:, c] = df_to_map.loc[:,c].replace("", np.nan)
            df_to_map.loc[:, c] = df_to_map.loc[:, c].astype(float, errors = 'ignore')

        for accnt in list_spot_accounts:
            df_to_map.loc[:, accnt] =  df_to_map.loc[:, accnt].fillna(method="ffill")

        for accnt in list_range_accounts:
            df_to_map.loc[:, accnt + "Avg"] = df_to_map.loc[:, accnt].rolling(range_years * 4).sum() / range_years

        return df_to_map

    def getDFmapped(self, code, start_date, end_date,\
                    dict_accounts, list_spot_accounts, list_range_accounts, range_years):
        df_process = self.getOpDaysByRange(start_date, end_date, range_years)
        # print(df_process)
        list_year_quater = getListYearQuater(df_process)

        df_to_map = self.getMappingDF(code, list_year_quater, dict_accounts)
        df_to_map = self.preprocessMappingDF(df_to_map, list_spot_accounts, list_range_accounts, range_years)

        # Spot 데이터 삽입
        for accnt in list_spot_accounts:
            df_process.loc[:, accnt] = df_process.loc[:, 'StartYearQuater'].map(lambda x: df_to_map.loc[x, accnt])

        for accnt in list_range_accounts:
            df_process.loc[:, accnt] = df_process.loc[:, 'StartYearQuater'].map(lambda x: df_to_map.loc[x, accnt + "Avg"])

        return df_process, df_to_map

    def getStockInfoByRange(self, info_type, code, start, end):
        str_code = "A" + str(code)
        file = self.dict_path["INFO"] + "\\" + info_type + ".CSV"
        # type can be "보통주수", "수정주가", "시가총액", "자사주수", "종목정보"

        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file)

            columns = None
            data = None
            for i, row in enumerate(csv_reader):
                if i == 0:
                    columns = row

                elif row[0] == "A" + code:
                    data = row
                    break

        result = pd.DataFrame(data).T
        result.columns = columns
        result = result.set_index('Symbol').iloc[:, 1:]
        result.columns = pd.to_datetime(result.columns)
        result = result.loc[:, (result.columns >= start) & (result.columns <= end)]

        result = result.T
        result = result.iloc[:, 0].str.replace(",", "")
        result[result == ""] = np.nan
        result = result.astype(float, errors='ignore')

        return result

    def getCap(self, code, start_date, end_date, csd_trea=True, fixcap=False):
        if fixcap == True:
            return self.getAbnorFixedCap(code, start_date, end_date, csd_trea)
        elif fixcap == False:
            return self.getNorCap(code,start_date,end_date,csd_trea)


    def getNorCap(self, code, start_date, end_date, csd_trea=True):
        # csd_trea : 자사주 매입을 고려한 시가총액
        if csd_trea == False:
            df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)
        elif csd_trea == True:
            df_price = self.getStockInfoByRange("종가", code, start_date, end_date)
            df_stocks = self.getStockInfoByRange("보통주수", code, start_date, end_date)
            df_trea = self.getStockInfoByRange("자사주수", code, start_date, end_date)
            df_cap_trea = df_price * (df_stocks - df_trea)
            df_cap_trea = df_cap_trea / 10 ** 6
            df_cap = df_cap_trea
        return df_cap

    def getAbnorFixedCap(self, code, start_date, end_date, csd_trea = True):
        LIMIT_PCT_CHG_RANGE = [-30, 30]
        # 일단 수직적 이상만 탐지하여 개선

        # Considering treasury stocks cap.
        df_price = self.getStockInfoByRange("종가", code, start_date, end_date)
        df_stocks = self.getStockInfoByRange("보통주수", code, start_date, end_date)
        df_trea = self.getStockInfoByRange("자사주수", code, start_date, end_date)
        df_cap_trea = df_price * (df_stocks - df_trea)
        df_cap_trea = df_cap_trea / 10 ** 6

        # Not consdiering treasury stocks cap.
        df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)

        df_cap_total = pd.concat([df_cap, df_cap_trea], axis=1)
        df_cap_pct_chg = df_cap_total.pct_change(1) * 100
        len_cols = len(df_cap_pct_chg.columns)

        for i in range(len_cols):
            list_abnormaly_date = []
            sr = df_cap_pct_chg.iloc[:, i]
            sr_abnormaly = sr[(sr < LIMIT_PCT_CHG_RANGE[0]) | (sr > LIMIT_PCT_CHG_RANGE[1])]
            list_abnormaly_date = list_abnormaly_date + list(sr_abnormaly.index)

        count_loop = len(list_abnormaly_date) / 2

        LIMIT_PCT_CHG_RANGE = [-30, 30]

        len_cols = len(df_cap_pct_chg.columns)

        # df_cap_total의 column 별로 수직적 분석을 하기 위한 loop
        for i in range(len_cols):
            list_abnormaly_date = []
            sr = df_cap_pct_chg.iloc[:, i]
            # 전일대비 pct_chg가 -30%, +30%를 넘을때 그때의 날짜를 저장
            sr_abnormaly = sr[(sr < LIMIT_PCT_CHG_RANGE[0]) | (sr > LIMIT_PCT_CHG_RANGE[1])]
            list_abnormaly_date = list_abnormaly_date + list(sr_abnormaly.index)

            # 날짜가 ["2015-01-01","2015-01-05", "2016-03-05","2016-04-07"] 이렇게 나온다면,
            # 2015-01-05 데이터로 2015-01-01 ~ 2015-01-05의 데이터를 채워버린다.
            # 2016-04-07 데이터로 2016-03-05 ~ 2016-04-07의 데이터를 채워버린다.
            # Anormaly detection에 대해서 알아보기.

            if len(list_abnormaly_date) % 2 != 0:
                raise ValueError("Unexpected value got. You have to how these inputs get in.")

            count_loop = int(len(list_abnormaly_date) / 2)
            for j in range(count_loop):
                df_cap_total[list_abnormaly_date[j * 2]: list_abnormaly_date[j * 2 + 1]][:-1].iloc[:, i] \
                    = df_cap_total[list_abnormaly_date[j * 2]: list_abnormaly_date[j * 2 + 1]].iloc[-1, i]

        if csd_trea == True:
            return df_cap_total.iloc[:,1]
        elif csd_trea == False:
            return df_cap_total.iloc[:, 0]













    # def getHistoricalPBR(self, code, start_date, end_date):
    #     df_process, df_to_map = \
    #         self.getDFmapped(code, start_date, end_date, CONFIG.PBR_DICT_ACCNTS, CONFIG.PBR_SPOT_ACNTS,
    #                        CONFIG.PBR_RANGE_ACCNTS, 1)
    #
    #     # 시가총액 부분을 개선할 수 있음 <자사주 고려 시가총액>
    #     df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)
    #
    #     df_process.loc[:, '시가총액'] = df_cap.values
    #     df_process.loc[:, 'PBR'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '총자본(천원)'] * 1000
    #
    #     return df_process
    #     # df_process.loc[:,'PBR'].plot()
    #     # plt.show()
    #
    # def getHistoricalPER(self, code, start_date, end_date, range_years):
    #     # print(1)
    #     df_process, df_to_map = \
    #         self.getDFmapped(code, start_date, end_date, CONFIG.PER_DICT_ACCNTS, CONFIG.PER_SPOT_ACNTS,
    #                        CONFIG.PER_RANGE_ACCNTS, range_years)
    #
    #     # 시가총액 부분을 개선할 수 있음 <자사주 고려 시가총액>
    #     df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)
    #
    #     df_process.loc[:, '시가총액'] = df_cap.values
    #     df_process.loc[:, 'PER'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '당기순이익(천원)'] * 1000
    #
    #     return df_process
    #     # df_process.loc[:, 'PER'].plot()
    #     # plt.show()
    #
    # def getHistoricalROE(self, code, start_date, end_date, range_years):
    #
    #     df_process, df_to_map = \
    #         self.getDFmapped(code, start_date, end_date, CONFIG.ROE_DICT_ACCNTS, CONFIG.ROE_SPOT_ACNTS,
    #                        CONFIG.ROE_RANGE_ACCNTS, range_years)
    #
    #     df_process.loc[:, 'ROE'] = df_process.loc[:, '당기순이익(천원)'] / df_process.loc[:, '총자본(천원)'] * 100
    #
    #     # return df_process
    #     df_process.loc[:, 'ROE'].plot()
    #     plt.show()



if __name__ == "__main__":
    code = "049430"
    start_date = "20080101"
    end_date = "20190131"

    dp = DataProcessor()
    # df= dp.getHistoricalPBR(code, start_date, end_date)
    # print(df.head())
    dp.getHistoricalROE(code, start_date, end_date, 3)
















