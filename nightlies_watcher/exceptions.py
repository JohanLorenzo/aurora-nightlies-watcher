class NoPushIdError(Exception):
    def __init__(self, revision):
        super().__init__('No push ID matches revision {}'.format(revision))


class TooManyPushIdsError(Exception):
    def __init__(self, revision):
        super().__init__('More than one push ID matched revision {}'.format(revision))
