# from fastapi_sqlalchemy_filter import Filter, FilterDepends, with_prefix
# from app.accounts.models import Transactions
# from typing import List
# # from pydantic import Field


# class TransactionBaseFilter(Filter):
#     transaction_id: str | None

#     class Constants(Filter.Constants):
#         model = Transactions
#         search_field_name = "transaction_id"
#         search_model_fields = ["cash_flow", "status", "service"]


# class TransactionFilter(TransactionBaseFilter):
#     order_by: List[str] | None
