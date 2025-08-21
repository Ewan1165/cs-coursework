statements = {
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
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID) ON DELETE SET NULL
        );
    """,
    "TblClockIn": """
        CREATE TABLE TblClockIn (
            ClockInId integer,
            UserID integer,
            Time integer,
            InOrOut integer,
            PRIMARY KEY (ClockInId),
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID) ON DELETE SET NULL
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
            FOREIGN KEY (SenderID) REFERENCES TblUsers(UserID) ON DELETE SET NULL,
            FOREIGN KEY (ReceiverID) REFERENCES TblUsers(UserID) ON DELETE SET NULL
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
            FOREIGN KEY (UserID) REFERENCES TblUsers(UserID) ON DELETE SET NULL,
            FOREIGN KEY (MessageID) REFERENCES TblMessages(MessageID)
        );
    """
}