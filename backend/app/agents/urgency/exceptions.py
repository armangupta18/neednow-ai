class UrgencyAgentException(Exception):
    pass


class UrgencyParsingException(UrgencyAgentException):
    pass


class UrgencyValidationException(UrgencyAgentException):
    pass