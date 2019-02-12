import pandas as pd
import numpy as np
import glob
import os
import CONFIG
import csv

from Util.FinanceReportsFinder import *
from Util.Logger import myLogger

import matplotlib.pyplot as plt

logger = myLogger("DataProcessor")

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
        logger.logger.info("Read operating days and stock name/code info successfully.")

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
            df_to_map.loc[:, c][df_to_map.loc[:, c] == ""] = np.nan
            df_to_map.loc[:, c] = df_to_map.loc[:, c].astype(float, errors = 'ignore')

        for accnt in list_spot_accounts:
            df_to_map.loc[:, accnt] =  df_to_map.loc[:, accnt].fillna(method="ffill")

        for accnt in list_range_accounts:
            df_to_map.loc[:, accnt + "Avg"] = df_to_map.loc[:, accnt].rolling(range_years * 4).sum() / range_years

        return df_to_map

    def getDFmapped(self, code, start_date, end_date,\
                    dict_accounts, list_spot_accounts, list_range_accounts, range_years):
        df_process = self.getOpDaysByRange(start_date, end_date, range_years)
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

    def getHistoricalPBR(self, code, start_date, end_date):
        df_process, df_to_map = \
            dp.getDFmapped(code, start_date, end_date, CONFIG.PBR_DICT_ACCNTS, CONFIG.PBR_SPOT_ACNTS,
                           CONFIG.PBR_RANGE_ACCNTS, 1)

        # 시가총액 부분을 개선할 수 있음 <자사주 고려 시가총액>
        df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)

        df_process.loc[:, '시가총액'] = df_cap.values
        df_process.loc[:, 'PBR'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '총자본(천원)'] * 1000
        df_process.loc[:,'PBR'].plot()
        plt.show()

    def getHistoricalPER(self, code, start_date, end_date, range_years):
        df_process, df_to_map = \
            dp.getDFmapped(code, start_date, end_date, CONFIG.PER_DICT_ACCNTS, CONFIG.PER_SPOT_ACNTS,
                           CONFIG.PER_RANGE_ACCNTS, range_years)

        # 시가총액 부분을 개선할 수 있음 <자사주 고려 시가총액>
        df_cap = self.getStockInfoByRange("시가총액", code, start_date, end_date)

        df_process.loc[:, '시가총액'] = df_cap.values
        df_process.loc[:, 'PER'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '당기순이익(천원)'] * 1000
        df_process.loc[:, 'PER'].plot()
        plt.show()


if __name__ == "__main__":
    code = "005930"
    start_date = "20080101"
    end_date = "20190131"

    dp = DataProcessor()
    # dp.getHistoricalPBR(code, start_date, end_date)
    dp.getHistoricalPER(code, start_date, end_date, 7)
















