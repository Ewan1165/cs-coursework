import sqlite3 as sql

tableData = {
    "TblUsers": """
        CREATE TABLE TblUsers (
            UserID integer,
            FirstName text,
            LastName text,
            PhoneNumber text,
            Password text,
            LoginCookie integer,
            Manager integer,
            PRIMARY KEY (UserID)
        );
    """,
    "TblRequests": """
        CREATE TABLE TblRequests (
            RequestID integer,
            UserID integer,
            Accepted bool,
            RequestType integer,
            StartTime integer,
            Length integer,
            PRIMARY KEY (RequestID),
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID)
        );
    """,
    "TblSlots": """
        CREATE TABLE TblSlots (
            SlotID integer,
            UserID integer,
            StartTime integer,
            Length integer,
            PRIMARY KEY (SlotID),
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID)
        );
    """,
    "TblClockIn": """
        CREATE TABLE TblClockIn (
            ClockInId integer,
            UserID integer,
            Time integer,
            InOrOut integer,
            PRIMARY KEY (ClockInId),
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID)
        );
    """,
    "TblMessages": """
        CREATE TABLE TblMessages (
            MessageID integer,
            SenderID integer,
            ReceiverID integer,
            Body text,
            Timestamp integer,
            PRIMARY KEY (MessageID),
            FOREIGN KEY (SenderID) REFERENCES TblUsers(UserID),
            FOREIGN KEY (ReceiverID) REFERENCES TblUsers(UserID)
        );
    """,
    "TblNotification": """
        CREATE TABLE TblNotification (
            NotificationID integer,
            UserID integer,
            Title text,
            Body text,
            MessageID integer,
            Read bool,
            PRIMARY KEY (NotificationID),
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID),
            FOREIGN KEY (MessageID) REFERENCES TblMessages(MessageID)
        );
    """
}

#define a class to perform all interactions with the database with all validations
class Database:
    def __init__(this, filename):
        #connect to the database
        this.filename = filename
        this.con = sql.connect(filename)
        tables = this.getTables()
        for table in tableData:
            if table not in tables:
                #create the table if it doesnt already exist
                this.query(tableData[table])

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
        print([cookie, manager])
        if cookie == None or cookie != logincookie:
            return 0
        if manager == 0:
            return 2
        else:
            return 1