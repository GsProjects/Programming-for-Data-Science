import csv
from collections import Counter

food = list(csv.DictReader(open('Food_Inspections.csv')))
column = input('Enter the column you want to process or enter nothing to escape: ')
if column != '':
    temporary_data = {row[column] for row in food}
    print(temporary_data)
    print(len(temporary_data))


def fill_cells(data):  # replace empty cells with null value
    print('In change_date_format')
    result = ammend_inspections(data)
    for x in result:
        for value in x.keys():
            if x[value] == '':
                x[value] = 'NULL'
    print('Returning 6')
    return result

def ammend_inspections(data):# clean inspection type data
    print('In ammend_inspections')
    result = remove_duplicate_locations(data)
    for items in result:
        items['Inspection Type'] = items['Inspection Type'].replace('canvas', 'canvass')
        items['Inspection Type'] = items['Inspection Type'].replace('out ofbusiness', 'out of business')
    return result
                                                                             

def remove_duplicate_locations(data):  # populate empty locations, then remove longitude and latitude columns
    print('In remove_duplicate_locations')
    result = clean_text_data(data)
    temp_data = []
    location = set()
    #  If location col empty populate with longitude and latitude
    for x in result:
        if x['Location'] == '':
            location.add(x['Latitude'])
            location.add(x['Longitude'])
            x['Location'] = location
            temp_data.append(x)
        else:
            temp_data.append(x)

    #  Remove longitude and latitude columns
    new_data = []
    for item in temp_data:
        item.pop('Latitude')
        item.pop('Longitude')
        new_data.append(item)
    print('Returning 5')
    return new_data


def clean_text_data(data):  # remove punctuation and whitespace to prevent duplicates
    print('In clean_text_data')
    result = ammend_city(data)
    text_based_columns = ['DBA Name', 'AKA Name', 'Inspection Type']
    for x in result:
        for value in x:
            x[value] = x[value].lower()
            for item in text_based_columns:
                x[item] = x[item].lower()
                x[item] = x[item].replace("'", "")
                x[item] = x[item].replace(".", "")
                x[item] = x[item].replace(",", "")
                x[item] = x[item].replace("-", " ")
                x[item] = x[item].replace("/", " ")
                x[item] = x[item].lstrip(" ")
                x[item] = x[item].rstrip(" ")
    print('Returning 4')
    return result


def ammend_city(data):  # if city value does not contain chicago substring remove the row, then remove the column
    print('In ammend_city')
    result = remove_state(data)
    new_data = []
    city = 'chicago'
    for x in result:
        if city in x['City'].lower() or x['City'].lower() == '':
            new_data.append(x)
        elif x['City'].lower() == 'chcicago':
            x['City'] = city
        else:
            x['City'] = 'non-chicago address, attention required'
    return new_data


def remove_state(data):
    print('In remove_state')
    result = change_date_format(data)
    
    for x in result:
        x.pop('State')
    print('Returning 2')
    return result


def change_date_format(data):  # changes date from mm/dd/yy to dd/mm/yy
    print('In change_date_format')
    result = fill_names(data)
    for x in result:
        if x['Inspection Date'] != '':
            x['Inspection Date'] = x['Inspection Date'].replace('-', '/')
            temporary_date = x['Inspection Date'].split('/')
            new_date = temporary_date[1] + '/' + temporary_date[0] + '/' + temporary_date[2]
            x['Inspection Date'] = new_date
    print('Returning 1')
    return result


def fill_names(data):  # populate empty name cells if possible
    print('In change_date_format')
    result = change_case(data)
    for x in result:
        if x['DBA Name'] == '':
            x['DBA Name'] = x['AKA Name']
        elif x['AKA Name'] == '':
            x['AKA Name'] = x['DBA Name']
    return data


def change_case(data):
    for item in data:
        for value in item:
            item[value] = item[value].lower()
    return data        
    

def write_data(data):
    with open('TemporaryOutput.csv', "w") as fh:
        out_csv = csv.DictWriter(fh, list(data[0].keys()))
        out_csv.writeheader()
        out_csv.writerows(data)


result = fill_cells(food)

#temporary = Counter(row[column] for row in result)

temporary = {row[column] for row in result}
print(temporary)
print(len(temporary))
'''
#print(Counter(temporary))
#with open('Temp_Result.txt', 'w') as file:
#    file.write(str(Counter(temporary)))

#print(temporary.most_common(50))
a = temporary.most_common(10)
for item in a:
    print(len(item[0]))'''
write_data(result)
