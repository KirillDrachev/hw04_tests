from django.core.paginator import Paginator

MAX_POSTS_ON_PAGE: int = 10


def by_page(request, list):
    paginator = Paginator(list, MAX_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
