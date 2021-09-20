import json


def test_index(app, client):
    res = client.get('/')
    assert res.status_code == 200
    expected = {'hello': 'world'}
    assert expected == json.loads(res.get_data(as_text=True))


def test_submitrequest(app, client):
    rv = client.post('/submitrequest', data=dict(
        id="pytestuser",
        fromDate="10/10/2021",
        fromTime="0700",
        toDate="10/11/2021",
        toTime="1600",
        hours="8",
        comments="pytest unit test"
    ), follow_redirects=True)
    assert rv.data == b'1'


def test_gethistory(app, client, capsys):
    rv = client.post('/gethistory', data=dict(
        id="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert b'pytestuser' in rv.data
    assert b'pytest unit test' in rv.data


def test_getpending(app, client, capsys):
    rv = client.post('/getpending', data=dict(
        id="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert b'Pending' in rv.data or rv.data == 'No Requests Pending'


def test_getunassigned(app, client, capsys):
    rv = client.post('/getunassigned', data=dict(
        id="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert b'Pending' in rv.data
    assert b'testuser' in rv.data


def test_assign(app, client, capsys):
    rv = client.post('/assign', data=dict(
        id="CLB\\roperki",
        emp="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert rv.data == b'1'


def test_getreassign(app, client, capsys):
    rv = client.post('/getreassign', data=dict(
        id="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert b'CLB\\\\roperki' in rv.data
    assert b'pytestuser' in rv.data


def test_reassign(app, client, capsys):
    rv = client.post('/reassign', data=dict(
        id="CLB\\roperki",
        emp="pytestuser"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert rv.data == b'1' or rv.data == b'2' or rv.data == b'3' or rv.data == b'4' or rv.data == b'5'


def test_updatestatus(app, client, capsys):
    rv = client.post('/updatestatus', data=dict(
        status="Rejected",
        id="CLB\\roperki",
        emp="pytestuser",
        requestdate="2021-09-19 14:23:59.713"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert rv.data == b'1'


def test_getrequest(app, client, capsys):
    rv = client.post('/getrequest', data=dict(
        id="pytestuser",
        requested="2021-09-19 14:23:59.713"
    ), follow_redirects=True)
    # with capsys.disabled():
    #     print("\n\n")
    #     print(rv.data)
    assert b'pytestuser' in rv.data
    assert b'2021-09-19 14:23:59.713' in rv.data


def test_resubmitrequest(app, client):
    rv = client.post('/resubmitrequest', data=dict(
        id="pytestuser",
        fromDate="10/10/2021",
        fromTime="1200",
        toDate="10/11/2021",
        toTime="1600",
        hours="4",
        comments="pytest unit test",
        requested="2021-09-19 14:23:59.713"
    ), follow_redirects=True)
    assert rv.data == b'1'
