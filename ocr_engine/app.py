from flask import Flask, json, request, jsonify
from werkzeug.utils import secure_filename
import urllib.request
import os, fitz, re

from flask import Flask, jsonify, request, session
 
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import collections
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['txt', 'pdf'])
# Database Docker
DB_HOST = "postgres"
DB_NAME = "postgresdb"
DB_USER = "postgres"
DB_PASS = "password"

#Database Localhost
# DB_HOST = "localhost"
# DB_NAME = "database1"
# DB_USER = "postgres"
# DB_PASS = "hudahuda"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# CORS(app) 

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST,
                            dbname=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS)
    return conn
 
@app.route('/')
def main():
    return 'Homepage'

@app.route('/getdatacv', methods=['GET'])
def getDataCv():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT  * FROM cv')
    # r = [dict((cur.description[i][0], value) \
    #            for i, value in enumerate(row)) for row in cur.fetchall()]
    # n = json.dumps((r[0] if r else None) if one else r)

    rows = cur.fetchall()
    print(rows)
    res = []
    content = {}
    for r in rows:
        content = {
            'firstname': r[0],
            'lastname' : r[1],
            'employeenumber' : r[2],
            'totalworkingyears' : r[3],
            'education': r[4]
        }
        res.append(content)
        content = {}
    conn.commit()
    cur.close()
    conn.close()
    print(jsonify(res))
    return jsonify(res)

@app.route('/getdatask', methods=['GET'])
def getDataSk():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT  * FROM sk')
    # r = [dict((cur.description[i][0], value) \
    #            for i, value in enumerate(row)) for row in cur.fetchall()]
    # n = json.dumps((r[0] if r else None) if one else r)

    rows = cur.fetchall()
    print(rows)
    res = []
    content = {}
    for r in rows:
        content = {
            'firstname': r[0],
            'lastname' : r[1],
            'employeenumber': r[2],
            'dateofbirth' : r[3],
            'monthlyincome': r[4],
            'jobtitle' : r[5]
            
        }
        res.append(content)
        content = {}
    conn.commit()
    cur.close()
    conn.close()
    print(jsonify(res))
    return jsonify(res)

@app.route('/uploadsk', methods=['POST'])
def upload_fileSK():
    # check if the post request has the file part
    if 'files' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
 
    files = request.files.getlist('files')
     
    errors = {}
    success = False
     
    for file in files:      
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            success = True
        else:
            errors[file.filename] = 'File type is not allowed'
 
    if success:
        pdf = 'static/files/' + filename
        doc = fitz.open(pdf)
        generated_file = open("temp/SK.txt", "wb")
        for page in doc:
            text = page.get_text()
            text = text.strip()
            text = text.encode("utf-8")
            generated_file.write(text)

            # print(text)
        generated_file.close()

        with open('temp/SK.txt', 'r') as f:
            for line in f:
                if 'Nama' in line:
                    while True:
                        line = next(f)
                        if ':' in line:
                            nama = line.split(':')[1].strip()
                            first_name = nama.split()[0]
                            last_name = nama.split()[1]
                            break

                if 'Tempat/tgl lahir' in line:
                    while True:
                        line = next(f)
                        if ':' in line:
                            tgl_lahir = line.split(':')[1].strip()
                            tgl_lahir = line.split('/')[1].strip()
                            break

                if 'gaji' in line:
                    line = line.split()
                    for gaji in line:
                        if re.match(r'^(\$).+(-)$', gaji):
                            gaji = re.sub(r'[^\w\s]', '', gaji).replace('Rp', '')
                            break

                if 'Posisi' in line or 'Jabatan' in line:
                    while True:
                        line = next(f)
                        if ':' in line:
                            posisi = [posisi.strip() for posisi in line.split(':')][1]
                            break
                        #   posisi = line.split(':')[1].strip()
        
        print(first_name, last_name, tgl_lahir, gaji, posisi)

        # check the firstname and lastname is store as a employee in database
        conn = get_db_connection()
        cur = conn.cursor()
        query1 = '''SELECT DISTINCT * FROM activity WHERE firstname = '{first_name}' AND lastname = '{last_name}' '''.format(first_name=first_name, last_name=last_name)
        cur.execute(query1)
        result1 = cur.fetchone()
        print(result1)
        # return jsonify(result1)
        if result1:
            employeenumber = result1[2]
            query = '''SELECT COUNT(*) FROM sk WHERE firstname = '{first_name}' AND lastname = '{last_name}' '''.format(first_name=first_name, last_name=last_name)
            cur.execute(query)
            result = cur.fetchone()

            if result[0] == 0:
                cur.execute('INSERT INTO sk VALUES (%s,%s,%s,%s,%s,%s)', (first_name, last_name,employeenumber, tgl_lahir, gaji, posisi))
                conn.commit()
                cur.close()
                conn.close()
                resp = jsonify({
                    'message' : 'File successfully uploaded & inserted',
                    'data' : {
                        'firstname' : first_name,  
                        'lastname' : last_name, 
                        'employeenumber' :employeenumber,
                        'dateofbirth' : tgl_lahir, 
                        'monthlyincome' : gaji, 
                        'jobtitle' : posisi
                } })
                resp.status_code = 201
                return resp
            elif result[0] >= 1:
                cur.execute('UPDATE sk SET monthlyincome = %s, jobtitle = %s, dateofbirth = %s WHERE firstname = %s AND lastname = %s', (gaji, posisi, tgl_lahir, first_name, last_name))
                conn.commit()
                cur.close()
                conn.close()
                resp = jsonify({
                    'message' : 'File successfully uploaded & updated',
                    'data' : {
                        'firstname' : first_name,  
                        'lastname' : last_name, 
                        'employeenumber' :employeenumber,
                        'dateofbirth' : tgl_lahir, 
                        'monthlyincome' : gaji, 
                        'jobtitle' : posisi
                } })
                resp.status_code = 201
                return resp
        else :
            return jsonify({
                'message' : 'File cannot be found in database',
            })
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

@app.route('/uploadcv', methods=['POST'])
def upload_fileCV():
    first_name, last_name = '', ''
    count = 0
    lulus = True
    degree = ['High', 'Bachelor', 'Master', 'Doctor']
    # check if the post request has the file part
    if 'files' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
 
    files = request.files.getlist('files')
     
    errors = {}
    success = False
     
    for file in files:      
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            success = True
        else:
            errors[file.filename] = 'File type is not allowed'
 
    if success:
        pdf = 'static/files/' + filename
        doc = fitz.open(pdf)
        generated_file = open("temp/CV.txt", "wb")
        for page in doc:
            text = page.get_text()
            text = text.strip()
            text = text.encode("utf-8")
            generated_file.write(text)

            # print(text)
        generated_file.close()

        with open('temp/CV.txt', 'r', encoding="utf8") as f:
            for line in f:
                if first_name == '' and last_name == '':
                    # if re.match(r'^[a-zA-Z].+[a-zA-Z]$', line):
                    first_name = line.split()[0]
                    last_name = line.split()[1]
                    continue

                if 'EXPERIENCE' in line:
                    while True:
                        line = next(f)
                        if len(line.split()) == 0:
                            continue
                        if 'EDUCATION' in line:
                            experience = akhir-awal
                            break
                        line = line.split('●')[0].strip()
                        if re.search(r'^[a-zA-Z].+(\(.+\))$', line):
                            if count == 0:
                                result = re.search(r'^[a-zA-Z].+(\(.+\))$', line)
                                result = result.group(1)
                                akhir = int(result.split()[-1].replace(')', ''))
                                count += 1
                            else:
                                result = re.search(r'^[a-zA-Z].+(\(.+\))$', line)
                                result = result.group(1)
                                awal = int(result.split()[1])
            
                if 'EDUCATION' in line:
                    while True:
                        line = next(f)
                        if len(line.split()) == 0:
                            continue

                        if line.split()[-1] == 'now)':
                            lulus = False
                            education = 2
                            continue

                        if line.split()[0] in degree:
                            if line.split()[0] == 'Bachelor' and lulus == False:
                                education = 2
                                break
                            if line.split()[0] == 'High':
                                education = 1
                            elif line.split()[0] == 'Bachelor':
                                education = 3
                            elif line.split()[0] == 'Master':
                                education = 4
                            elif line.split()[0] == 'Doctor':
                                education = 5
                            break
        
        print(first_name, last_name, experience, education)

        # check the firstname and lastname is store as a employee in database
        conn = get_db_connection()
        cur = conn.cursor()
        query1 = '''SELECT DISTINCT * FROM activity WHERE firstname = '{first_name}' AND lastname = '{last_name}' '''.format(first_name=first_name, last_name=last_name)
        cur.execute(query1)
        result1 = cur.fetchone()
        print(result1[2])

        if result1:
            employeenumber = result1[2]
            query = '''SELECT COUNT (*) FROM cv WHERE firstname = '{firstname}' AND lastname = '{lastname}' '''.format(firstname=first_name, lastname=last_name)
            cur.execute(query)
            result = cur.fetchone()
            if result[0] == 0:
                cur.execute('INSERT INTO cv VALUES (%s,%s,%s,%s,%s)', (first_name, last_name,employeenumber, experience, education))
                conn.commit()
                cur.close()
                conn.close()
                resp = jsonify({
                    'message' : 'File successfully uploaded & inserted',
                    'data' : {
                        'firstname' : first_name,  
                        'lastname' : last_name, 
                        'employeenumber' : employeenumber,
                        'totalworkingyears' : experience, 
                        'education' : education
                } })
                resp.status_code = 201
                return resp
            elif result[0] >= 1:
                cur.execute('UPDATE cv SET totalworkingyears = %s, education = %s WHERE firstname = %s AND lastname = %s', (experience, education, first_name, last_name))
                conn.commit()
                cur.close()
                conn.close()
                resp = jsonify({
                    'message' : 'File successfully uploaded & updated',
                    'data' : {
                        'firstname' : first_name,  
                        'lastname' : last_name, 
                        'employeenumber' : employeenumber,
                        'totalworkingyears' : experience, 
                        'education' : education
                } })
                resp.status_code = 201
                return resp 
        else :
            return jsonify({
                'message' : 'File cannot be found in database',
            })
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

if __name__ == '__main__':
    app.run(debug=True)