from rest_framework.pagination import PageNumberPagination


class FollowPageNumberPagination(PageNumberPagination):
    """Кастомная пагинация для поддержки параметра limit"""
    page_size_query_param = 'limit'
    page_size = 6
    max_page_size = 100


class NoPagination(PageNumberPagination):
    """Отключение пагинации"""
    page_size = None
