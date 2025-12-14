import sqlite3 as sql
import tableData
from datetime import datetime, timedelta
from time import time

#define a class to perform all interactions with the database with all validations
class Database:
    def __init__(this, filename):
        #connect to the database
        this.filename = filename
        this.con = sql.connect(filename)
        tables = this.getTables()
        for table in tableData.statements:
            if table not in tables:
                #create the table if it doesnt already exist
                this.query(tableData.statements[table])

    def getTables(this):
        #return all tables that currently exist in the database
        return list(map(lambda x: x[0], this.fetch("SELECT name FROM sqlite_master WHERE type = \"table\";")))

    def query(this, query, data = ()):
        #execute a query that doesnt fetch any data, and commit any changes to the database
        cursor = this.con.cursor()
        cursor.execute(query, data)
        this.con.commit()

    def fetchOne(this, query, data = ()):
        #execute a query that fetches one entry, and return it
        cursor = this.con.cursor()
        cursor.execute(query, data)
        return cursor.fetchone()

    def fetch(this, query, data = ()):
        #execute a query that fetches multiple entries, and return them as an array
        cursor = this.con.cursor()
        cursor.execute(query, data)
        return cursor.fetchall()
    
    #Checks the login status based on name and cookie returns 0 if they arent logged in, 1 if they are an employee or 2 if they are a manager
    def userLoginStatus(this, firstname, lastname, logincookie):
        try:
            cookie, manager = this.fetchOne("SELECT LoginCookie, Manager FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))
        except:
            return 0
        if cookie == None or cookie != logincookie:
            return 0
        if manager == 0:
            return 2
        else:
            return 1
        
    def userNotExists(this, firstname, lastname):
        return len(this.fetch("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))) == 0

    def getUserId(this, firstname, lastname):
        return this.fetchOne("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))[0]

    def getUserIdFromHeader(this, header):
        return this.getUserId(header["FirstName"], header["LastName"])

    def userLoginStatusHeader(this, header):
        return this.userLoginStatus(header["FirstName"], header["LastName"], header["LoginCookie"])

    #Returns true if the password is the same as the one stored in the database
    def testPassword(this, firstname, lastname, password):
        dbPassword = this.fetchOne("SELECT Password FROM tblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))[0]
        return (dbPassword == password)
    
    def updateCookie(this, firstname, lastname, newCookie):
        this.query("UPDATE tblUsers SET LoginCookie = ? WHERE FirstName = ? AND LastName = ?;", (newCookie, firstname, lastname))