
def getSpotYearQuaterByDate(date):
    year = date.year
    month = date.month
    day = date.day

    if month < 4:
        r_year = year - 1
        r_quater = "3Q"
    elif month < 6:
        r_year = year - 1
        r_quater = "4Q"
    elif month < 9:
        r_year = year
        r_quater = "1Q"
    elif month < 12:
        r_year = year
        r_quater = "2Q"
    else:
        r_year = year
        r_quater = "3Q"

    return str(r_year) + "_" + r_quater

def getRangeYearQuaterByDate(date, years, option):
    year_quater = getSpotYearQuaterByDate(date)
    year = int(year_quater.split("_")[0]) # int
    quater = int(year_quater.split("_")[-1][0]) # int

    list_year_quater = []

    if quater == 4:
        for i in range(years):
            r_year = year - i
            list_year_quater.append(str(r_year) + "_4Q")
    else:
        for i in range(years + 2):
            if i == 0:
                r_year = year - i
                list_year_quater.append(str(r_year) + "_" + str(quater) +"Q")
            elif i == years + 1:
                r_year = year - i + 1
                list_year_quater.append(str(r_year) + "_" + str(quater) + "Q")
            else:
                r_year = year - i
                list_year_quater.append(str(r_year) + "_4Q")

    if option == "start":
        ret = list_year_quater[0]
    elif option == "end":
        ret = list_year_quater[-1]
    return ret


def getListYearQuater(df_process):
    end_year_quater = df_process.iloc[-1, 0]
    start_year_quater = df_process.iloc[0, 1]
    start_year = int(start_year_quater.split("_")[0])
    end_year = int(end_year_quater.split("_")[0])

    list_year_quater = []
    bool_start = False
    bool_end = False
    for year in range(start_year, end_year + 1):
        for quater in range(1, 5):
            ret = str(year) + "_" + str(quater) + "Q"
            if ret == start_year_quater:
                bool_start = True

            if bool_start and not bool_end:
                list_year_quater.append(ret)

            if ret == end_year_quater:
                bool_end = True
    return list_year_quater






