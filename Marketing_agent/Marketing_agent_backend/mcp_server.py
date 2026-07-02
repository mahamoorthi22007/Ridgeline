"""
MCP server — exposes the Qdrant memory layer as a standard tool that any
MCP-compatible agent (including our ADK ContentGenerator agent) can call.

This runs as a subprocess over stdio, launched automatically by the ADK
McpToolset — you don't need to start it separately.
"""

from mcp.server.fastmcp import FastMCP
import memory

mcp = FastMCP("campaign-memory")


@mcp.tool()
def search_past_campaigns(query: str, content_type: str = "") -> str:
    """Search past generated campaign content for similar tone/style examples.

    Args:
        query: What kind of content you're about to write, e.g. "Instagram
            poster caption for a college hackathon about sustainability".
        content_type: Optional filter — one of "instagram_poster",
            "whatsapp_message", "email", "linkedin_post", "tagline". Leave
            blank to search across all types.

    Returns:
        A formatted list of similar past examples, or a message saying
        none were found (which is normal and expected the first few times
        this pipeline runs, before any memory has built up).
    """
    results = memory.search_similar(
        query_text=query,
        content_type=content_type or None,
        limit=3,
    )
    if not results:
        return "No similar past campaigns found in memory yet. Write fresh content."

    lines = ["Similar past campaigns found:"]
    for r in results:
        lines.append(f"- [{r['content_type']}] from '{r['campaign_name']}': {r['text'][:200]}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
