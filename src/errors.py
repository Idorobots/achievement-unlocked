import abc


class ApiError(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def http_code(self):
        pass

    @abc.abstractproperty
    def code(self):
        pass

    @abc.abstractproperty
    def message(self):
        pass

    def to_dict(self):
        return {
            'error': {
                'code': self.code,
                'message': self.message
            }
        }


class UnknownAchievementFilter(ApiError):
    def __init__(self, filter_by):
        self.__message = "unknown achievement filter: '{}'".format(filter_by)

    @property
    def message(self):
        return self.__message

    @property
    def code(self):
        return 1000

    @property
    def http_code(self):
        return 400


class UnknownAchievementId(ApiError):
    def __init__(self, achievement_id):
        self.__message = "unknown achievement id: '{}'".format(achievement_id)

    @property
    def message(self):
        return self.__message

    @property
    def code(self):
        return 1001

    @property
    def http_code(self):
        return 404
