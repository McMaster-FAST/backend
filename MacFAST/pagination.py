from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

# We could just pass ?page=<num> in the frontend but this ensures the backend controls the pagination logic.
class OnlyPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "totalPages": self.page.paginator.num_pages,
                "next": self.get_relative_next_link(),
                "previous": self.get_relative_previous_link(),
                "results": data,
            }
        )

    def get_relative_next_link(self):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        # Return relative path
        return page_number

    def get_relative_previous_link(self):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        # Return relative path
        return page_number

