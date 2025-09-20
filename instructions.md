I need to build a client that hosts an AI agent that's capable of interacting with the computer with tools. here's what it needs to do:

It needs to maintain multiple strings of AI agent state. State can be extremely complex. We should just assume that they're arbitrary Python objects.

However, note that tools can use both global state and per-conversation state. tools should have full control over this. they should be passed some objects that allow them to store arbitrary state globally and per-conversation. State should be persisted by the client between client restarts, but there should be a command-line option that lets me entirely reset state.

The server monitors prompts sent over websockets. You can see details for the server in @evanai-server/SERVER-SPEC.md . Prompts sent from the server should have the following format:

{
  "recipient": "agent",
  "type": "new_prompt",
  "payload": {
    "conversation_id": "uuid_string",
    "prompt": "prompt\nprompt\n"
  }
}

If the "conversation_id" is a new conversation_id, then the agent client should create a new conversation.

Okay. tools in this client should work as easy plug-play plugins. the client should have a folder of ToolSetProviders. a ToolSetProvider should be a protocol (in the Swift sense, even though the client itself should be written in Python). a ToolSetProvider has:

- an `init()` function, which lets it return: [list of tools, global state, per-conversation state]. Every tool has:

ID: an ID for the tool that uniquely identifies it
Description: a description for the tool. this will be read by the model
Parameters: A dictionary of parameters. Parameters can be nested arbitrarily deeply. Every parameter object should include a type (including whether it's optional), a name, default values (optional), and a description. parameters are JSON objects.
Returns: Similar to parameters, JSON schema that describes the return type.

per-conversation state should be standardized as a map mapping from conversation IDs to data. Though tools can technically violate the contract this way by mixing per-conversation state, that should be the ToolSetProvider's fault.

- a `callTool(toolID, toolParameters, perConversationState, GlobalState)` function. the client calls this function when the model uses a tool. `callTool` should return a tuple: (return type, error), return type is specified by the tool. if the error is not null, then return type should be ignored, the agent should be terminated, and the error should be dumped out. any error is regarded as a critical runtime error.

Tool calls should be validated by the client, not by the tool providers themselves. Similarly, the client should handle converting the tool call's outputted spec to whatever spec the LLM needs, not the ToolSetProvider. If tool call validations fail, the client should send a generic error back to Claude. something along the lines of "Error: Tool call `get_weather` expected parameter `city`, got `null`"

The LLM that we will be using for this is Claude. feel free to access Anthropic's API docs for Claude's API. The tools should be provided in the format specified by Anthropic's API docs. 

We won't be including any tools here for now, though first add a random, say, weather tool that takes in a location and just outputs some result as a means of testing the system.

The agent client should report all completions by claude via this format:

{
  "recipient": "user_device",
  "type": "agent_response",
  "payload": {
    "conversation_id": "uuid_string",
    "prompt": "Claude completion here"
  }
}