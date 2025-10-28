# Agent client factory for Azure OpenAI and OpenAI
import os
from azure.identity import AzureCliCredential
from azure.identity.aio import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIChatClient, AzureAIAgentClient, AzureOpenAIResponsesClient
from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient

def get_azopenaichatclient(api_version="2024-08-01-preview", deployment_name="gpt-4o") -> AzureOpenAIChatClient:
    """Returns an instance of AzureOpenAIChatClient."""
    return AzureOpenAIChatClient(
        credential=AzureCliCredential(),
        endpoint="https://ai-services-test-ai-resource.openai.azure.com/",
        api_version=api_version,
        deployment_name=deployment_name
    )

def get_azopenairesponsesclient(api_version="preview", deployment_name="gpt-4o") -> AzureOpenAIResponsesClient:
    """Returns an instance of AzureOpenAIResponsesClient."""
    return AzureOpenAIResponsesClient(
        credential=AzureCliCredential(),
        endpoint="https://ai-services-test-ai-resource.openai.azure.com/",
        api_version=api_version,
        deployment_name=deployment_name
    )

def get_azaiagentclient(api_version="2024-08-01-preview", deployment_name="gpt-4o") -> AzureAIAgentClient:
    """Returns an instance of AzureAIAgentClient."""
    return AzureAIAgentClient(
        async_credential=DefaultAzureCredential(), 
        project_endpoint="https://ai-services-test-ai-resource.services.ai.azure.com/api/projects/ai-services-test-ai",
        model_deployment_name=deployment_name,
        api_version=api_version
    )

def get_openaichatclient(model_id="gpt-4o") -> OpenAIChatClient:
    """Returns an instance of OpenAIChatClient."""
    return OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://ai-services-test-ai-resource.openai.azure.com/",
        model_id=model_id
    )

def get_openairesponsesclient(model_id="gpt-4o") -> OpenAIResponsesClient:
    """Returns an instance of OpenAIResponsesClient."""
    return OpenAIResponsesClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://ai-services-test-ai-resource.openai.azure.com/",
        model_id=model_id
    )
