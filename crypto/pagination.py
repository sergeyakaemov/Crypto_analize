from rest_framework.pagination import CursorPagination


class CoinCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-id"
