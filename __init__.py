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

#Serve the requested file if it exists in public directory
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

#Serve the landing page
@app.route("/")
def serveLandingPage():
    return static_file("index.html", root="public")

#Employee Apis

#Test Login status code 230: logged in and is an employee, 231: logged in and is a manager, 232: not logged in
@app.route("/api/testLogin", method="POST")
def testLogin():
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

#Log user in status code 232: password is incorrect
@app.route("/api/login", method="POST")
def apiLogin():
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
def apiLogout():
    authHeader = json.loads(request.get_header("authorization"))
    loginStatus = db.userLoginStatusHeader(authHeader)
    if loginStatus in [1, 2]:
        db.deleteCookie(authHeader["FirstName"], authHeader["LastName"])

#Admin Apis

@app.route("/api/admin/getManaged", method="POST")
def getManaged():
    authHeader = json.loads(request.get_header("authorization"))
    if not db.isAdminStatusHeader(authHeader):
        response.status = 401
        return
    response.content_type = 'application/json'
    return json.dumps(db.getManagedBy(authHeader["FirstName"], authHeader["LastName"]))

run(app, host="localhost", port=3000)