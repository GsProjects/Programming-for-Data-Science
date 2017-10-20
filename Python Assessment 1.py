import csv

food = list(csv.DictReader(open('Food_Inspections.csv')))
column = input('Enter the column you want to process or enter nothing to escape: ')
if column != '':
    temporary_data = {row[column] for row in food}
    print(temporary_data)
    print(len(temporary_data))


def clean_text_data(data):
    print('In clean_text_data')
    result = ammend_city(data)
    new_data = []
    text_based_columns = ['DBA Name','City','AKA Name','State','Inspection Type']
    for x in result:
        for value in x:
            x[value] = x[value].lower()
            for item in text_based_columns:
                x[item] = x[item].lower()
                x[item] = x[item].replace("'", "")
                x[item] = x[item].replace(".", "")
                x[item] = x[item].replace(",", "")
                x[item] = x[item].replace("-", "")
        if x['AKA Name'] == '':
            x['AKA Name'] = x['DBA Name']
        new_data.append(x)
    return new_data


def ammend_city(data):
    print('In ammend_city')
    result = add_state(data)
    new_data = []
    city = 'chicago'
    for x in result:
        if city in x['City'].lower():
            x['City'] = city
        new_data.append(x)
    return new_data


def add_state(data):
    print('In add_state')
    new_data = []
    for x in data:
        if x['State'] == '':
            x['State'] = 'IL'

        new_data.append(x)
    return new_data


def write_data(data):

    with open('TemporaryOutput.csv', "w") as fh:
        out_csv = csv.DictWriter(fh, list(data[0].keys()))
        out_csv.writeheader()
        out_csv.writerows(data)


result = clean_text_data(food)
write_data(result)
