"""Tests for utils module."""

from datetime import datetime

from mcp_server_inoreader.utils import (
    chunk_list,
    days_to_timestamp,
    extract_item_ids,
    format_article_list,
    format_feed_list,
    parse_article,
    parse_feed,
)


class TestParseArticle:
    def test_parse_article_basic(self):
        item = {
            "id": "tag:google.com,2005:reader/item/123",
            "title": "Test Article",
            "published": 1700000000,
            "author": "Test Author",
            "origin": {"title": "Test Feed", "streamId": "feed/123"},
            "categories": [],
            "alternate": [{"type": "text/html", "href": "https://example.com"}],
            "summary": {"content": "Test summary"},
        }

        result = parse_article(item)

        assert result["id"] == "tag:google.com,2005:reader/item/123"
        assert result["title"] == "Test Article"
        assert result["author"] == "Test Author"
        assert result["feed_title"] == "Test Feed"
        assert result["url"] == "https://example.com"
        assert result["is_read"] is False

    def test_parse_article_with_read_category(self):
        item = {
            "id": "tag:google.com,2005:reader/item/123",
            "title": "Test Article",
            "published": 1700000000,
            "author": "Test Author",
            "origin": {"title": "Test Feed", "streamId": "feed/123"},
            "categories": [{"id": "user/-/state/com.google/read", "label": "Read"}],
        }

        result = parse_article(item)

        assert result["is_read"] is True


class TestParseFeed:
    def test_parse_feed_basic(self):
        subscription = {
            "id": "feed/123",
            "title": "Test Feed",
            "url": "https://example.com/feed",
            "htmlUrl": "https://example.com",
            "categories": [{"label": "Tech"}],
            "firstitemmsec": 1700000000,
        }

        result = parse_feed(subscription)

        assert result["id"] == "feed/123"
        assert result["title"] == "Test Feed"
        assert result["url"] == "https://example.com/feed"
        assert result["categories"] == ["Tech"]


class TestDaysToTimestamp:
    def test_days_to_timestamp(self):
        result = days_to_timestamp(7)
        expected = int(datetime.now().timestamp() - 7 * 24 * 60 * 60)
        assert abs(result - expected) < 2


class TestFormatArticleList:
    def test_format_article_list_empty(self):
        result = format_article_list([])
        assert result == "No articles found."

    def test_format_article_list_with_articles(self):
        articles = [
            {
                "title": "Article 1",
                "feed_title": "Feed 1",
                "published_date": "2024-01-01",
                "url": "https://example.com/1",
                "is_read": False,
            }
        ]
        result = format_article_list(articles)
        assert "Article 1" in result
        assert "Feed 1" in result
        assert "https://example.com/1" in result


class TestFormatFeedList:
    def test_format_feed_list_empty(self):
        result = format_feed_list([])
        assert result == "No feeds found."

    def test_format_feed_list_with_feeds(self):
        feeds = [{"title": "Feed 1", "url": "https://example.com", "categories": ["Tech"]}]
        result = format_feed_list(feeds)
        assert "Feed 1" in result
        assert "Tech" in result


class TestExtractItemIds:
    def test_extract_item_ids(self):
        articles = [{"id": "1"}, {"id": "2"}, {"title": "No ID"}]
        result = extract_item_ids(articles)
        assert result == ["1", "2"]


class TestChunkList:
    def test_chunk_list_basic(self):
        result = chunk_list([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_list_empty(self):
        result = chunk_list([], 2)
        assert result == []

    def test_chunk_list_larger_chunk(self):
        result = chunk_list([1, 2, 3], 5)
        assert result == [[1, 2, 3]]
