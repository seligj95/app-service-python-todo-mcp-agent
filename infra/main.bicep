targetScope = 'resourceGroup'

@description('Name of the environment')
param environmentName string

@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Secret key for Flask application')
@secure()
param secretKey string = ''

// Generate unique resource token
var resourceToken = uniqueString(subscription().id, resourceGroup().id, location, environmentName)

// Define resource prefix
var resourcePrefix = 'tda'

// App Service Plan name
var appServicePlanName = 'az-${resourcePrefix}-plan-${resourceToken}'

// App Service name  
var appServiceName = 'az-${resourcePrefix}-app-${resourceToken}'

// Azure AI Hub name
var aiHubName = 'az-${resourcePrefix}-hub-${resourceToken}'

// Azure AI Project name
var aiProjectName = 'az-${resourcePrefix}-project-${resourceToken}'

// Azure OpenAI account name
var openAIAccountName = 'az-${resourcePrefix}-openai-${resourceToken}'

// Storage account name (required for AI Hub)
var storageAccountName = 'az${resourcePrefix}st${take(resourceToken, 8)}'

// Key Vault name (required for AI Hub)
var keyVaultName = 'az-${resourcePrefix}-kv-${take(resourceToken, 8)}'

// Create App Service Plan (P0V3 Linux)
resource appServicePlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: appServicePlanName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  sku: {
    name: 'P0v3'
    tier: 'Premium0V3'
    size: 'P0v3'
    family: 'Pv3'
    capacity: 1
  }
  properties: {
    reserved: true // Linux App Service Plan
  }
  kind: 'linux'
}

// Create App Service
resource appService 'Microsoft.Web/sites@2024-04-01' = {
  name: appServiceName
  location: location
  tags: {
    'azd-env-name': environmentName
    'azd-service-name': 'todo-app'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
      appCommandLine: 'python -m uvicorn main:app --host 0.0.0.0 --port 8000'
      appSettings: [
        {
          name: 'SECRET_KEY'
          value: secretKey
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAIAccount.properties.endpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: gpt41MiniDeployment.name
        }
        {
          name: 'AZURE_AI_PROJECT_ENDPOINT'
          value: 'https://${aiProject.properties.discoveryUrl}'
        }
        {
          name: 'AZURE_APP_SERVICE_URL'
          value: 'https://${appServiceName}.azurewebsites.net'
        }
      ]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
      healthCheckPath: '/health'
    }
  }
}

// Create Storage Account (required for AI Hub)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

// Create Key Vault (required for AI Hub)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    accessPolicies: []
  }
}

// Create Azure OpenAI Account
resource openAIAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAIAccountName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openAIAccountName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

// Create GPT-4.1-mini deployment
resource gpt41MiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAIAccount
  name: 'gpt-4-1-mini'
  sku: {
    name: 'GlobalStandard'
    capacity: 150
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

// Create Azure AI Hub (workspace)
resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiHubName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
  }
  kind: 'Hub'
  properties: {
    friendlyName: 'Todo MCP AI Hub'
    description: 'AI Hub for Todo MCP Agent chat functionality'
    keyVault: keyVault.id
    storageAccount: storageAccount.id
    hbiWorkspace: false
    publicNetworkAccess: 'Enabled'
  }
}

// Create Azure AI Project
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiProjectName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
  }
  kind: 'Project'
  properties: {
    friendlyName: 'Todo MCP AI Project'
    description: 'AI Project for Todo MCP Agent chat functionality'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
}

// Create AI Hub connection to Azure OpenAI
resource aiHubOpenAIConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-10-01' = {
  parent: aiHub
  name: 'openai-connection'
  properties: {
    authType: 'AAD'
    category: 'AzureOpenAI'
    target: openAIAccount.properties.endpoint
    metadata: {
      ApiType: 'Azure'
      ResourceId: openAIAccount.id
    }
  }
}

// Grant App Service access to OpenAI
resource appServiceOpenAIRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, appService.id, openAIAccount.id, 'CognitiveServicesOpenAIUser')
  scope: openAIAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant App Service access to AI Project
resource appServiceAIProjectRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, appService.id, aiProject.id, 'AzureMLDataScientist')
  scope: aiProject
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f6c7c914-8db3-469d-8ca1-694a8f32e121') // AzureML Data Scientist
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant AI Hub access to OpenAI (for Azure AI Foundry integration)
resource aiHubOpenAIRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, aiHub.id, openAIAccount.id, 'CognitiveServicesOpenAIContributor')
  scope: openAIAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a001fd3d-188f-4b5d-821b-7da978bf7442') // Cognitive Services OpenAI Contributor
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant AI Project access to OpenAI (for Azure AI Foundry integration)
resource aiProjectOpenAIRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, aiProject.id, openAIAccount.id, 'CognitiveServicesOpenAIContributor')
  scope: openAIAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a001fd3d-188f-4b5d-821b-7da978bf7442') // Cognitive Services OpenAI Contributor
    principalId: aiProject.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output RESOURCE_GROUP_ID string = resourceGroup().id
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output SERVICE_WEB_NAME string = appService.name
output SERVICE_WEB_URI string = 'https://${appService.properties.defaultHostName}'
output SERVICE_TODO_APP_IDENTITY_PRINCIPAL_ID string = appService.identity.principalId
output AZURE_OPENAI_ENDPOINT string = openAIAccount.properties.endpoint
output AZURE_OPENAI_NAME string = openAIAccount.name
output AZURE_AI_PROJECT_ENDPOINT string = 'https://${aiProject.properties.discoveryUrl}'
output AZURE_AI_PROJECT_NAME string = aiProject.name
output AZURE_AI_HUB_NAME string = aiHub.name
output AZURE_OPENAI_DEPLOYMENT_NAME string = gpt41MiniDeployment.name
