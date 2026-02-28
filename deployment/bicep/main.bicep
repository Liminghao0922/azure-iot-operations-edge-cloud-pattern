// Azure IoT Operations Bicep Deployment Template
// Deploys core Azure resources for IoT Operations
// Based on architecture steps in hands-on guide

param location string = 'eastus'
param resourceGroupPrefix string = 'rg-aio'
param environment string = 'dev'
param clusterName string = 'aiocluster'

// Unique suffix for resource names
param uniqueSuffix string = uniqueString(resourceGroup().id)

// Resource naming
var prefix = '${resourceGroupPrefix}-${environment}'
var deviceRegistryName = '${prefix}-registry-${uniqueSuffix}'
var schemaRegistryName = '${prefix}-schema-${uniqueSuffix}'
var storageAccountName = replace('${prefix}storage${uniqueSuffix}', '-', '')
var eventHubNamespaceName = '${prefix}-eventhub-${uniqueSuffix}'
var eventHubName = 'aio-events'
var keyVaultName = '${prefix}-kv-${uniqueSuffix}'

// Tags for all resources
var commonTags = {
  environment: environment
  project: 'AzureIoTOperations'
  createdBy: 'bicep'
  createdDate: utcNow('u')
}

// ==================== Storage Account ====================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    isHnsEnabled: true  // Enable hierarchical namespace for Data Lake
  }
  tags: commonTags
}

// Create container for Schema Registry
resource schemaContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/schema-registry'
  properties: {
    publicAccess: 'None'
  }
}

// ==================== Event Hub Namespace ====================
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2022-10-01-preview' = {
  name: eventHubNamespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: 1
  }
  properties: {
    isAutoInflateEnabled: true
    maximumThroughputUnits: 20
    kafkaEnabled: false
    zoneRedundant: false
  }
  tags: commonTags

  // Event Hub instance
  resource eventHub 'eventhubs@2022-10-01-preview' = {
    name: eventHubName
    properties: {
      messageRetentionInDays: 1
      partitionCount: 2
      status: 'Active'
    }

    // Shared Access Policy for Event Hub
    resource sendListenPolicy 'authorizationRules@2022-10-01-preview' = {
      name: 'SendListen'
      properties: {
        rights: [
          'Send'
          'Listen'
        ]
      }
    }
  }
}

// ==================== Device Registry ====================
resource deviceRegistry 'Microsoft.DeviceRegistry/registries@2023-03-15-preview' = {
  name: deviceRegistryName
  location: location
  properties: {}
  tags: commonTags
}

// ==================== Key Vault ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
  }
  tags: commonTags

  // Store Event Hub connection string as secret
  resource eventHubConnectionSecret 'secrets@2023-02-01' = {
    name: 'event-hub-connection-string'
    properties: {
      value: listKeys('${eventHubNamespace::eventHub::sendListenPolicy.id}', '2022-10-01-preview').primaryConnectionString
    }
  }

  // Store storage account connection string
  resource storageConnectionSecret 'secrets@2023-02-01' = {
    name: 'storage-account-connection-string'
    properties: {
      value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, '2023-01-01').keys[0].value};EndpointSuffix=core.chinacloudapi.cn'
    }
  }
}

// ==================== Diagnostic Settings ====================
resource storageAccountDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${storageAccount.name}-diagnostics'
  scope: storageAccount
  properties: {
    workspaceId: ''  // Set to Log Analytics workspace if available
    metrics: [
      {
        category: 'Transaction'
        enabled: true
      }
    ]
  }
}

resource eventHubDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${eventHubNamespace.name}-diagnostics'
  scope: eventHubNamespace
  properties: {
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
    logs: [
      {
        category: 'OperationalLogs'
        enabled: true
      }
    ]
  }
}

// ==================== Output ====================
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output storageContainerName string = 'schema-registry'

output eventHubNamespaceName string = eventHubNamespace.name
output eventHubName string = eventHubName
output eventHubNamespaceId string = eventHubNamespace.id
output eventHubConnectionStringKeyName string = 'event-hub-connection-string'

output deviceRegistryName string = deviceRegistry.name
output deviceRegistryId string = deviceRegistry.id

output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id

output deploymentSummary object = {
  region: location
  environment: environment
  resourcePrefix: prefix
  createdResources: {
    storageAccount: storageAccount.name
    eventHubNamespace: eventHubNamespace.name
    eventHub: eventHubName
    deviceRegistry: deviceRegistry.name
    keyVault: keyVault.name
  }
  nextSteps: [
    'Update connection strings in Key Vault'
    'Configure Arc-enabled cluster'
    'Deploy Azure IoT Operations via portal'
    'Configure MQTT Broker listener'
    'Create data flows'
  ]
}
