# app/utils.py
def contains_angular(text: str) -> bool:
    start = text.find('<')
    end = text.find('>')
    return start != -1 and end != -1 and abs(start - end) > 0

def evaluate_angular(index, text, dataframe):
    evaluation_dict = {
        '<NAME>': 'Name',
        '<YEAR>': 'Year',
        '<DOMAIN>': 'Domain',
        '<TIME>': 'Time'
    }

    if contains_angular(text):
        row = dataframe.iloc[index]
        for template, column in evaluation_dict.items():
            if template in text:
                text = text.replace(template, str(row[column]))
    return text
