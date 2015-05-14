import abc


class AppError(Exception, metaclass=abc.ABCMeta):
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


class ApiError(AppError):
    pass


class UnknownAchievementFilter(ApiError):
    def __init__(self, filter_by):
        self.__message = "Unknown achievement filter: '{}'.".format(filter_by)

    @property
    def message(self):
        return self.__message

    @property
    def code(self):
        return "unknown_achievement_filter"

    @property
    def http_code(self):
        return 400


class UnknownAchievementId(ApiError):
    def __init__(self, achievement_id):
        self.__message = "Unknown achievement id: '{}'.".format(achievement_id)

    @property
    def message(self):
        return self.__message

    @property
    def code(self):
        return "unknown_achievement_id"

    @property
    def http_code(self):
        return 404


class InternalError(AppError):
    @property
    def http_code(self):
        return 500

    @property
    def code(self):
        return "internal_server_error"

    @property
    def message(self):
        return "U dun goofed."


class UnknownHandler(InternalError):
    def __init__(self, handler):
        self.__message = "Unknown handler: '{}'.".format(handler)

    @property
    def code(self):
        return "unknown_handler"

    @property
    def message(self):
        return self.__message
