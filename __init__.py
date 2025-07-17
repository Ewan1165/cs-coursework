from bottle import Bottle, run, static_file, HTTPError, request, response
import os, json
from sql import Database

app = Bottle()
db = Database("db.db")

#Define types of files that can be sent from the public directory
mimetypes = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".ico": "image/x-icon"
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

#Apis

#Test Login status code 230: logged in and is an employee, 231: logged in and is a manager, 232: not logged in
@app.route("/api/testLogin", method="POST")
def testLogin():
    body = json.loads(request.body.read())
    loginStatus = db.userLoginStatus(body["FirstName"], body["LastName"], body["LoginCookie"])
    print([body["FirstName"], body["LastName"], body["LoginCookie"]])
    print(loginStatus)
    match loginStatus:
        case 0:
            response.status = 232
        case 1:
            response.status = 230
        case 2:
            response.status = 231
    return

run(app, host="localhost", port=3000)