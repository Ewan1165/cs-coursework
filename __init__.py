from bottle import Bottle, run, static_file, HTTPError, request, response
import os, json, random
import sha256
from sql import Database
from time import time
from datetime import datetime, timedelta

app = Bottle()
db = Database("db.db")

#Define types of files that can be sent from the public directory
mimetypes = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml"
}

#Serve the requested file if it exists in public directory (for html, css and other resource files)
@app.route("/<filepath:path>")
def serveStatic(filepath):
    fullPath = os.path.join("public", filepath)

    #Append index.html to the file path if the request url is a directory in public
    if os.path.isdir(fullPath):
        fullPath = os.path.join(fullPath, "index.html")
        filepath = os.path.join(filepath, "index.html")

    #Serve the file with the correct mime for the file extension otherwise return 404
    extension = os.path.splitext(fullPath)[1].lower()
    if os.path.isfile(fullPath):
        return static_file(filepath, root="public", mimetype=mimetypes[extension])
    else:
        return HTTPError(404, "Page not found")

#Serve the landing page which redirects the user to the correct page based on their login status
@app.route("/")
def serveLandingPage():
    return static_file("index.html", root="public")

#Employee Apis

def checkLoggedIn(function):
    def wrapper():
        authHeader = json.loads(request.get_header("authorization"))
        if db.userLoginStatusHeader(authHeader) in [1,2]:
            rawBody = request.body.read()
            if rawBody:
                body = json.loads(rawBody)
            else:
                body = None
            return function(authHeader, body)
        else:
            response.status = 232
    return wrapper
        
def checkLoggedInAdmin(function):
    def wrapper():
        authHeader = json.loads(request.get_header("authorization"))
        if db.userLoginStatusHeader(authHeader) == 2:
            rawBody = request.body.read()
            if rawBody:
                body = json.loads(rawBody)
            else:
                body = None
            return function(authHeader, body)
        else:
            response.status = 401
    return wrapper

#Test Login status code 230: logged in and is an employee, 231: logged in and is a manager, 232: not logged in
@app.route("/api/testLogin", method="POST")
def api_testLogin():
    authHeader = json.loads(request.get_header("authorization"))
    print(authHeader)
    loginStatus = db.userLoginStatusHeader(authHeader)
    match loginStatus:
        case 0:
            response.status = 232
        case 1:
            response.status = 230
        case 2:
            response.status = 231
    return

#Log user in status code 230: password is correct (sent back new login cookie) 232: password is incorrect
@app.route("/api/login", method="POST")
def api_Login():
    authHeader = json.loads(request.get_header("authorization"))
    hashedPassword = sha256.hash(authHeader["Password"])
    correctPassword = db.testPassword(authHeader["FirstName"], authHeader["LastName"], hashedPassword)
    if correctPassword == False:
        response.status = 232
        return
    newCookie = random.randint(100000000000, 999999999999)
    db.updateCookie(authHeader["FirstName"], authHeader["LastName"], newCookie)
    response.status = 230
    response.content_type = 'application/json'
    return json.dumps({"LoginCookie": newCookie})

#Logs user out by deleting their cookie
@app.route("/api/logout", method="POST")
@checkLoggedIn
def api_Logout(authHeader, body):
    db.query("UPDATE tblUsers SET LoginCookie = NULL WHERE FirstName = ? AND LastName = ?;", (authHeader["firstname"], authHeader["lastname"]))

#Insers a request into the database
@app.route("/api/createrequest", method="POST")
@checkLoggedIn
def api_createrequest(authHeader, body):
    userId = db.getUserIdFromHeader(authHeader)
    db.query("INSERT INTO TblRequests (UserID, Accepted, RequestType, StartTime, Length) VALUES (?, false, ?, ?, ?);", (userId, body["requesttype"], body["timestamp"], body["length"]))

#Create an entry into TblClockIn with InOrOut attribute of body.status
@app.route("/api/setclockstatus", method="POST")
@checkLoggedIn
def api_setclockstatus(authHeader, body):
    userId = db.getUserIdFromHeader(authHeader)
    currTime = int(time())
    db.query("INSERT INTO TblClockIn (UserID, Time, InOrOut) VALUES (?, ?, ?);", (userId, currTime, body["status"]))

#Returns InOrOut property of last entry in TblClockIn created by currently logged in user
@app.route("/api/getclockstatus", method="GET")
@checkLoggedIn
def api_getClockStatus(authHeader, body):
    try:
        status = db.fetchOne("""SELECT InOrOut FROM TblClockIn, TblUsers WHERE
            TblUsers.UserID = TblClockIn.UserID AND FirstName = ? AND LastName = ? ORDER BY Time DESC;""", (authHeader["FirstName"], authHeader["LastName"]))[0]
    except:
        userID = db.getUserIdFromHeader(authHeader)
        status = db.query("INSERT INTO TblClockIn (UserID, Time, InOrOut) VALUES (?, ?, 0);", (userID, time()))
    
    response.content_type = 'application/json'
    return json.dumps({"status": status})

#Sends a json list of all accepted requests which are in the current week
@app.route("/api/gettimetable", method="GET")
@checkLoggedIn
def api_gettimetable(authHeader, body):
    now = datetime.now()
    startofweek = now - timedelta(days=now.weekday())
    startofweek = startofweek.replace(hour=0, minute=0, second=0, microsecond=0)
    startofweek = int(startofweek.timestamp()) * 1000
    endofweek = startofweek + 604800000
    
    events = db.fetch("""
                SELECT RequestType, StartTime, Length FROM TblRequests, TblUsers
                WHERE TblRequests.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Accepted = true
                AND StartTime < ? AND StartTime + Length > ?;""", (authHeader["FirstName"], authHeader["LastName"], endofweek, startofweek))
    
    response.content_type = 'application/json'
    return json.dumps(events)

#Hashes then updates password in the database
@app.route("/api/changepassword", method="POST")
@checkLoggedIn
def api_changepassword(authHeader, body):
    newpass = body["newpassword"]
    hashedpass = sha256.hash(newpass)
    db.query("UPDATE TblUsers SET Password = ? WHERE FirstName = ? AND LastName = ?;", (hashedpass, authHeader["FirstName"], authHeader["LastName"]))

#Returns the 5 most recent unread and 5 most recent read notifications
@app.route("/api/getnotifications", method="GET")
@checkLoggedIn
def api_getnotifications(authHeader, body):
    unread = db.fetch("""SELECT Title, Body, Read, NotificationID FROM TblNotification, TblUsers
                        WHERE TblNotification.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Read = false
                        ORDER BY NotificationID DESC;""", (authHeader["FirstName"], authHeader["LastName"]))

    read = db.fetch("""SELECT Title, Body, Read, NotificationID FROM TblNotification, TblUsers
                        WHERE TblNotification.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Read = true
                        ORDER BY NotificationID DESC LIMIT 5;""", (authHeader["FirstName"], authHeader["LastName"]))
    
    return json.dumps(unread + read)

#Sets the notification specified by the user as read
@app.route("/api/readnotification", method="POST")
@checkLoggedIn
def api_readnotification(authHeader, body):
    db.query("UPDATE TblNotification SET Read = true WHERE NotificationID = ?;", (body["notifid"], ))


#Gets all people who the user has messaged or recieved messages from
@app.route("/api/getmessagepeople", method="GET")
@checkLoggedIn
def api_getmessagepeople(authHeader, body):
    userid =  db.getUserIdFromHeader(authHeader)
    people = db.fetch("""
        SELECT DISTINCT FirstName, LastName FROM (
        SELECT FirstName, LastName, Timestamp FROM TblMessages, TblUsers WHERE TblMessages.SenderID = TblUsers.UserID AND TblMessages.ReceiverID = ?
        UNION SELECT FirstName, LastName, Timestamp FROM TblMessages, TblUsers WHERE TblMessages.ReceiverID = TblUsers.UserID AND TblMessages.SenderID = ?
        ) ORDER BY Timestamp DESC;
    """, (userid, userid))
    return json.dumps(people)

#Returns all messages between the 2 users
@app.route("/api/getmessages", method="POST")
@checkLoggedIn
def api_getmessages(authHeader, body):
    id1 = db.getUserIdFromHeader(authHeader)
    id2 = db.getUserId(body["firstname"], body["lastname"])
    msgs = db.fetch("""SELECT Body, Timestamp, CASE WHEN SenderID = ? THEN 1 ELSE 0 END AS Direction
                        From TblMessages WHERE
                        (SenderID = ? AND ReceiverID = ?) OR (SenderID = ? AND ReceiverID = ?) ORDER BY Timestamp ASC;""", (id1, id1, id2, id2, id1))
    
    return json.dumps(msgs)

#Create an entry into TblMessages
@app.route("/api/sendmessage", method="POST")
@checkLoggedIn
def api_sendmessage(authHeader, body):
    senderID = db.getUserIdFromHeader(authHeader)
    reveiverID = db.getUserId(body["firstname"], body["lastname"])
    timestamp = int(time())
    db.query("INSERT INTO TblMessages (SenderID, ReceiverID, Body, Timestamp) VALUES (?, ?, ?, ?);", (senderID, reveiverID, body["msg"], timestamp))

#Admin Apis

#Gets all first and last names of the users who are managed by the manager who sent the web request
@app.route("/api/admin/getmanaged", method="POST")
@checkLoggedInAdmin
def api_getManaged(authHeader, body):
    response.content_type = 'application/json'
    adminId = db.getUserIdFromHeader(authHeader)
    users = db.fetch("SELECT FirstName, LastName FROM TblUsers WHERE Manager = ?;", (adminId,))
    return json.dumps(users)

#Gets the first and last names of all managers in the database
@app.route("/api/admin/getmanagers")
@checkLoggedInAdmin
def api_getManagers(authHeader, body):
    response.content_type = 'application/json'
    managers = db.fetch("SELECT FirstName, LastName FROM TblUsers WHERE Manager = 0;")
    return json.dumps(managers)

#Create a new employee account with the password "password"
@app.route("/api/admin/createaccount", method="POST")
@checkLoggedInAdmin
def api_createAccount(authHeader, body):
    if (db.fetchOne("SELECT 1 FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (body["FirstName"], body["LastName"])) != None):
        response.status = 241
        return
    manager = body["Manager"]
    managerId = db.getUserId(manager[0], manager[1])
    db.query("INSERT INTO TblUsers (FirstName, LastName, PhoneNumber, Password, Manager) VALUES (?, ?, ?, ?, ?);", (body["FirstName"], body["LastName"], body["PhoneNum"], "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", managerId))
    response.status = 240

#Gets all leave and overtime requests from employees managed by the user who sent the web request
@app.route("/api/admin/getrequests", method="POST")
@checkLoggedInAdmin
def api_getrequests(authHeader, body):
    response.content_type = 'application/json'
    adminId = db.getUserIdFromHeader(authHeader)
    requests = db.fetch("""SELECT RequestType, StartTime, Length, FirstName, LastName, RequestID
                        FROM TblUsers, TblRequests
                        WHERE TblUsers.UserID = TblRequests.UserID AND Manager = ? AND Accepted = false;""", (adminId, ))
    return json.dumps(requests)

#Accepts an overtime or leave request by setting the value of its accepted attribute to true
@app.route("/api/admin/acceptrequest", method="POST")
@checkLoggedInAdmin
def api_acceptrequest(authHeader, body):
    db.query("UPDATE TblRequests SET Accepted = 1 WHERE RequestID = ?;", (body["requestid"], ))

#Deletes an overtime or leave request from the database
@app.route("/api/admin/deleterequest", method="POST")
@checkLoggedInAdmin
def api_deleterequest(authHeader, body):
    db.query("DELETE FROM TblRequests WHERE RequestID = ?;", (body["requestid"], ))

#Resets a users password to "password"
@app.route("/api/admin/resetpassword", method="POST")
@checkLoggedInAdmin
def api_resetpassword(authHeader, body):
    db.query("UPDATE TblUsers SET Password = \"5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8\" WHERE FirstName = ? AND LastName = ?;", (body["firstname"], body["lastname"]))

#Deletes a user from the database
@app.route("/api/admin/removeuser", method="POST")
@checkLoggedInAdmin
def api_removeuser(authHeader, body):
    db.query("PRAGMA foreign_keys = ON;")
    db.query("DELETE FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (body["firstname"], body["lastname"]))

@app.route("/api/admin/getuserdata", method="POST")
@checkLoggedInAdmin
def api_getuserdata(authHeader, body):
    now = datetime.now()
    thismonday = now - timedelta(days=now.weekday())
    thismonday = thismonday.replace(hour=0, minute=0, second=0, microsecond=0)
    thismondaytimestamp = int(thismonday.timestamp())
    data = []
    for i in range(2, 22):
        startofweek = thismondaytimestamp - (i * 604800)
        endofweek = startofweek + 604799
        allclocks = db.fetch("""SELECT Time, InOrOut FROM TblClockIn, TblUsers
                             WHERE TblClockIn.UserID = TblUsers.UserID AND FirstName = ?
                             AND LastName = ? AND Time < ? AND Time > ?;""", (body["firstname"], body["lastname"], endofweek, startofweek))
        timeSpent = 0
        lastTimestamp = 0
        for i in range(len(allclocks)):
            if allclocks[i][1] == 1 and lastTimestamp == 0:
                lastTimestamp = allclocks[i][0]
            elif allclocks[i][1] == 0 and lastTimestamp != 0:
                timeSpent += allclocks[i][0] - lastTimestamp
                lastTimestamp = 0
        hoursSpent = int(timeSpent / 3600)
        data.append(hoursSpent)

    response.content_type = 'application/json'
    return json.dumps(data)

run(app, host="localhost", port=3000)
