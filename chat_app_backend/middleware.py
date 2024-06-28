import logging
import time
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CustomLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        request.start_datetime = datetime.now()

    def process_response(self, request, response):
        # Lấy thời gian xử lý
        duration = time.time() - request.start_time

        # Lấy thông tin method và URL
        method = request.method
        url = request.get_full_path()

        # Lấy thời gian bắt đầu yêu cầu
        request_time = request.start_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Tạo message log
        message = (
            f"[{request_time}] {method} {url} - Status: {response.status_code} - "
            f"Duration: {duration:.2f}s - Message: {response.data.get('message', '') if hasattr(response, 'data') else ''}"
        )

        # Ghi log thông tin chi tiết
        logger.info(message)

        return response

    def process_exception(self, request, exception):
        # Lấy thời gian xử lý
        duration = time.time() - request.start_time

        # Lấy thông tin method và URL
        method = request.method
        url = request.get_full_path()

        # Lấy thời gian bắt đầu yêu cầu
        request_time = request.start_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Tạo message log cho exception
        message = (
            f"[{request_time}] {method} {url} - Exception: {exception} - "
            f"Duration: {duration:.2f}s"
        )

        # Ghi log thông tin chi tiết
        logger.error(message, exc_info=True)
