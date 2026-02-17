"""Inoreader MCP Tools - FastMCP tool implementations."""

from fastmcp import Context

from .client import InoreaderClient
from .server import mcp
from .utils import (
    chunk_list,
    days_to_timestamp,
    format_article_list,
    format_feed_list,
    parse_article,
    parse_feed,
)


@mcp.tool()
async def list_feeds(ctx: Context) -> str:
    """List all subscribed feeds in Inoreader."""
    try:
        async with InoreaderClient() as client:
            subscriptions = await client.get_subscription_list()
            feeds = [parse_feed(sub) for sub in subscriptions]

            if not feeds:
                return "No feeds found in your Inoreader account."

            feeds.sort(key=lambda x: x["title"].lower())

            result = f"Found {len(feeds)} feeds:\n\n"
            result += format_feed_list(feeds)

            return result
    except Exception as e:
        return f"Error listing feeds: {str(e)}"


@mcp.tool()
async def list_articles(
    ctx: Context,
    limit: int = 20,
    days: int = 7,
    feed_id: str | None = None,
    unread_only: bool = True,
) -> str:
    """List recent articles with optional filters.

    Args:
        limit: Number of articles to return (default: 20)
        days: Articles from last N days (default: 7)
        feed_id: Optional feed ID to filter articles
        unread_only: Only show unread articles (default: True)
    """
    try:
        async with InoreaderClient() as client:
            newer_than = days_to_timestamp(days) if days else None

            stream_contents = await client.get_stream_contents(
                stream_id=feed_id,
                count=limit,
                exclude_read=unread_only,
                newer_than=newer_than,
            )

            if isinstance(stream_contents, str):
                return "Error: API returned unexpected response format"

            items = stream_contents.get("items", [])
            articles = [parse_article(item) for item in items]

            if not articles:
                filters = []
                if unread_only:
                    filters.append("unread")
                if days:
                    filters.append(f"from the last {days} days")
                if feed_id:
                    filters.append(f"in feed {feed_id}")

                filter_str = " ".join(filters) if filters else ""
                return f"No articles found{' ' + filter_str if filter_str else ''}."

            result = f"Found {len(articles)} articles"
            if unread_only:
                result += " (unread only)"
            if days:
                result += f" from the last {days} days"
            result += ":\n\n"

            result += format_article_list(articles)

            return result
    except Exception as e:
        return f"Error listing articles: {str(e)}"


@mcp.tool()
async def search_articles(
    ctx: Context,
    query: str,
    limit: int = 50,
    days: int | None = 7,
) -> str:
    """Search for articles by keyword.

    Args:
        query: Search query
        limit: Number of articles to return (default: 50)
        days: Search within the last N days (default: 7)
    """
    try:
        async with InoreaderClient() as client:
            newer_than = days_to_timestamp(days) if days else None

            result = await client.search(query=query, count=limit, newer_than=newer_than)

            items = result.get("items", [])
            articles = [parse_article(item) for item in items]

            if not articles:
                return f"No articles found matching '{query}'"

            response = f"Found {len(articles)} articles matching '{query}'"
            if days:
                response += f" from the last {days} days"
            response += ":\n\n"

            response += format_article_list(articles)

            return response
    except Exception as e:
        return f"Error searching articles: {str(e)}"


@mcp.tool()
async def get_content(ctx: Context, article_id: str) -> str:
    """Get full content of a specific article.

    Args:
        article_id: Article ID to get content for
    """
    try:
        async with InoreaderClient() as client:
            result = await client.get_stream_item_contents([article_id])
            items = result.get("items", [])

            if not items:
                return f"Article with ID {article_id} not found."

            item = items[0]
            article = parse_article(item)

            content = f"**{article['title']}**\n"
            content += f"Author: {article['author']}\n"
            content += f"Feed: {article['feed_title']}\n"
            content += f"Date: {article['published_date']}\n"

            if article["url"]:
                content += f"Link: {article['url']}\n"
            else:
                content += "Link: No URL available\n"

            content += f"Status: {'Read' if article['is_read'] else 'Unread'}\n"

            if "content" in item:
                full_content = item["content"].get("content", "")
                if full_content:
                    content += f"\n---\n\n{full_content}"
            elif article["summary"]:
                content += f"\n---\n\n{article['summary']}"
            else:
                content += "\n---\n\nNo content available for this article."

            return content
    except Exception as e:
        return f"Error getting article content: {str(e)}"


@mcp.tool()
async def mark_as_read(ctx: Context, article_ids: list[str]) -> str:
    """Mark articles as read.

    Args:
        article_ids: List of article IDs to mark as read
    """
    try:
        if not article_ids:
            return "No article IDs provided."

        async with InoreaderClient() as client:
            chunks = chunk_list(article_ids, 20)
            success_count = 0

            for chunk in chunks:
                success = await client.mark_as_read(chunk)
                if success:
                    success_count += len(chunk)

            if success_count == len(article_ids):
                return f"Successfully marked {success_count} article(s) as read."
            elif success_count > 0:
                return f"Marked {success_count} out of {len(article_ids)} articles as read."
            else:
                return "Failed to mark articles as read."
    except Exception as e:
        return f"Error marking articles as read: {str(e)}"


@mcp.tool()
async def get_stats(ctx: Context) -> str:
    """Get statistics about unread articles."""
    try:
        async with InoreaderClient() as client:
            unread_counts = await client.get_unread_count()

            total_unread = 0
            feed_stats = []

            for item in unread_counts:
                count = item.get("count", 0)
                if count > 0 and item.get("id", "").startswith("feed/"):
                    total_unread += count
                    feed_stats.append({"id": item["id"], "count": count})

            result = "**Inoreader Statistics:**\n\n"
            result += f"Total unread articles: {total_unread}\n\n"

            if feed_stats:
                feed_stats.sort(key=lambda x: x["count"], reverse=True)

                result += "Top feeds with unread articles:\n"
                for stat in feed_stats[:10]:
                    feed_name = stat["id"].replace("feed/", "")
                    if "://" in feed_name:
                        feed_name = feed_name.split("://")[-1]
                    result += f"- {feed_name}: {stat['count']} unread\n"

            return result
    except Exception as e:
        return f"Error getting stats: {str(e)}"
