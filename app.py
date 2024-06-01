from flask import Flask, jsonify,render_template,request,redirect, url_for
from bs4 import BeautifulSoup
import requests
import csv
import json
from flask import Flask, send_file
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/render', methods=['POST'])
def render():
    url = request.form.get('url')
    print(url)
    return render_template('render.html', url=url)
@app.route('/scrape', methods=['POST'])
def scrape():
    user_input = request.form.get('user_input')
    print(user_input)
    url = request.form.get('url')
    print(url)
    tag_classes = user_input.split(',')
    print(tag_classes)
    response = requests.get(url)
    response.raise_for_status()  
    soup = BeautifulSoup(response.text, 'html.parser')
    scrape_elements = {tag_class: soup.select(f'{tag_class}') for tag_class in tag_classes}
    num = min(len(elements) for elements in scrape_elements.values())
    scraped_content_list = []
    for i in range(num):
        data = {}
        for tag_class in tag_classes:
            element = scrape_elements[tag_class][i]
            data[tag_class] = element.get_text(strip=True)
        scraped_content_list.append(data)

    return render_template('scrape.html', scraped_data=scraped_content_list, user_input=user_input)

def decode_unicode_values(tags_list):
    for item in tags_list:
        for key in item:
            item[key] = item[key].encode('utf-8').decode('unicode_escape')
    return tags_list

@app.route('/scrape_CSV', methods=['POST'])
def scrape_data_CSV():
    value = request.form.get('action')
    user_input = request.form.get('user_input')
    user_input_list = user_input.split(',')

    # Debug prints to check received form data
    print("Action:", value)
    print("User Input:", user_input)
    scraped_content_list = request.form.get('scraped_content_list')
    print("Scraped Content List:", scraped_content_list)
    
    try:
        tags_list = json.loads(scraped_content_list)
    except json.JSONDecodeError as e:
        return f"JSON decoding error: {str(e)}", 400

    # Decode Unicode values
    tags_list = decode_unicode_values(tags_list)

    if value == 'csv':
        filename = 'download.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=user_input_list)
            w.writeheader()
            for element in tags_list:
                w.writerow(element)
        return send_file(filename, as_attachment=True, attachment_filename=filename, mimetype='text/csv')
    
    elif value == 'json':
        filename = 'download.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tags_list, f, indent=4, ensure_ascii=False)
        return send_file(filename, as_attachment=True, attachment_filename=filename, mimetype='application/json')

    
    elif value == 'excel':
        filename = 'download.xlsx'
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        header = list(tags_list[0].keys())
        worksheet.append(header)
        for item in tags_list:
            row = [item[field] for field in header]
            worksheet.append(row)
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, attachment_filename=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


    
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True,host='0.0.0.0',port=5000)
