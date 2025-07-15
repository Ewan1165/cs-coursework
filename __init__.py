from bottle import Bottle, run, static_file, HTTPError
import os

app = Bottle()

mimetypes = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css"
}

@app.route("/<filepath:path>")
def serveStatic(filepath):
    fullPath = os.path.join("public", filepath)

    if os.path.isdir(fullPath):
        fullPath = os.path.join(fullPath, "index.html")
        filepath = os.path.join(filepath, "index.html")

    extension = os.path.splitext(fullPath)[1].lower()
    if os.path.isfile(fullPath):
        return static_file(filepath, root="public", mimetype=mimetypes[extension])
    else:
        return HTTPError(404, "Page not found")


@app.route("/")
def serveLandingPage():
    return static_file("index.html", root="public")

run(app, host="localhost", port=3000)