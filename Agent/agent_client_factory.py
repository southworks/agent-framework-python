# Agent client factory for Azure OpenAI
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIChatClient, AzureOpenAIResponsesClient

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
