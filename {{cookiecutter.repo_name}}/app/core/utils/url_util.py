"""URL 파싱/조작 유틸리티."""

from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse


class URLUtil:
    """URL 관련 유틸리티 함수 모음."""

    @staticmethod
    def bump_version(url: str, next_v: int) -> str:
        """URL의 v 쿼리 파라미터를 설정한다 (캐시 무효화용).

        Args:
            url: 대상 URL.
            next_v: 설정할 버전 번호.

        Returns:
            v 파라미터가 설정된 URL.
        """
        return URLUtil.set_query_param(url, "v", next_v)

    @staticmethod
    def get_extension(raw_url: str) -> str:
        """URL에서 파일 확장자를 추출한다 (.포함).

        Args:
            raw_url: 대상 URL.

        Returns:
            확장자 (예: ".png"). 없으면 빈 문자열.
        """
        path = urlparse(unquote(raw_url)).path
        if "." in path:
            return "." + path.rsplit(".", 1)[-1].lower()
        return ""

    @staticmethod
    def get_filename(raw_url: str) -> str:
        """URL에서 파일명을 추출한다.

        Args:
            raw_url: 대상 URL.

        Returns:
            파일명 (예: "image.png").
        """
        path = urlparse(unquote(raw_url)).path
        return path.rsplit("/", 1)[-1] if "/" in path else path

    @staticmethod
    def get_path(url: str) -> str:
        """URL에서 경로만 추출한다 (스킴/도메인 제외).

        Args:
            url: 대상 URL.

        Returns:
            경로 (예: "/posts/images/abc.png").
        """
        return unquote(urlparse(url).path)

    @staticmethod
    def get_query_param(url: str, key: str) -> str | None:
        """URL에서 특정 쿼리 파라미터 값을 조회한다.

        Args:
            url: 대상 URL.
            key: 쿼리 파라미터 키.

        Returns:
            파라미터 값. 없으면 None.
        """
        params = parse_qs(urlparse(url).query)
        values = params.get(key)
        return values[0] if values else None

    @staticmethod
    def set_query_param(url: str, key: str, value: str | int | None) -> str:
        """URL에 쿼리 파라미터를 설정하거나 제거한다.

        Args:
            url: 대상 URL.
            key: 쿼리 파라미터 키.
            value: 설정할 값. None이면 해당 키를 제거.

        Returns:
            수정된 URL.
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        if value is None:
            params.pop(key, None)
        else:
            params[key] = [str(value)]

        query_string = urlencode({k: v[0] for k, v in params.items()})
        return urlunparse(parsed._replace(query=query_string))
