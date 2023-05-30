import datetime
import time

def TIME_STAMP():
    return datetime.datetime.now().strftime("%Y%m%dZ%Hh%Mm%Ss")

def time_to_datetime(time):
    return datetime.datetime.strptime(f'{time.tm_year}-{time.tm_mon}-{time.tm_mday}', "%Y-%m-%d")

def week_to_date(weektime):
    # 'YYYYWWNN.N'
    weektime = weektime.lower()
    (year_str, rest_str) = weektime.split('ww')  # type: (str, str)
    if rest_str.find('.') > 0:
        (week_str, day_str) = rest_str.split('.')
    else:
        week_str = rest_str
        day_str = '5'
    year = int(year_str)
    week = int(week_str)
    day = int(day_str)
    if day == 7:
        day = 0
    assert (week > 0 and week < 54)
    assert (day >= 0 and day < 7)
    #now = datetime.datetime.now()
    #this_year = int(now.strftime("%Y"))
    #assert (year >= 2020 and year <= this_year + 1)

    print(f'time 1 {year}.{week}.{day}')

    # get first day of that year
    cal_data_first = datetime.datetime(year,1,1).isocalendar()
    weekyear_first = int(cal_data_first[0])
    weeknum_first = int(cal_data_first[1])
    weekday_first = int(cal_data_first[2])
    print(f'this new year {weekyear_first}.{weeknum_first}.{weekday_first}')

    if week == 1 and day < weekday_first:
        if weekday_first == 7 and year == weekyear_first + 1:
            y = year
            m = 1
            d = day + 1
        else:
            y = year - 1
            m = 12
            d = 31 - weekday_first + day + 1
    elif week == 1 and day == 0:
        y = year
        m = 1
        day = 1
    else:
        day0 = (week - 2) * 7
        if weekday_first==7:
            day1 = 7
        else:
            day1 = 7 - weekday_first

        day2 = day + 1
        day = abs(day0+day1+day2)

        print(f'day = {day0} + {day1} + {day2} = {day}')
        a = time.strptime(f'{year}-{day}', '%Y-%j')
        y = int(a.tm_year)
        m = int(a.tm_mon)
        d = int(a.tm_mday)

    timestamp =  f'{y}-{m}-{d}'
    print(f'ww {weektime} -> {year}-{week}-{day} => {timestamp}')
    return timestamp

def date_to_week(download_time):
    my_time = time.strptime(str(download_time), "%Y-%m-%d")
    daynum = int(my_time.tm_yday)
    weekday = (int(my_time.tm_wday)+1)%7
    year = int(my_time.tm_year)
    day = int(my_time.tm_mday)

    cal_data_first = datetime.datetime(year,1,1).isocalendar()
    weekyear_first = int(cal_data_first[0])
    weeknum_first = int(cal_data_first[1])
    weekday_first = int(cal_data_first[2])
    print(f'this new year {weekyear_first}.{weeknum_first}.{weekday_first}')

    if weekday_first == 7:
        weekday_first = 0

    if daynum <= 7:
        if daynum == 7 and weekday_first == 0:
            weeknum = 1
        else:
            weeknum = int((daynum + weekday_first - 1) / 7) + 1
    else:
        weeknum = int((daynum + weekday_first - 1) / 7) + 1

    print(f'date 1 {year}.{weeknum}.{weekday}')

    if weeknum in (52, 53, 54) and day > 25:
        if 31 + 1 - day + weekday < 7:
            year += 1
            weeknum = 1
    print(f'date 2 {year}.{weeknum}.{weekday}')
    return (year, weeknum, weekday)


def test1(week):
    t = week_to_date(week)
    y,w, d = date_to_week(t)
    print(f'====={week}==>{t}===>{y}WW{w}.{d}===============')
    assert(week.upper() == f"{y}WW{w}.{d}")

def test2(date):
    y,w, d  = date_to_week(date)
    s = f'{y}WW{w}.{d}'
    t = week_to_date(s)
    print(f'====={date}===>{y}WW{w}.{d}==>{t}===============')
    assert(date==t)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #test2('2000-12-24')
    #test1('2001WW2.0')
    #test1('2001WW2.5')
    for year in range(2000, 2050):
        for week in (1,2,52):
            for day in range(0, 7):
                test1(f'{year}WW{week}.{day}')

    for year in range(2000, 2050):
        for month in (1,12):
            for day in range(1, 32):
                test2(f'{year}-{month}-{day}')

