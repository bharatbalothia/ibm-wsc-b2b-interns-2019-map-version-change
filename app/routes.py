from app import app
from flask import render_template, redirect, request, url_for, send_file, session
from werkzeug.utils import secure_filename
from datetime import timedelta
import cProfile, pstats, io
from authenticate import authenticate
from versionChanger import change


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


@app.route('/version_change')
def version_change():
    session['newversion'] = [{'version': '00201'}, {'version': '00204'}, {'version': '002001'},
                             {'version': '002001FORD'}, {'version': '002002'}, {'version': '002002CHRY'},
                             {'version': '002002FORD'}, {'version': '002002VICS'}, {'version': '002003'},
                             {'version': '002003FORD'}, {'version': '002003GM'}, {'version': '002003VICS'},
                             {'version': '002040'}, {'version': '002040CHRY'}, {'version': '002040GM'},
                             {'version': '002040NAV'}, {'version': '002040VICS'}, {'version': '00300'},
                             {'version': '00301'}, {'version': '00302'}, {'version': '00303'}, {'version': '00304'},
                             {'version': '00305'}, {'version': '00306'}, {'version': '00307'}, {'version': '003010'},
                             {'version': '003010CHRY'}, {'version': '003010FORD'}, {'version': '003010GM'},
                             {'version': '003010UCS'}, {'version': '003010VICS'}, {'version': '003011'},
                             {'version': '003012'}, {'version': '003020'}, {'version': '003020AIAG'},
                             {'version': '003020M'}, {'version': '003020RAIL'}, {'version': '003020UCS'},
                             {'version': '003020VICS'}, {'version': '003021'}, {'version': '003022'},
                             {'version': '003030'}, {'version': '003030CHRY'}, {'version': '003030GM'},
                             {'version': '003030RAIL'}, {'version': '003030UCS'}, {'version': '003030VICS'},
                             {'version': '003031'}, {'version': '003032'}, {'version': '003032FORD'},
                             {'version': '003040'}, {'version': '003040AIAG'}, {'version': '003040NAV'},
                             {'version': '003040RAIL'}, {'version': '003040RIGMAT'}, {'version': '003040UCS'},
                             {'version': '003040VICS'}, {'version': '003041'}, {'version': '003042'},
                             {'version': '003042CBC'}, {'version': '003050'}, {'version': '003050AIAG'},
                             {'version': '003050RAIL'}, {'version': '003050RIFMAT'}, {'version': '003050UCS'},
                             {'version': '003050VICS'}, {'version': '003051'}, {'version': '003052'},
                             {'version': '003060'}, {'version': '003060AIAG'}, {'version': '003060BISAC'},
                             {'version': '003060RAIL'}, {'version': '003060RIFMAT'}, {'version': '003060UCS'},
                             {'version': '003060VICS'}, {'version': '003061'}, {'version': '003062'},
                             {'version': '003070'}, {'version': '003070RAIL'}, {'version': '003070UCS'},
                             {'version': '003070VICS'}, {'version': '003071'}, {'version': '003072'},
                             {'version': '00400'}, {'version': '00401'}, {'version': '00402'}, {'version': '00403'},
                             {'version': '00404'}, {'version': '00405'}, {'version': '00406'}, {'version': '004010'},
                             {'version': '004010AIAG'}, {'version': '004010RAIL'}, {'version': '004010RIFMAT'},
                             {'version': '004010TI0900'}, {'version': '004010UCS'}, {'version': '004010VICS'},
                             {'version': '004011'}, {'version': '004012'}, {'version': '004020'},
                             {'version': '004020RAIL'}, {'version': '004020UCS'}, {'version': '004020VICS'},
                             {'version': '004021'}, {'version': '004022'}, {'version': '004030'},
                             {'version': '004030RAIL'}, {'version': '004030RIFMAT'}, {'version': '004030UCS'},
                             {'version': '004030VICS'}, {'version': '004031'}, {'version': '004032'},
                             {'version': '004035RAIL'}, {'version': '004040'}, {'version': '004040RAIL'},
                             {'version': '004040UCS'}, {'version': '004040VICS'}, {'version': '004041'},
                             {'version': '004042'}, {'version': '004050'}, {'version': '004050RAIL'},
                             {'version': '004050UCS'}, {'version': '004050VICS'}, {'version': '004051'},
                             {'version': '004052'}, {'version': '004060'}, {'version': '004060RAIL'},
                             {'version': '004060RIFMAT'}, {'version': '004060UCS'}, {'version': '004060VICS'},
                             {'version': '004061'}, {'version': '004062'}, {'version': '00500'}, {'version': '00501'},
                             {'version': '00502'}, {'version': '00503'}, {'version': '00504'}, {'version': '00505'},
                             {'version': '005010'}, {'version': '005010RAIL'}, {'version': '005010UCS'},
                             {'version': '005010VICS'}, {'version': '005011'}, {'version': '005012'},
                             {'version': '005020'}, {'version': '005020RAIL'}, {'version': '005020UCS'},
                             {'version': '005020VICS'}, {'version': '005021'}, {'version': '005022'},
                             {'version': '005030'}, {'version': '005030RAIL'}, {'version': '005030UCS'},
                             {'version': '005030VICS'}, {'version': '005031'}, {'version': '005032'},
                             {'version': '005040'}, {'version': '005040RAIL'}, {'version': '005040UCS'},
                             {'version': '005040VICS'}, {'version': '005041'}, {'version': '005042'},
                             {'version': '005050'}, {'version': '005050RAIL'}, {'version': '005051'},
                             {'version': '005052'}, {'version': '00600'}, {'version': '00601'}, {'version': '00602'},
                             {'version': '006010'}, {'version': '006010RAIL'}, {'version': '006011'},
                             {'version': '006012'}, {'version': '006020'}, {'version': '006020RAIL'},
                             {'version': '006021'}, {'version': '006022'}]
    return render_template('index.html', title='Home', user=session['username'], newversion=session['newversion'])


@app.route('/uploader_basemap', methods=['GET', 'POST'])
def upload_basemap_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save("C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\MapVersionChanger\\basemap\\" + secure_filename(f.filename))
        Targetversion = request.form.get('select_version')
        basefile = "C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\MapVersionChanger\\basemap\\" + f.filename

        map_name_get = request.form.get('Map')
        finalMapName = map_name_get + ".mxl"
        finalmap = "C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\MapVersionChanger\\Generatedmap\\" + finalMapName


        name_list = finalMapName.split("_")
        template_file_name = name_list[-3] + "_" + name_list[-2] + "_" + name_list[-1]
        template_file = "C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\MapVersionChanger\\std_version_templates\\" + \
                        template_file_name
        change(template_file,basefile,Targetversion,finalmap,map_name_get)
        return send_file(finalmap, as_attachment=True)


@app.route('/report_file/')
def group_file_tut():
    # print(1)
    mymap = session['report_file']
    try:
        return send_file(mymap, attachment_filename='demo.docx')
    except Exception as e:
        return str(e)


@app.route('/logout', methods=['GET'])
def logout():
    for key in list(session):
        session.pop(key, None)
    return redirect(url_for('index'))
