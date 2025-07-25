import sqlite3 as sql
import tableData

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
    
    def userLoginStatus(this, firstname, lastname, logincookie):
        try:
            cookie, manager = this.fetchOne("SELECT LoginCookie, Manager FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))
        except:
            return 0
        if cookie == None or cookie != logincookie:
            return 0
        print("LOGGED IN")
        if manager == 0:
            return 2
        else:
            return 1
        
    def userLoginStatusHeader(this, header):
        return this.userLoginStatus(header["FirstName"], header["LastName"], header["LoginCookie"])
    
    def isAdminStatusHeader(this, header):
        return (this.userLoginStatusHeader(header) == 2)

    def testPassword(this, firstname, lastname, password):
        dbPassword = this.fetchOne("SELECT Password FROM tblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))[0]
        return (dbPassword == password)
    
    def updateCookie(this, firstname, lastname, newCookie):
        this.query("UPDATE tblUsers SET LoginCookie = ? WHERE FirstName = ? AND LastName = ?;", (newCookie, firstname, lastname))

    def deleteCookie(this, firstname, lastname):
        this.query("UPDATE tblUsers SET LoginCookie = NULL WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))

    def getManagedBy(this, firstname, lastname):
        adminId = this.fetchOne("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))[0]
        return this.fetch("SELECT FirstName, LastName FROM TblUsers WHERE Manager = ?;", (adminId,))

    def getManagers(this):
        return this.fetch("SELECT FirstName, LastName FROM TblUsers WHERE Manager = 0;")
    
    def createAccount(this, firstname, lastname, phonenum, manager):
        if (this.fetchOne("SELECT 1 FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname)) != None):
            return 1
        managerId = this.fetchOne("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (manager[0], manager[1]))[0]
        this.query("INSERT INTO TblUsers (FirstName, LastName, PhoneNumber, Password, Manager) VALUES (?, ?, ?, ?, ?);", (firstname, lastname, phonenum, "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", managerId))
        return 0