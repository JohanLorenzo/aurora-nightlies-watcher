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


class TaskNotFoundError(Exception):
    def __init__(self, repository, revision, missing_android_architecture):
        self.missing_android_architecture = missing_android_architecture
        super().__init__('Task for architecture {} and revision {} in repository {} does not exist'.format(
            missing_android_architecture, revision, repository
        ))


class TreeherderJobAlreadyExistError(Exception):
    def __init__(self, repository, revision, job_name):
        super().__init__('"{}" already exists for revision "{}" in repository "{}"'.format(
            job_name, repository, revision
        ))


class NoTreeherderResultSetError(Exception):
    def __init__(self, repository, revision):
        super().__init__('No result found for revision {} in repository {}'.format(revision, repository))


class TooManyTreeherderResultSetsError(Exception):
    def __init__(self, repository, revision):
        super().__init__('More than 1 result matches revision {} in repository {}'.format(revision, repository))
