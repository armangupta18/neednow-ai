class ProductAgentException(Exception):
    pass


class RetrievalException(
    ProductAgentException
):
    pass


class RankingException(
    ProductAgentException
):
    pass