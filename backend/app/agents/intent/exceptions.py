class IntentAgentException(Exception):
    pass


class IntentParsingException(IntentAgentException):
    pass


class IntentValidationException(IntentAgentException):
    pass