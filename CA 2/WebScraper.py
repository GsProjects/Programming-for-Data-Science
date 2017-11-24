import bs4
from bs4 import BeautifulSoup
from urllib.request import urlopen
import calendar
import mysql.connector
from datetime import datetime


def get_html():
    url = 'https://en.wikipedia.org/wiki/List_of_Presidents_of_the_United_States'
    html_content = urlopen(url)
    content = BeautifulSoup(html_content, "lxml")
    html_content.close()
    return content


def parse_html(content):
    tables = content.find_all('table', {'class': 'wikitable'})  # look for all tables with class wikitable
    president_table = tables[0]
    table_rows = president_table.find_all('tr')
    start_rows = 2  # first two rows contain headers
    new_index = 2
    for index, rows in enumerate(table_rows[start_rows:],start=2):  # index starts at 2 to skip first two rows
        if new_index < len(table_rows):
            row = table_rows[new_index]
            if len(row.td.attrs) > 0:  # if the td tag has one or more attributes
                if 'rowspan' in row.td.attrs:  # if theres a rowspan
                    attribute = row.td.attrs['rowspan']
                    num_merged = int(attribute)
                    merged_rows = [items for items in table_rows[new_index: new_index + num_merged]]
                    parse_rows(merged_rows)
                    merged_rows = []
                    new_index = new_index + num_merged
                    num_merged = 0

                else:  # if not a rowspan attribute
                    parse_rows(row)
                    new_index += 1

            else:
                new_index += 1
                parse_rows(row)


def remove_tags(data):  # removes the citation data in the cells
    unwanted_tags = ['sup','br']
    for element in data([item for item in unwanted_tags]):
        element.decompose()
    return data


def parse_rows(rows):
    table_data = []
    for items in rows:  # for each td element in the list
        if len(items) >= 1:
            if type(items) is not bs4.element.NavigableString:
                if items.name =='td':
                    table_data.append(items)  # if the rowspan is one

                else:
                    #  if the president has multiple rows
                    table_data.extend(items.findAll('td'))  # get all the td elements in the row

    td_data = parse_td_data(table_data)
    separate_data(td_data)
    return True


def separate_data(president_rows):
    parsed_row =[]
    if len(president_rows) > 0:
        for item in president_rows:

            if type(item) is not bs4.element.NavigableString:
                text = item.get_text()
                text.strip('')
                text = text.replace('\n',' ')
                text = text.replace('\n–\n',' ')
                text = text.replace("\xa0",'')
                text = text.replace("National Union April 15, 1865 – c.\u20091868",'National Union') #  special case for andrew johnson
                text = text.replace("Democratic c.\u20091868 – March 4, 1869 ", 'Democratic')
                parsed_row.append(text)
        if len(parsed_row) > 0:
            prep_data(parsed_row)


def parse_td_data(data):

    removal_values = [0,1,2,2]
    if len(data) > 8 :
        for items in removal_values:
            data.remove(data[items])

        for items in data:
            if len(items.get_text()) >= 15 and len(items.get_text()) <= 18:  # remove data from term column
                data.remove(items)

            if len(items.get_text()) >= 23 and len(items.get_text()) <= 24:  # special case for when the term data is longer than normal e.g Abraham Lincoln
                data.remove(items)

    elif len(data) <= 8:
        removal_values = [0, 1, 2]

        for items in removal_values:
            data.remove(data[items])

        for items in data:
            if len(items.get_text()) >= 15 and len(items.get_text()) <= 18:
                data.remove(items)

            if len(items.get_text()) >= 23 and len(items.get_text()) <= 24:  # special case for when the term data is longer than normal e.g Abraham Lincoln
                data.remove(items)

    return data


def prep_data(data):
    information =[]

    #  split the presidency dates
    presidency_dates = data[0].split('–')  # possible encoding error with the hyphen as the mac hyphen will not work in the split function

    #  split the president information
    president_info = parse_president_info(data)
    if len(data) >= 4:

        #  if they died in office
        presidency_info = presidency_information(presidency_dates)

        information.extend(presidency_info)
        information.extend(president_info)  # set to '' at top if nothing is found


        # DO THIS:   special case where date accompanies the whig party for john tyler
        if len(data[2]) == 39:
            if data[2].split()[0] == 'Whig':
                information.append({'Party': data[2].split()[0]})
        else:
            information.append({'Party':data[2]})  # appends the party name

        if len(data) >= 4:
            vp_data = vp_info(data[3], presidency_info[0], presidency_info[1],information)
            information.extend(vp_data)

        if len(data) >= 5:
            if len(data[4]) == 16:
                data.remove(data[4])  # exception case where the term date is not caught
            vp_data = vp_info(data[4], presidency_info[0], presidency_info[1],information)
            information.extend(vp_data)

        if len(data) >= 6:
            vp_data = vp_info(data[5], presidency_info[0], presidency_info[1],information)
            information.extend(vp_data)

        if len(data) >= 7:
            vp_data = vp_info(data[6], presidency_info[0], presidency_info[1],information)
            information.extend(vp_data)

        prepare_insert(information)


def parse_president_info(data):
    president_info = []
    president_name = '' 
    new_data = []

    for index, items in enumerate(data[1].split()):
        if items == '(Lived:' or items == 'years)' or items == 'years' or items == 'old)' or items == 'Born':
            items = ''
        if len(items) > 1:  # remove the spaces left by the previous if statement
            if items[0] == '(':  # if the age is displayed as (93 only take everything after the (
                items = items[1:]
            president_info.append(items)

    year_of_birth = president_info[-2]
    if '–' in year_of_birth:
        hyphen_index = year_of_birth.index('–')
        year_of_birth = ''.join(year_of_birth[:hyphen_index])

    president_info.remove(president_info[-2])  # remove the year the president was born and or died

    for items in president_info[:-1]:
        president_name += items + ' '

    president_age = president_info[-1]

    new_data.append({'President_Name':president_name})
    new_data.append({'Year_of_Birth':year_of_birth})
    new_data.append({'President_Age':president_age})
    return new_data


def presidency_information(presidency_dates):

    new_data =[]
    status = ['(Died', '(Resigned', '(Succeeded']
    for items in status:
        for elements in presidency_dates[1].split():
            if items == elements:
                presidential_status = items[1:]  # remove the bracket

                presidency_dates[1] = presidency_dates[1][ :presidency_dates[1].index(items)]  # get the date up until the status

                new_data.append({'Presidency_Start': datetime.strptime(presidency_dates[0].strip(' ').replace(',',''), '%B %d %Y').date()})
                new_data.append({'Presidency_End': datetime.strptime(presidency_dates[1].strip(' ').replace(',',''), '%B %d %Y').date()})
                new_data.append({'Status':presidential_status})
    if len(new_data) == 0:
        if presidency_dates[1].strip(' ') == 'Incumbent':
            new_data.append({'Presidency_Start': datetime.strptime(presidency_dates[0].strip(' ').replace(',', ''), '%B %d %Y').date()})
            new_data.append({'Presidency_End': datetime.strptime(str(datetime.today().strftime('%B %d %Y')), '%B %d %Y' ).date()})
            new_data.append({'Status': ''})  # add an empty field to represent status...for easier insertion in db

        else:
            new_data.append({'Presidency_Start': datetime.strptime(presidency_dates[0].strip(' ').replace(',',''), '%B %d %Y').date()})
            new_data.append({'Presidency_End': datetime.strptime(presidency_dates[1].strip(' ').replace(',',''), '%B %d %Y').date()})
            new_data.append({'Status':''})

    return new_data


def vp_info(data, start_vacancy, end_vacancy,information):

    status = ['(Died', '(Resigned', '(Succeeded', '(Balance']
    new_data =[]
    first_vp_data = data
    if data == 'Office vacant':  # if the vp is vacant for the entire presidency use presidency dates of vacancy dates
        new_data.append({'Vacant': data})
        new_data.append({'Vacant_Start': start_vacancy['Presidency_Start']})
        new_data.append({'Vacant_End': end_vacancy['Presidency_End']})

    elif len(data.split()) > 1 and len(data.split()) <= 4:  # if theres only one vice president, len of <=4 for people like George H. W. Bush
        new_data.append({'Vice_President_Name': data})
    elif len(data.split()) > 0 and '–' not in data.split(): #  if the vice president had one of the statuses after their name with no date
        for items in status:
            if items in data.split():
                vp_name = ' '.join(data.split()[ :data.split().index(items)])

                if vp_name == 'Office vacant':
                    # if office vacant for balance get previous vp dates so adjust parameters
                    previous_vp_data = information[-2:]
                    keys =[]
                    dates =[]
                    for items in previous_vp_data:
                        for key,value in items.items():
                            keys.append(key)
                            dates.append(value)

                    if 'Vice_President_Start' == keys[0] and 'Vice_President_End' == keys[1]:
                        new_data.append({'Vacant': vp_name})
                        new_data.append({'Vacant_Start': dates[0]})
                        new_data.append({'Vacant_End': dates[1]})
                else:
                    # JOHN TYLER
                    new_data.append({'Vice_President_Name': vp_name})

    else:
        for elements in first_vp_data.split():
            if elements == '–':
               hyphen_index = first_vp_data.split().index(elements)
               if first_vp_data.split()[ hyphen_index - 3] in calendar.month_name:
                   first_vp_name = first_vp_data.split()[ : hyphen_index - 3]
                   vp_name = ' '.join(first_vp_name)

                   if vp_name == 'Office vacant':
                       end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                       start_date = first_vp_data.split()[hyphen_index - 3: hyphen_index]
                       start_date = ' '.join(start_date)

                       new_data.append({'Vacant': vp_name})
                       new_data.append({'Vacant_Start': datetime.strptime(start_date.strip(' ').replace(',',''), '%B %d %Y').date()})
                       new_data.append({'Vacant_End': datetime.strptime(end_date.strip(' ').replace(',',''), '%B %d %Y').date()})

                   else:
                       if vp_name != 'Unaffiliated':
                           end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                           start_date = first_vp_data.split()[hyphen_index - 3: hyphen_index]
                           start_date = ' '.join(start_date)

                           new_data.append({'Vice_President_Name': vp_name})
                           new_data.append({'Vice_President_Start': datetime.strptime(start_date.strip(' ').replace(',',''), '%B %d %Y').date()})
                           new_data.append({'Vice_President_End': datetime.strptime(end_date.strip(' ').replace(',',''), '%B %d %Y').date()})


               elif first_vp_data.split()[ hyphen_index - 2] in calendar.month_name:
                   first_vp_name = first_vp_data.split()[: hyphen_index - 2]
                   vp_name = ' '.join(first_vp_name)

                   if vp_name == 'Office vacant':
                       end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                       start_date = first_vp_data.split()[hyphen_index - 2: hyphen_index]
                       start_date.append(end_date.split()[2])
                       start_date = ' '.join(start_date)
                       #  if the year is missing because because they died or left in the same year then get the year from the end date

                       new_data.append({'Vacant': vp_name})
                       new_data.append({'Vacant_Start': datetime.strptime(start_date.strip(' ').replace(',',''), '%B %d %Y').date()})
                       new_data.append({'Vacant_End': datetime.strptime(end_date.strip(' ').replace(',',''), '%B %d %Y').date()})

                   else:
                       end_date = ' '.join(first_vp_data.split()[hyphen_index + 1: hyphen_index + 4])
                       start_date = first_vp_data.split()[hyphen_index - 2: hyphen_index]
                       start_date.append(end_date.split()[2])
                       start_date = ' '.join(start_date)

                       new_data.append({'Vice_President_Name': vp_name})
                       new_data.append({'Vice_President_Start': datetime.strptime(start_date.strip(' ').replace(',',''), '%B %d %Y').date()})
                       new_data.append({'Vice_President_End': datetime.strptime(end_date.strip(' ').replace(',',''), '%B %d %Y').date()})
    return new_data


def prepare_insert(information):

    search_values = ['Vice','Vacant']
    vice_president_table =[]
    president_table = []

    for dictionaries in information:
        for key,value in dictionaries.items():
            if search_values[0] in key or search_values[1] in key:
                vice_president_table.append(dictionaries)
            else:
                president_table.append(dictionaries)

    if(len(vice_president_table) > 0 ):  # add the president to all the vice president info
        vice_president_table.append(information[3])



    table_name_1 = 'Presidents'
    table_name_2 = 'Vice_President'
    table_name_3 = 'Vacant'
    data =[]
    insert_data(president_table,table_name_1)
    if len(vice_president_table) > 2:
        if len(vice_president_table) == 4: # send the data as is to the vacant table
            insert_data(vice_president_table, table_name_3)
        elif len(vice_president_table) > 4:
            new_index = 0
            for index,dictionaries in enumerate(vice_president_table):
                for key, value in vice_president_table[new_index].items():
                    if 'Vice_President' in key:
                        start = vice_president_table[new_index + 1]
                        end = vice_president_table[new_index + 2]
                        data.append({key:value})
                        data.append(start)
                        data.append(end)
                        data.append(vice_president_table[-1])
                        new_index = new_index +  3

                        insert_data(data, table_name_2)
                        data = []

                    if 'Vacant' in key:
                        start = vice_president_table[new_index + 1]
                        end = vice_president_table[new_index + 2]
                        data.append({key: value})
                        data.append(start)
                        data.append(end)
                        data.append(vice_president_table[-1])

                        new_index = new_index + 3

                        insert_data(data, table_name_3)
                        data = []


    else:
        # INSERT INTO VICE PRESIDENT TABLE
        insert_data(vice_president_table, table_name_2)


def insert_data(president_data, name):
    column_names =[]
    column_data = []
    values ='('

    for dictionaries in president_data:
        for key,value in dictionaries.items():
            column_names.append(key)
            column_data.append(value)

    for items in column_data:
        values += '%s, '

    values = values[:-2]  # remove the last space and comma
    values += ');'

    insert_statement = 'Insert into ' + name + ' ('
    insert_statement += ', '.join(column_names)
    insert_statement += ')'
    insert_statement += ' values ' + values

    perform_insert(insert_statement, column_data)


def perform_insert(statement, column_data):
    conn = create_connection()
    cursor = conn.cursor()
    query =(statement)
    cursor.execute(query, [items for items in column_data])
    conn.commit()
    cursor.close()
    conn.close()


def get_states():
    url = 'https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#States'
    html_content = urlopen(url)
    content = BeautifulSoup(html_content, "lxml")
    html_content.close()
    tables = content.find_all('table')


    table_rows = tables[0].find_all('tr')
    states = []
    for row in table_rows:
        if row.th:
            state = row.th.get_text()
            if '[' in state:
                index = state.index('[')
                state = state[:index]
                states.append(state.strip(' '))
            else:
                states.append(state.strip(' '))

    states.remove(states[0])
    states.remove(states[0])
    return states







def get_extra_data():
    conn = create_connection()
    cursor = conn.cursor()
    query = ('Select President_Name from Presidents;')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    url = 'https://en.m.wikipedia.org/wiki/'
    num = 0
    for items in result:
        num+=1
        items[0].strip(' ')
        new_url = url + items[0].replace(' ','_')

        html_content = urlopen(new_url)
        content = BeautifulSoup(html_content, "lxml")
        html_content.close()

        tables = content.find_all('table', {'class': 'infobox vcard'})

        info = []
        info_table = tables[0].find_all('tr')

        for index,rows in enumerate(info_table):
            row = info_table[index]
            if row.th:

                if row.th.get_text() == 'Born':
                    info.append(row)

                    if  info_table[index + 1].th.get_text() == 'Died':
                        info.append(info_table[index + 1])
                        index +=2

        parse_new_data(info, items[0])


def parse_new_data(data, president_name):

    info = []
    if len(data) == 2:
        born = data[0].find_all('span',{'class':'bday'})
        birth_date = datetime.strptime(born[0].get_text(), '%Y-%m-%d').date()
        death = data[1].find_all('span', {'class': 'dday deathdate'})
        death_date = datetime.strptime(death[0].get_text(), '%Y-%m-%d').date()

        if data[0].get_text().split()[-1] == 'U.S.' or data[0].get_text().split()[-1] == 'U.S.)' or data[0].get_text().split()[-1] == 'U.S.),':
            state = data[0].get_text().split()[-2]
            if state.replace(',','') == 'Carolina':
                state = data[0].get_text().split()[-3] + ' Carolina'

            if state == 'Massachusetts,':
                state = 'Massachusetts'
            if state == 'D.C.,':
                state = 'Washington'
            elif state == 'York,':
                state = 'New York'
            elif state.replace(',','') == 'Jersey':
                state = 'New Jersey'
            elif state == 'Hampshire':
                state = 'New Hampshire'
            elif state == 'America':

                if data[0].get_text().split()[-3].replace(',','') == 'Carolina':
                    state = 'Carolina'
                else:
                    state = 'Virginia'
            else:
                state = state.replace(',','')
        else:
            state = data[0].get_text().split()[-1]
            if state.replace(',', '') == 'Carolina':
                state = data[0].get_text().split()[-2] + ' Carolina'

            if state == 'Massachusetts,':
                state = 'Massachusetts'
            if state == 'D.C.,':
                state = 'Washington'
            elif state == 'York,':
                state = 'New York'
            elif state == 'Jersey':
                state = 'New Jersey'
            elif state == 'Hampshire':
                state = 'New Hampshire'
            elif state == 'America':

                if data[0].get_text().split()[-3].replace(',','') == 'Carolina':
                    state =data[0].get_text().split()[-4] +' Carolina'
                else:
                    state = 'Virginia'
            else:
                state = state.replace(',', '')

        info.append(birth_date)
        info.append(death_date)
        info.append(state)
        info.append(president_name.strip(' '))
        insert_new_data(info)


    elif len(data) == 1:
        born = data[0].find_all('span', {'class': 'bday'})
        birth_date = datetime.strptime(born[0].get_text(), '%Y-%m-%d').date()

        if data[0].get_text().split()[-1] == 'City':
            state = 'New York'
        if data[0].get_text().split()[-1] == 'U.S.':
            state = data[0].get_text().split()[-2]
            state = state.replace(',','')
        if data[0].get_text().split()[-3].replace(',','') == 'Carolina':
            state = 'Carolina'


    info.append(birth_date)
    info.append(state)
    info.append(president_name.strip(' '))
    insert_new_data(info)


def insert_new_data(info):
    if len(info) == 4:
        conn = create_connection()
        cursor = conn.cursor()
        query = ('Update Presidents set President_Birth=%s, President_Death=%s, State=%s where President_Name = %s;')
        cursor.execute(query, [item for item in info] )
        conn.commit()
        cursor.close()
        conn.close()
    elif len(info) == 3:
        conn = create_connection()
        cursor = conn.cursor()
        query = (
        'Update Presidents set President_Birth=%s, State=%s where President_Name = %s;')
        cursor.execute(query, [item for item in info])
        conn.commit()
        cursor.close()
        conn.close()


def create_connection():
    cnx2 = mysql.connector.connect(host='localhost',
                                   user='root', password='MyNewPass',
                                   database='Web_Data')
    return cnx2

def question_1():
    print('QUESTION 1')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('Select President_Name, DATE(Presidency_End) from Presidents where Status = "Died";')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The number of presidents that died in office is: ', len(result), '. They are \n')
    [print(item[0], ' : ', item[1].strftime('%B %d %Y')) for item in result]
    print('')
    print('#####################################################################')


def question_2():
    print('QUESTION 2')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('Select President_Name, Presidency_End from Presidents where Status = "Resigned";')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The number of presidents that resigned in office is: ', len(result), '. They are \n')
    for item in result:
        print(item[0], ' : ', item[1].strftime('%B %d %Y'))
    print('#####################################################################')


def question_3():
    print('QUESTION 3')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('Select President_Name as Presidents_Who_Were_Vice_Presidents from Presidents where President_Name IN (select Vice_President_Name from Vice_President);')

    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    for items in result:
        conn = create_connection()
        cursor = conn.cursor()
        query = ('Select President_Name as President_To from Vice_President where Vice_President_Name = %s;')
        cursor.execute(query, items)
        result = cursor.fetchone()
        print(items[0] ,' was a president and also vice president to: ', result[0])
        print(' ')
        cursor.close()
        conn.close()
    print('#####################################################################')


def question_4():
    print('QUESTION 4')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select (sum(TIMESTAMPDIFF(month,Vacant_Start,Vacant_End))-mod(sum(TIMESTAMPDIFF(month,Vacant_Start,Vacant_End)),12))/12 as years, mod(sum(TIMESTAMPDIFF(month,Vacant_Start,Vacant_End)),12) as months  from Vacant;')
    cursor.execute(query, )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print('The Vice President Office has been vacant for: ', result[0], ' years and: ', result[1], ' Months')
    print('#####################################################################')


def question_5():
    print('QUESTION 5')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('Select President_Name,President_Age,Presidency_Start from Presidents where President_Age = (Select min(President_Age) from Presidents);')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The youngest serving President was : \n')
    for items in result:
        print('Name:',  items[0], ' Age: ', items[1], ' Start of Presidency', items[2])
    print('#####################################################################')

def question_6():
    print('QUESTION 6')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select President_Name, President_Age from Presidents where DATEDIFF(Presidency_End,President_Birth) = (Select max(DATEDIFF(Presidency_End,President_Birth )) from Presidents);')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The oldest serving President was : \n')
    for items in result:
        print('Name: ', items[0], ' Age: ', items[1])
    print('#####################################################################')


def question_7():
    print('QUESTION 7')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select President_Name, max(DATEDIFF(Presidency_End, Presidency_Start)) as Length_Of_Term from Presidents where DATEDIFF(Presidency_Start, Presidency_End) = (select max(DATEDIFF(Presidency_Start, Presidency_End)) from Presidents) Group by President_Name;')
    cursor.execute(query, )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print('The Shortest Presidential Term in days was : ', result[0], ' served by: ', result[1])
    print(result)
    print('#####################################################################')


def question_8():
    print('QUESTION 8')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select Party, count(President_Name) as temp from Presidents group by Party Having temp = count(President_Name);')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    for items in result:
        print(round(items[1]/45*100, 2), '% of the presidents were ', items[0])
    print('#####################################################################')


def question_9():
    print('QUESTION 9')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select President_Name, State from Presidents;')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The Presidents by State : \n')
    for items in result:
        print('Name: ', items[0], ' State: ', items[1]  )
    print('#####################################################################')

def question_11():
    print('QUESTION 11')
    print(' ')
    conn = create_connection()
    cursor = conn.cursor()
    query = ('select State,count(State) as num_occurrences from Presidents group by State Having num_occurrences = 1;')
    cursor.execute(query, )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    print('The States that only produced one President are : \n')
    print(result)
    print('#####################################################################')



#result = get_html()
#data = remove_tags(result)
#parse_html(data)
states = get_states()

#get_extra_data()
question_1()
question_2()
question_3()
question_4()
question_5()
question_6()
question_7()
question_8()
question_9()




#  create table Presidents (Presidency_Start Date, Presidency_End Date, Status varchar(50), President_Name varchar(50), Year_of_Birth int(11), President_Age int(11), Party varchar(50),President_Birth Date, President_Death Date, State varchar(50));
#  create table Vice_President (Vice_President_Name varchar(50), Vice_President_Start Date, Vice_President_End Date, President_Name varchar(50));
#  create table Vacant (Vacant varchar(50), Vacant_Start Date, Vacant_End Date, President_Name varchar(50));