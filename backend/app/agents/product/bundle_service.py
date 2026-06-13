class BundleService:

    BUNDLES = {

        "party": [
            "chips",
            "soft drinks",
            "cups",
            "plates",
        ],

        "baby": [
            "baby wipes",
            "diapers",
            "formula milk",
        ],

        "medical": [
            "thermometer",
            "pain relief",
        ],
    }

    @staticmethod
    def generate(
        category: str,
        products,
    ):

        keywords = (
            BundleService.BUNDLES
            .get(category, [])
        )

        bundle = []

        for product in products:

            title = product.title.lower()

            if any(
                keyword in title
                for keyword in keywords
            ):
                bundle.append(product)

        return bundle[:5]