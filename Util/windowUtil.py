import datetime

def checkDateValidate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y%m%d')
        return True
    except ValueError:
        return False

def checkCodes(code, df):
    len_code = len(code)

    if len_code < 6:
        return False, "no-enter"

    elif len_code == 6:
        try:
            stock_name = df.loc["A" + code, :][0]
            return True, stock_name
        except KeyError:
            return False, "no-exist"

    else:
        return False, "no-format"

def qtDateToString(date):
    year = date.year()
    year = str(year)

    month = date.month()
    month = "{0:0=2d}".format(month)

    day = date.day()
    day = "{0:0=2d}".format(day)

    return year + month + day


