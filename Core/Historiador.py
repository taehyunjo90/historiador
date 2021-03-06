import matplotlib.pyplot as plt

from Core.DataProcessor import DataProcessor

import CONFIG

class Historiador():

    def __init__(self):
        self.dp = DataProcessor()

    def getHistoricalPBR(self, code, start_date, end_date, csd_trea = True, fixcap = False):
        df_process, df_to_map = \
            self.dp.getDFmapped(code, start_date, end_date, CONFIG.PBR_DICT_ACCNTS, CONFIG.PBR_SPOT_ACNTS,
                           CONFIG.PBR_RANGE_ACCNTS, 0)

        df_cap = self.dp.getCap(code, start_date, end_date, csd_trea, fixcap)

        df_process.loc[:, '시가총액'] = df_cap.values
        df_process.loc[:, 'PBR'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '총자본(천원)'] * 1000

        return df_process

    def getHistoricalPER(self, code, start_date, end_date, range_years, csd_trea = True, fixcap = False):
        df_process, df_to_map = \
            self.dp.getDFmapped(code, start_date, end_date, CONFIG.PER_DICT_ACCNTS, CONFIG.PER_SPOT_ACNTS,
                           CONFIG.PER_RANGE_ACCNTS, range_years)

        df_cap = self.dp.getCap(code, start_date, end_date, csd_trea, fixcap)

        df_process.loc[:, '시가총액'] = df_cap.values
        df_process.loc[:, 'PER'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '당기순이익(천원)'] * 1000

        return df_process

    def getHistoricalROE(self, code, start_date, end_date, range_years, fixcap = False):

        df_process, df_to_map = \
            self.dp.getDFmapped(code, start_date, end_date, CONFIG.ROE_DICT_ACCNTS, CONFIG.ROE_SPOT_ACNTS,
                           CONFIG.ROE_RANGE_ACCNTS, range_years)

        df_process.loc[:, 'ROE'] = df_process.loc[:, '당기순이익(천원)'] / df_process.loc[:, '총자본(천원)'] * 100

        return df_process
        # df_process.loc[:, 'ROE'].plot()
        # plt.show()

    def getHistoricalPBRandROE(self, code, start_date, end_date, range_years, csd_trea = True, fixcap = False):
        df_process, df_to_map = \
            self.dp.getDFmapped(code, start_date, end_date, CONFIG.ROE_DICT_ACCNTS, CONFIG.ROE_SPOT_ACNTS,
                           CONFIG.ROE_RANGE_ACCNTS, range_years)

        df_cap = self.dp.getCap(code, start_date, end_date, csd_trea, fixcap)

        df_process.loc[:, '시가총액'] = df_cap.values
        df_process.loc[:, 'PBR'] = df_process.loc[:, '시가총액'] / df_process.loc[:, '총자본(천원)'] * 1000
        df_process.loc[:, 'ROE'] = df_process.loc[:, '당기순이익(천원)'] / df_process.loc[:, '총자본(천원)'] * 100

        return df_process



if __name__ == "__main__":
    code = "005710"
    start_date = "20080101"
    end_date = "20190131"

    hs = Historiador()
    df = hs.getHistoricalPBR(code, start_date, end_date, True)
    print(df.head())
    # hs.getHistoricalPBRandROE(code, start_date, end_date, 1, True)