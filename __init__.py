from bottle import Bottle, run, static_file, HTTPError, request, response
import os, json, random
import sha256
from sql import Database

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
def api_Logout():
    authHeader = json.loads(request.get_header("authorization"))
    loginStatus = db.userLoginStatusHeader(authHeader)
    if loginStatus in [1, 2]:
        db.deleteCookie(authHeader["FirstName"], authHeader["LastName"])

#Insers a request into the database
@app.route("/api/createrequest", method="POST")
def api_createrequest():
    authHeader = json.loads(request.get_header("authorization"))
    loginStatus = db.userLoginStatusHeader(authHeader)
    if loginStatus in [1, 2]:
        body = json.loads(request.body.read())
        db.createRequestFromHeader(authHeader, body["requesttype"], body["timestamp"], body["length"])

#Create an entry into TblClockIn with InOrOut attribute of body.status
@app.route("/api/setclockstatus", method="POST")
def api_setclockstatus():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        status = json.loads(request.body.read())["status"]
        db.setClockStatus(authHeader, status)

#Returns InOrOut property of last entry in TblClockIn created by currently logged in user
@app.route("/api/getclockstatus", method="GET")
def api_getClockStatus():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        status = db.getClockStatus(authHeader)
        return json.dumps({"status": status})

#Sends a json list of all accepted requests which are in the current week
@app.route("/api/gettimetable", method="GET")
def api_gettimetable():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        events = db.getWeekEvents(authHeader)
        response.content_type = 'application/json'
        return json.dumps(events)

#Hashes then updates password in the database
@app.route("/api/changepassword", method="POST")
def api_changepassword():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        newpass = json.loads(request.body.read())["newpassword"]
        hashedpass = sha256.hash(newpass)
        db.updatePassword(authHeader, hashedpass)

#Returns the 5 most recent unread and 5 most recent read notifications
@app.route("/api/getnotifications", method="GET")
def api_getnotifications():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        unread = db.getUnreadNotifications(authHeader)
        read = db.getReadNotifications(authHeader)
        return json.dumps(unread + read)

#Sets the notification specified by the user as read
@app.route("/api/readnotification", method="POST")
def api_readnotification():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        body = json.loads(request.body.read())
        db.setNotifRead(body["notifid"])

#Gets all people who the user has messaged or recieved messages from
@app.route("/api/getmessagepeople", method="GET")
def api_getmessagepeople():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        return json.dumps(db.getMessagePeople(authHeader))

#Returns all messages between the 2 users
@app.route("/api/getmessages", method="POST")
def api_getmessages():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        body = json.loads(request.body.read())
        return json.dumps(db.getMessages(authHeader, body["firstname"], body["lastname"]))

#Create an entry into TblMessages
@app.route("/api/sendmessage", method="POST")
def api_sendmessage():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) in [1,2]:
        body = json.loads(request.body.read())
        db.sendMessage(authHeader, body["firstname"], body["lastname"], body["msg"])

#Admin Apis

#Gets all first and last names of the users who are managed by the manager who sent the web request
@app.route("/api/admin/getmanaged", method="POST")
def api_getManaged():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) != 2:
        response.status = 401
        return
    response.content_type = 'application/json'
    return json.dumps(db.getManagedBy(authHeader["FirstName"], authHeader["LastName"]))

#Gets the first and last names of all managers in the database
@app.route("/api/admin/getmanagers")
def api_getManagers():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    response.content_type = 'application/json'
    return json.dumps(db.getManagers())

#Create a new employee account with the password "password"
@app.route("/api/admin/createaccount", method="POST")
def api_createAccount():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    bodyData = json.loads(request.body.read())
    print(bodyData)
    success = db.createAccount(bodyData["FirstName"], bodyData["LastName"], bodyData["PhoneNum"], bodyData["Manager"])
    if success == 0:
        response.status = 240
    if success == 1:
        response.status = 241

#Gets all leave and overtime requests from employees managed by the user who sent the web request
@app.route("/api/admin/getrequests", method="POST")
def api_getrequests():
    authHeader = json.loads(request.get_header("authorization"))
    if db.userLoginStatusHeader(authHeader) != 2:
        response.status = 401
        return

    response.content_type = 'application/json'
    return json.dumps(db.getRequestsByHeader(authHeader))

#Accepts an overtime or leave request by setting the value of its accepted attribute to true
@app.route("/api/admin/acceptrequest", method="POST")
def api_acceptrequest():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    
    db.acceptRequest(json.loads(request.body.read())["requestid"])

#Deletes an overtime or leave request from the database
@app.route("/api/admin/deleterequest", method="POST")
def api_deleterequest():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    
    db.deleterequest(json.loads(request.body.read())["requestid"])

@app.route("/api/admin/resetpassword", method="POST")
def api_resetpassword():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    body = json.loads(request.body.read())
    db.resetPassword(body["firstname"], body["lastname"])

@app.route("/api/admin/removeuser", method="POST")
def api_removeuser():
    if db.userLoginStatusHeader(json.loads(request.get_header("authorization"))) != 2:
        response.status = 401
        return
    body = json.loads(request.body.read())
    db.removeUser(body["firstname"], body["lastname"])

run(app, host="localhost", port=3000)