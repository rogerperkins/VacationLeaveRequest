from flask import Flask, request, render_template, jsonify
from flask.json import JSONEncoder
import logging
import pyodbc
from datetime import date, datetime
from decimal import Decimal

app = Flask(__name__)

logFormatStr = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
logging.basicConfig(format=logFormatStr, filename="global.log", level=logging.DEBUG)
formatter = logging.Formatter(logFormatStr, '%m-%d %H:%M:%S')
fileHandler = logging.FileHandler("summary.log")
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
app.logger.addHandler(fileHandler)
app.logger.addHandler(streamHandler)
app.logger.info("Logging is set up.")


class JsonEncoder(JSONEncoder):
    """JSON serializer for objects not serializable by default json code"""
    def default(self, obj):
        if obj is None:
            return ''
        if isinstance(obj, (datetime, date)):
            return obj.strftime("%m/%d/%Y %#I:%M %p")  # obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return JSONEncoder.default(self, obj)


@app.route('/')
def index():
    return jsonify({'hello': 'world'})


@app.route('/main')
def main():
    return render_template('request.htm')


@app.route('/request')
def req():
    return render_template('request.htm')


@app.route('/history')
def history():
    return render_template('history.htm')


@app.route('/pending')
def pending():
    return render_template('pending.htm')


@app.route('/approval')
def approval():
    return render_template('approval.htm')


@app.route('/org')
def org():
    return render_template('org.htm')


@app.route('/unassigned')
def unassigned():
    return render_template('unassigned.htm')


# post methods

@app.route('/getuser', methods=['POST'])
def getuser():
    username = request.environ.get('REMOTE_USER')
    return username


@app.route('/submitrequest', methods=['POST'])
def submitrequest():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')
    fromdate = request.form.get('fromDate')
    fromtime = request.form.get('fromTime')
    todate = request.form.get('toDate')
    totime = request.form.get('toTime')
    hours = request.form.get('hours')
    comments = request.form.get('comments')

    app.logger.info("--- Submit Request ---")
    app.logger.info("userid:   " + userid)
    app.logger.info("fromdate: " + str(fromdate))
    app.logger.info("fromtime: " + str(fromtime))
    app.logger.info("todate:   " + str(todate))
    app.logger.info("totime    " + str(totime))
    app.logger.info("hours:    " + str(hours))
    app.logger.info("comments: " + str(comments))
    app.logger.info("--- Submit Request ---")

    f = datetime.strptime(fromdate + ' ' + fromtime, '%m/%d/%Y %H%M')
    t = datetime.strptime(todate + ' ' + totime, '%m/%d/%Y %H%M')

    sql = """
    INSERT INTO [dbo].[requests]
               ([userid]
               ,[fromdate]
               ,[todate]
               ,[hours]
               ,[comments])
         VALUES ({}, {}, {}, {}, {})""".format(userid, str(f), str(t), str(hours), str(comments))

    # app.logger.info("sql:" + sql)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    INSERT INTO [dbo].[requests]
               ([userid]
               ,[fromdate]
               ,[todate]
               ,[hours]
               ,[comments]
               ,[statusby])
         VALUES (?, ?, ?, ?, ?, ?)""", userid, f, t, hours, str(comments), userid).rowcount

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("count: " + str(count))

    return str(count)


@app.route('/gethistory', methods=['POST'])
def gethistory():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')

    app.logger.info("--- Get History ---")
    app.logger.info("userid:   " + userid)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    SELECT [userid]
          ,[fromdate]
          ,[todate]
          ,[hours]
          ,[comments]
          ,[requestdate]
          ,[status]
          ,[statusby]
          ,[statusdate]
          ,convert(varchar, [requestdate], 121) as requestdatestring
          ,(select top 1 1 from dbo.org where supervisor = ?) as issuper
    FROM [dbo].[requests]
    WHERE userid = ?
    ORDER BY [fromdate] DESC,[todate] DESC,[requestdate] DESC""", userid, userid)

    rows = cursor.fetchall()

    if len(rows):

        q = [dict(zip([key[0] for key in cursor.description], row)) for row in rows]

        cnxn.commit()
        cursor.close()
        cnxn.close()

        app.logger.info("--- Get History ---")

        app.json_encoder = JsonEncoder
        return jsonify({'history': q})

    return "No Requests Submitted" # noqa


@app.route('/getpending', methods=['POST'])
def getpending():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')

    app.logger.info("--- Get Pending ---")
    app.logger.info("userid:   " + userid)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    SELECT [userid]
          ,[fromdate]
          ,[todate]
          ,[hours]
          ,[comments]
          ,[requestdate]
          ,[status]
          ,[statusby]
          ,[statusdate]
          ,convert(varchar, [fromdate], 121) as fromdatestring
          ,convert(varchar, [requestdate], 121) as requestdatestring
    FROM [dbo].[requests] INNER JOIN [dbo].[org] on org.employee = requests.userid
    WHERE org.supervisor = ? and [status] = 'Pending'
    ORDER BY [statusby]""", userid)  # [fromdate] DESC,[todate] DESC,[requestdate] DESC

    rows = cursor.fetchall()

    if len(rows):

        q = [dict(zip([key[0] for key in cursor.description], row)) for row in rows]

        cnxn.commit()
        cursor.close()
        cnxn.close()

        app.logger.info("--- Get Pending ---")

        app.json_encoder = JsonEncoder
        return jsonify({'pending': q})

    return "No Requests Pending" # noqa


@app.route('/getunassigned', methods=['POST'])
def getunassigned():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')

    app.logger.info("--- Get Unassigned ---")
    app.logger.info("userid:   " + userid)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    SELECT [userid]
          ,[fromdate]
          ,[todate]
          ,[hours]
          ,[comments]
          ,[requestdate]
          ,[status]
          ,[statusby]
          ,[statusdate]
    FROM [dbo].[requests]
    WHERE userid NOT IN (SELECT employee FROM [dbo].[org])""")

    rows = cursor.fetchall()

    if len(rows):

        q = [dict(zip([key[0] for key in cursor.description], row)) for row in rows]

        cnxn.commit()
        cursor.close()
        cnxn.close()

        app.logger.info("--- Get Unassigned ---")

        app.json_encoder = JsonEncoder
        return jsonify({'unassigned': q})

    return "No Unassigned Requests" # noqa


@app.route('/assign', methods=['POST'])
def assign():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')
    emp = request.form.get('emp')

    app.logger.info("--- Assign ---")
    app.logger.info("supervisor: " + userid)
    app.logger.info("employee: " + emp)
    app.logger.info("--- Assign ---")

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    INSERT INTO [dbo].[org]
               ([supervisor]
               ,[employee])
         VALUES (?, ?)""", userid, emp).rowcount

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("count: " + str(count))

    return str(count)


@app.route('/getreassign', methods=['POST'])
def getreassign():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')

    app.logger.info("--- Get Reassign ---")
    app.logger.info("userid:   " + userid)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    SELECT [supervisor]
          ,[employee]
    FROM [dbo].[org]
    ORDER BY [supervisor], [employee]""")

    rows = cursor.fetchall()

    if len(rows):

        q = [dict(zip([key[0] for key in cursor.description], row)) for row in rows]

        cnxn.commit()
        cursor.close()
        cnxn.close()

        app.logger.info("--- Get Reassign ---")

        app.json_encoder = JsonEncoder
        return jsonify({'reassign': q})

    return "No Assignment Users Setup" # noqa


@app.route('/reassign', methods=['POST'])
def reassign():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')
    emp = request.form.get('emp')

    app.logger.info("--- Reassign ---")
    app.logger.info("supervisor: " + userid)
    app.logger.info("employee: " + emp)
    app.logger.info("--- Reassign ---")

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    UPDATE [dbo].[org] SET [supervisor] = ?
    WHERE [employee] = ?""", userid, emp).rowcount

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("count: " + str(count))

    return str(count)


@app.route('/updatestatus', methods=['POST'])
def updatestatus():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    status = request.form.get('status')
    supervisor = request.form.get('id')
    emp = request.form.get('emp')
    requestdate = request.form.get('requestdate')

    app.logger.info("--- Update Status ---")
    app.logger.info("status: " + status)
    app.logger.info("supervisor: " + supervisor)
    app.logger.info("employee: " + emp)
    app.logger.info("requestdate: " + requestdate)
    app.logger.info("--- Update Status ---")

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    UPDATE [dbo].[requests] SET [status] = ?, [statusby] = ?, [statusdate] = getdate()
    WHERE [userid] = ? AND [requestdate] = ?""", status, supervisor, emp, requestdate).rowcount

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("count: " + str(count))

    return str(count)


@app.route('/getrequest', methods=['POST'])
def getrequest():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')
    requestdate = request.form.get('requested')

    app.logger.info("--- Get Request ---")
    app.logger.info("userid:   " + userid)
    app.logger.info("requestdate:   " + str(requestdate))

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    SELECT [userid]
          ,[fromdate]
          ,[todate]
          ,[hours]
          ,[comments]
          ,[requestdate]
          ,[status]
          ,[statusby]
          ,[statusdate]
          ,convert(varchar, [requestdate], 121) as requestdatestring
    FROM [dbo].[requests]
    WHERE userid = ? AND [requestdate] = ?""", userid, requestdate)

    rows = cursor.fetchall()

    q = [dict(zip([key[0] for key in cursor.description], row)) for row in rows]

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("--- Get Request ---")

    app.json_encoder = JsonEncoder
    return jsonify({'request': q})


@app.route('/resubmitrequest', methods=['POST'])
def resubmitrequest():
    # username = request.environ.get('REMOTE_USER')

    # Get data from fields
    userid = request.form.get('id')
    fromdate = request.form.get('fromDate')
    fromtime = request.form.get('fromTime')
    todate = request.form.get('toDate')
    totime = request.form.get('toTime')
    hours = request.form.get('hours')
    comments = request.form.get('comments')
    requestdate = request.form.get('requested')

    f = datetime.strptime(fromdate + ' ' + fromtime, '%m/%d/%Y %H%M')
    t = datetime.strptime(todate + ' ' + totime, '%m/%d/%Y %H%M')

    app.logger.info("--- Resubmit Request ---")
    app.logger.info("userid:      " + userid)
    app.logger.info("from:        " + str(f))
    app.logger.info("to:          " + str(t))
    app.logger.info("hours:       " + str(hours))
    app.logger.info("comments:    " + str(comments))
    app.logger.info("requestdate: " + str(requestdate))
    app.logger.info("--- resubmit Request ---")

    sql = """
    UPDATE [dbo].[requests]
      SET [fromdate] = '{}', [todate] = '{}', [hours] = '{}', [comments] = '{}', 
          [status] = 'Pending', [statusby] = '{}', [statusdate] = getdate()
    WHERE [userid] = '{}' AND [requestdate] = '{}'""".format(f, t, hours, str(comments), userid, userid, requestdate)

    app.logger.info(sql)

    cnxn = pyodbc.connect(
      'DRIVER={ODBC Driver 17 for SQL Server};SERVER=chw12ts9r2vb42;DATABASE=LeaveRequest;UID=lr_writer;PWD=lr_writer')
    cursor = cnxn.cursor()

    count = cursor.execute("""
    UPDATE [dbo].[requests]
      SET [fromdate] = ?, [todate] = ?, [hours] = ?, [comments] = ?, 
          [status] = 'Pending', [statusby] = ?, [statusdate] = getdate()
    WHERE [userid] = ? AND [requestdate] = ?""", f, t, hours, str(comments), userid, userid, requestdate).rowcount

    cnxn.commit()
    cursor.close()
    cnxn.close()

    app.logger.info("count: " + str(count))

    return str(count)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088, threaded=True, debug=True)
