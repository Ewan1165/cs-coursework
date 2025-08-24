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
    
    def createRequestFromHeader(this, header, requesttype, timestamp, length):
        userId = this.fetchOne("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (header["FirstName"], header["LastName"]))[0]
        this.query("INSERT INTO TblRequests (UserID, Accepted, RequestType, StartTime, Length) VALUES (?, false, ?, ?, ?);", (userId, requesttype, timestamp, length))

    def getRequestsByHeader(this, header):
        adminId = this.fetchOne("SELECT UserID FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (header["FirstName"], header["LastName"]))[0]
        return this.fetch("""SELECT RequestType, StartTime, Length, FirstName, LastName, RequestID
                          FROM TblUsers, TblRequests
                          WHERE TblUsers.UserID = TblRequests.UserID AND Manager = ? AND Accepted = false;""", (adminId, ))
    
    def acceptRequest(this, id):
        this.query("UPDATE TblRequests SET Accepted = 1 WHERE RequestID = ?;", (id, ))

    def deleterequest(this, id):
        this.query("DELETE FROM TblRequests WHERE RequestID = ?;", (id, ))

    def setClockStatus(this, header, status):
        userId = this.getUserIdFromHeader(header)
        currTime = int(time())
        this.query("INSERT INTO TblClockIn (UserID, Time, InOrOut) VALUES (?, ?, ?);", (userId, currTime, status))

    def getClockStatus(this, header):
        try:
            return this.fetchOne("""SELECT InOrOut FROM TblClockIn, TblUsers WHERE
                                 TblUsers.UserID = TblClockIn.UserID AND FirstName = ? AND LastName = ? ORDER BY Time DESC;""", (header["FirstName"], header["LastName"]))[0]
        except:
            userID = this.getUserIdFromHeader(header)
            this.query("INSERT INTO TblClockIn (UserID, Time, InOrOut) VALUES (?, ?, 0);", (userID, time()))

    def getWeekEvents(this, header):
        now = datetime.now()
        startofweek = now - timedelta(days=now.weekday())
        startofweek = startofweek.replace(hour=0, minute=0, second=0, microsecond=0)
        startofweek = int(startofweek.timestamp()) * 1000
        endofweek = startofweek + 604800000
        
        events = this.fetch("""
                   SELECT RequestType, StartTime, Length FROM TblRequests, TblUsers
                   WHERE TblRequests.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Accepted = true
                   AND StartTime < ? AND StartTime + Length > ?;""", (header["FirstName"], header["LastName"], endofweek, startofweek))
        return events
    
    def updatePassword(this, header, hashedpass):
        this.query("UPDATE TblUsers SET Password = ? WHERE FirstName = ? AND LastName = ?;", (hashedpass, header["FirstName"], header["LastName"]))

    def resetPassword(this, firstname, lastname):
        this.query("UPDATE TblUsers SET Password = \"5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8\" WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))

    def removeUser(this, firstname, lastname):
        this.query("PRAGMA foreign_keys = ON;")
        this.query("DELETE FROM TblUsers WHERE FirstName = ? AND LastName = ?;", (firstname, lastname))

    def getUnreadNotifications(this, header):
        return this.fetch("""SELECT Title, Body, Read, NotificationID FROM TblNotification, TblUsers
                          WHERE TblNotification.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Read = false
                          ORDER BY NotificationID DESC;""", (header["FirstName"], header["LastName"]))

    def getReadNotifications(this, header):
        return this.fetch("""SELECT Title, Body, Read, NotificationID FROM TblNotification, TblUsers
                          WHERE TblNotification.UserID = TblUsers.UserID AND FirstName = ? AND LastName = ? AND Read = true
                          ORDER BY NotificationID DESC LIMIT 5;""", (header["FirstName"], header["LastName"]))
    
    def setNotifRead(this, notifid):
        this.query("UPDATE TblNotification SET Read = true WHERE NotificationID = ?;", (notifid, ))

    def getMessagePeople(this, header):
        userid =  this.getUserIdFromHeader(header)
        return this.fetch("""
            SELECT DISTINCT FirstName, LastName FROM (
            SELECT FirstName, LastName, Timestamp FROM TblMessages, TblUsers WHERE TblMessages.SenderID = TblUsers.UserID AND TblMessages.ReceiverID = ?
            UNION SELECT FirstName, LastName, Timestamp FROM TblMessages, TblUsers WHERE TblMessages.ReceiverID = TblUsers.UserID AND TblMessages.SenderID = ?
            ) ORDER BY Timestamp DESC;
        """, (userid, userid))
    
    def getMessages(this, header, firstname, lastname):
        id1 = this.getUserIdFromHeader(header)
        id2 = this.getUserId(firstname, lastname)
        return this.fetch("""SELECT Body, Timestamp, CASE WHEN SenderID = ? THEN 1 ELSE 0 END AS Direction
                          From TblMessages WHERE
                          (SenderID = ? AND ReceiverID = ?) OR (SenderID = ? AND ReceiverID = ?) ORDER BY Timestamp ASC;""", (id1, id1, id2, id2, id1))
    
    def sendMessage(this, header, firstname, lastname, msg):
        senderID = this.getUserIdFromHeader(header)
        reveiverID = this.getUserId(firstname, lastname)
        timestamp = int(time())
        this.query("INSERT INTO TblMessages (SenderID, ReceiverID, Body, Timestamp) VALUES (?, ?, ?, ?);", (senderID, reveiverID, msg, timestamp))