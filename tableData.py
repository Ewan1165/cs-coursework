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