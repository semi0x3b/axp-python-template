"""async_client 픽스처 + 헬스체크 엔드포인트 스모크."""


async def test_healthz(async_client):
    response = await async_client.get("/healthz")

    assert response.status_code == 200
