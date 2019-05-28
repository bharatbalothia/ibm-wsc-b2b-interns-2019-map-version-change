from app import app
from flask import render_template, redirect, request, url_for, send_file, session, jsonify
from werkzeug.utils import secure_filename
from datetime import timedelta
import cProfile, pstats, io
from authenticate import authenticate
from versionChanger import change
import os
import couchdb

couchserver = couchdb.Server("http://%s:%s@9.199.145.193:5984/" % ("admin", "admin123"))
segment_db = couchserver["segmentusagedefs"]
baseFolder = "C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\"


def profile(fnc):
    """A decorator that uses cProfile to profile a function"""

    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        # print(s.getvalue())
        return retval

    return inner


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)


@app.route('/')
@app.route('/index')
def index():
    if 'logged_in' in session and 'username' in session and session['logged_in'] == True:
        return redirect(url_for('version_change'))

    if ('authorized' in session):
        temp = session['authorized']
        session.pop('authorized', None)
        return render_template('login.html', title='Home', authorized=temp)
    else:
        return render_template('login.html', title='Home', authorized=1)


@app.route('/authentication', methods=['POST'])
def ldapAuth():
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])

    isLoged = authenticate(POST_USERNAME, POST_PASSWORD)
    if not isLoged[0]:
        session['authorized'] = 0
        error = 'Invalid login'
        return render_template('login.html', error=error)
    else:
        session['logged_in'] = True
        session['username'] = isLoged[1]

        # flash('You are now logged in', 'success')
        return redirect(url_for('version_change'))


@app.route('/get_versions',methods=['POST'])
def get_versions():
    print("called")
    trans = request.form.get('transaction')
    print(trans)
    versions = {data.value for data in segment_db.view('_design/version-seg/_view/version-seg', key=trans)}
    versions = sorted(versions)
    html_string_selected = ''
    for entry in versions:
        html_string_selected += '<option value="{}">{}</option>'.format(entry, entry)
    return jsonify(html_string_selected=html_string_selected)


@app.route('/version_change')
def version_change():
    if  'Transactions' not in session:
        session['Transactions'] = [data.key for data in segment_db.view('_design/all-transactions/_view/all-transactions',group=True)]
        transactions = session['Transactions']
    else:
        transactions = session['Transactions']
    return render_template('index.html', title='Home', user=session['username'], transactions=transactions)


@app.route('/uploader_basemap', methods=['GET', 'POST'])
def upload_basemap_file():
    if request.method == 'POST':
        f = request.files['file']
        transaction = request.form.get('select_transaction')
        f.save(baseFolder+ "MapVersionChanger\\basemap\\" + secure_filename(f.filename))
        Targetversion = request.form.get('select_version')
        print(f.filename)
        map_name_get = request.form.get('Map')
        if f.filename.split(".")[0].split("_")[-1] in Targetversion or f.filename == map_name_get:
            error = "Both Target and Base versions are same. No Conversion required."
            return render_template('index.html', title='Home', user=session['username'],
                                   transactions=session['Transactions'], error=error)

        try:
            variable = int(Targetversion)
        except ValueError:
            variable = Targetversion
        basefile = baseFolder+ "MapVersionChanger\\basemap\\" + f.filename


        finalMapName = map_name_get + ".mxl"
        finalmap = baseFolder+ "MapVersionChanger\\Generatedmap\\" + finalMapName
        template_file_names = ["I" + "_" + transaction + "_" + str(variable)+".mxl","O" + "_" + transaction + "_" + str(variable)+".mxl"]
        template_file = ""
        for files in template_file_names:
            print(files)
            some_path = baseFolder+ "MapVersionChanger\\std_version_templates\\" + files
            if os.path.exists(some_path):
                print(some_path)
                template_file = some_path
                break
        else:
            error = "Error Occured !! Either the Template file is not available or You have given the Template map name wrong"
            return render_template('index.html', title='Home', user=session['username'], transactions=session['Transactions'],error=error)
        sessdict = change(template_file,basefile,Targetversion,finalmap,map_name_get)
        #return render_template('index.html', title='Home', user=session['username'],transactions=session['Transactions'], sess=sessdict)
        return send_file(finalmap, as_attachment=True)


@app.route('/report_file')
def group_file_tut():
    files = os.listdir(baseFolder+ "MapVersionChanger\\std_version_templates")
    return render_template('templatelist.html',files = files,title='Home', user=session['username'])

@app.route('/templateUploader',methods=['POST'])
def templateUploader():
    if request.method == 'POST':
        f = request.files['file']
        print("called")
        f.save(baseFolder+ "MapVersionChanger\\std_version_templates\\" + secure_filename(f.filename))
        return redirect(url_for('group_file_tut'))

@app.route('/downloadTemplate/<string:id>', methods=['GET', 'POST'])
def download_temp(id):
    files = baseFolder+ "MapVersionChanger\\std_version_templates\\"+id
    return send_file(files,as_attachment=True)

@app.route('/deleteTemplate/<string:id>', methods=['GET', 'POST'])
def delete_temp(id):
    files = baseFolder+ "MapVersionChanger\\std_version_templates\\"+id
    os.remove(files)
    return redirect(url_for('group_file_tut'))

@app.route('/logout', methods=['GET'])
def logout():
    for key in list(session):
        session.pop(key, None)
    return redirect(url_for('index'))
