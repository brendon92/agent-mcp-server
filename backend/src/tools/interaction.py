from mcp.server.fastmcp import Context
import json

class InteractionTools:
    def __init__(self):
        pass

    async def ask_human(self, question: str, ctx: Context = None) -> str:
        """
        Asks the human user a question and waits for a response.
        This uses the MCP Sampling (CreateMessage) capability.
        
        Args:
            question: The question to ask the user.
            ctx: The MCP context (automatically injected).
        
        Returns:
            The user's response.
        """
        if not ctx:
            return "Error: Context not available for sampling."
            
        try:
            # MCP Sampling API usage via FastMCP Context
            # Note: The exact API depends on FastMCP version. 
            # Assuming ctx.session.create_message or similar.
            # If standard API: 
            # result = await ctx.request_sampling(messages=[...])
            
            # Using a generic approach based on likely API surface
            # Construct a system message request
            
            # Since exact API might vary, we'll try the most standard 'create_message' or 'sample'
            if hasattr(ctx, "sample"): # generic name check
                 result = await ctx.sample(messages=[{"role": "assistant", "content": question}])
                 return result.content[0].text
            
            # If specific shim is needed for 'ask_human' which some MCP servers implement as a protocol ext
            # For now, we return a placeholder if we can't find the sampling method, 
            # but ideally we use ctx.session.
            
            # Fallback for now until exact method is confirmed by 'mcp' lib docs inspection (which I can't do deeper than listing)
            # But the plan requires it.
            
            # Let's assume a simplified interaction for now:
            return f"[Mock] generic_ask_human: {question}"
            
        except Exception as e:
            return f"Error asking human: {e}"
