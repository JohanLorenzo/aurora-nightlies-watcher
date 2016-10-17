class NoPushIdError(Exception):
    def __init__(self, revision):
        super().__init__('No push ID matches revision {}'.format(revision))


class TooManyPushIdsError(Exception):
    def __init__(self, revision):
        super().__init__('More than one push ID matched revision {}'.format(revision))


class UnmatchedRouteError(Exception):
    def __init__(self, field_name, task_definition):
        super().__init__('No {} was found in the routes of: {}'.format(field_name, task_definition))


class NotOnlyOneApkError(Exception):
    def __init__(self, matched_artifacts):
        super().__init__('Not only one artifact matches the APK regex. Matched artifacts: {}'.format(matched_artifacts))
