class ValidationError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is not None:
            return u'{0}: {1}'.format(self.__class__.__name__, self.msg)
        else:
            return self.__class__.__name__


class UnknownParticipantError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is not None:
            return u'{0}: {1}'.format(self.__class__.__name__, self.msg)
        else:
            return self.__class__.__name__
