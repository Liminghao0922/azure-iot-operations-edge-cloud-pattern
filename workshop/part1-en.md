# Workshop Part 1: Core Deployment

## 🎯 Learning Goals

By the end of this part, you will:

- [ ] Understand the solution architecture
- [ ] Prepare the development environment
- [ ] Deploy the infrastructure
- [ ] Configure core services

## ⏱ Estimated Time: 3 hours

## 📋 Prerequisites

- **Azure subscription**
  - If you do not have one, create a [free Azure account](https://azure.microsoft.com/free/) (12 months free services + $200 credit)
  - Required permissions: for faster deployment, use **Owner** on the subscription; minimum permissions see [Azure IoT Operations required permissions](https://learn.microsoft.com/azure/iot-operations/deploy-iot-ops/overview-deploy#required-permissions)
- Basic Kubernetes knowledge

> **💡 Note**
> This guide uses WSL2 (Ubuntu). If you already have an Ubuntu environment, you can skip the "Install and configure WSL2" and "Install Ubuntu" steps in Step 1.
> For supported environments, see [Azure IoT Operations supported environments](https://learn.microsoft.com/azure/iot-operations/deploy-iot-ops/overview-deploy#supported-environments)

## 🚀 Steps

### Step 1: Environment Setup (30 minutes)

1. Install and configure WSL2

- Update WSL2 to the latest version
- Check the WSL2 version

```powershell
wsl --update
wsl --version
```

2. Ensure DNS Tuning is enabled

- Enable DNS Tuning as recommended by WSL2 to improve DNS query performance
- Open Settings and follow these steps:

> 💡 **Steps**:
>
> - Settings → System → WSL Settings
> - Enable DNS Tuning
>   ![DNS Tuning settings screenshot](image/dns-tuning-settings.png)

3. Install Ubuntu

```powershell
wsl --install Ubuntu
```

![Ubuntu installation](image/ubuntu-installation.png)

4. Install required tools

- Install Azure CLI
  ```bash
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
  ```
- Install the connectedk8s extension
  ```bash
  az extension add --upgrade --name connectedk8s
  ```
- kubectl (installed automatically with K3s)
- Helm
  ```bash
  sudo apt-get install curl gpg apt-transport-https --yes
  curl -fsSL https://packages.buildkite.com/helm-linux/helm-debian/gpgkey | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
  echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
  sudo apt-get update
  sudo apt-get install helm
  ```

### Step 2: Create and Configure Kubernetes Cluster (30 minutes)

1. Create a K3s cluster

```bash
curl -sfL https://get.k3s.io | sh -
```

2. Configure kubectl access

```bash
mkdir ~/.kube
sudo KUBECONFIG=~/.kube/config:/etc/rancher/k3s/k3s.yaml kubectl config view --flatten > ~/.kube/merged
mv ~/.kube/merged ~/.kube/config
chmod 0600 ~/.kube/config
export KUBECONFIG=~/.kube/config
kubectl config use-context default
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
```

3. Verify kubectl installation

```bash
kubectl version --client
```

4. Optimize system parameters

- Increase inotify limits
  ```bash
  echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
  echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
  sudo sysctl -p
  ```
- Increase file descriptor limit
  ```bash
  echo fs.file-max = 100000 | sudo tee -a /etc/sysctl.conf
  sudo sysctl -p
  ```

5. Check cluster status

```bash
kubectl get pods --all-namespaces
```

Expected: Pods in kube-system are Running or Completed.
![Kubernetes Pod status](image/cluster-pods-status.png)

6. Create a project folder, clone the GitHub repo, and open in VS Code

```bash
cd ~
mkdir projects
git clone https://github.com/Liminghao0922/azure-iot-operations-edge-cloud-pattern
cd azure-iot-operations-edge-cloud-pattern/
code .
```

- VS Code Python extension: [Python - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- VS Code Kubernetes extension: [Kubernetes - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools) (optional but recommended)

After installation, a Kubernetes icon appears in the VS Code sidebar. You can view cluster resources there.
![VS Code Kubernetes extension](image/vscode-kubernetes-extension.png)

### Step 3: Enable Azure Arc (30 minutes)

1. Sign in to Azure

   ```
   az login
   ```
2. Register Azure resource providers (once per subscription)

```bash
az provider register -n "Microsoft.ExtendedLocation"
az provider register -n "Microsoft.Kubernetes"
az provider register -n "Microsoft.KubernetesConfiguration"
az provider register -n "Microsoft.IoTOperations"
az provider register -n "Microsoft.DeviceRegistry"
az provider register -n "Microsoft.SecretSyncController"
```

3. Create a resource group

```bash
az group create --location japaneast --name rg-demo-aio
```

Expected: JSON response confirming creation.

4. Arc-enable the cluster

```bash
az connectedk8s connect \
  --name aiocluster \
  -l eastus \
  --resource-group rg-demo-aio\
  --enable-oidc-issuer \
  --enable-workload-identity \
  --disable-auto-upgrade
```

Expected: command completes successfully (may take several minutes).

5. Verify Arc agents

```bash
kubectl get deployments,pods -n azure-arc
```

All Pods should be Running.
![Azure Arc agents status](image/arc-agents-verification.png)

6. Get the OIDC Issuer URL

```bash
az connectedk8s show \
  --resource-group rg-demo-aio\
  --name aiocluster \
  --query oidcIssuerProfile.issuerUrl \
  --output tsv
```

Save this URL for later steps.

7. Configure the K3s API server

```bash
sudo nano /etc/rancher/k3s/config.yaml
```

Add the following (replace <SERVICE_ACCOUNT_ISSUER> with the URL from the previous step):

```
kube-apiserver-arg:
  - service-account-issuer=<SERVICE_ACCOUNT_ISSUER>
  - service-account-max-token-expiration=24h
```

Save and exit (Ctrl+X, Y, Enter).

8. Enable custom locations

```bash
export OBJECT_ID=$(az ad sp show --id bc313c14-388c-4e7d-a58e-70017303ee3b --query id -o tsv)
az connectedk8s enable-features \
  -n aiocluster \
  -g rg-demo-aio \
  --custom-locations-oid $OBJECT_ID \
  --features cluster-connect custom-locations
```

Restart K3s:

```bash
sudo systemctl restart k3s
```

Wait 1-2 minutes.

### Step 4: Deploy Azure IoT Operations from Azure Portal (30 minutes)

1. Create an IoT Operations instance in Azure portal

- Go to [Azure Portal](https://portal.azure.com/)
- Search for Azure IoT Operations
- Select Create

2. Basics tab

   | Parameter               | Value        |
   | ----------------------- | ------------ |
   | Subscription            | Your choice  |
   | Resource group          | rg-demo-aio  |
   | Cluster name            | aiocluster   |
   | Custom location name    | Default/custom |
   | Deployment version      | 1.2 (latest) |
   | Click Next: Configuration |            |

   ![Basics](image/basics-configuration.png)
3. Configuration tab

   | Parameter                       | Notes       |
   | ------------------------------ | ----------- |
   | Azure IoT Operations name      | Default/custom |
   | MQTT broker configuration      | Default (test) |
   | Data flow profile configuration| Default (test) |
   | Click Next: Dependency management |          |

   ![Configuration](image/configuration-settings.png)
4. Dependency management - Schema Registry

- Select Create new
- Provide name and namespace
- Select/create storage account and container
  ![Schema Registry create](image/schema-registry-create.png)
  ![Schema Registry container](image/schema-registry-container.png)
- Click Apply
  ![Schema Registry apply](image/schema-registry-apply.png)

5. Dependency management - Device Registry

- Select Create new
- Fill in basic info (subscription, resource group, name, region)
- Complete creation and select the new namespace
  ![Device Registry create](image/device-registry-create.png)

6. Security settings

- Choose **Secure settings** deployment option
- **Key Vault configuration**

  - Select an existing Key Vault or create a new one
  - Ensure Key Vault has RBAC enabled and assign `Key Vault Secrets Officer` to the deployment user
    ![Key Vault security config](image/keyvault-configuration.png)
- **Managed Identity configuration**

  - Create a managed identity for secret sync
    ![Managed Identity key sync](image/managed-identity-key-sync.png)
  - Create a managed identity for cloud link
    ![Managed Identity cloud link](image/managed-identity-cloud-link.png)
- Click **Automation >**
  ![Automation tab](image/automation-tab.png)

> **💡 Tips**:
>
> - Secure settings are strongly recommended for production
> - Use Managed Identity to avoid hard-coded credentials
> - Enable soft delete and purge protection in Key Vault
> - See [Enable secure settings in Azure IoT Operations](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/howto-enable-secure-settings?tabs=bash)

### Step 5: Run Deployment Commands (30-60 minutes)

1. Copy and run the Azure CLI commands from the portal Automation tab
   ![Automation init command](image/automation-init-command.png)
2. Run the commands in order:

- Interactive Azure sign-in

  ```bash
  az login
  ```
- Install Azure IoT Operations CLI extension

  ```bash
  az extension add --upgrade --name azure-iot-ops
  ```
- Create schema registry. The auto-generated script may omit location, so set `--location eastus` explicitly.

  ```bash
  az iot ops schema registry create  \
   --subscription <subscription-id>  \
   -g rg-demo-aio  \
   -n my-iot-reg  \
   --registry-namespace my-iot-reg-ns  \
   --sa-resource-id /subscriptions/<subscription-id>/resourceGroups/rg-demo-aio/providers/Microsoft.Storage/storageAccounts/saiot   \
   --sa-container iotconfig  \
   --location eastus
  ```
- Initialize the cluster (10+ minutes) # copy portal command `az iot ops init`
- Deploy Azure IoT Operations (30 minutes) # copy portal command `az iot ops create`
  ![Automation deploy command](image/automation-create-command.png)
- Enable secret sync # copy portal command `az iot ops secretsync enable`
- For long-running commands, monitor progress in the terminal

3. Wait for all commands to finish, then close the portal wizard

### Step 6: Verify Deployment (10 minutes)

1. Check deployment health

```bash
az iot ops check
```

Expected:
![IoT Operations health check](image/health-check-result.png)
2. Check broker health details

```bash
az iot ops check --svc broker --detail-level 1
```

3. Access Operations UI

- Open [IoT Operations UI](https://iotoperations.azure.com/)
- Sign in with Microsoft Entra ID
- Check the unassigned instance to confirm the cluster is created

## ✅ Verification Checklist

- [ ] Cluster is running
- [ ] All Pods are Running
- [ ] Services have IP addresses
- [ ] Health endpoints are reachable
- [ ] Logs are collected
- [ ] Metrics are collected

## 🔗 Resources

- [Azure IoT Operations docs](https://learn.microsoft.com/en-us/azure/iot-operations/)
- [Kubernetes install guide](https://kubernetes.io/docs/)
- [K3s docs](https://docs.k3s.io/)
- [Azure Arc docs](https://learn.microsoft.com/en-us/azure/azure-arc/)
- [Azure CLI reference](https://learn.microsoft.com/en-us/cli/azure/)

## 🆘 Common Issues

**Issue: Device must be managed to access resources**

- Fix: run `az login` again and ensure browser-based interactive sign-in

**Issue: kubectl cannot access the cluster**

- Fix: make sure the environment variable is set
  ```bash
  export KUBECONFIG=~/.kube/config
  ```

**Issue: Arc connection fails**

- Fix:
  1. Check Azure account permissions (Owner or Contributor + User Access Administrator)
  2. Confirm resource providers are registered
  3. Check network connectivity

**Issue: Deployment command times out**

- Fix: the command can take 10-15 minutes; if it fails, run `az iot ops check` to verify status

---

## Estimated Total Time

- Environment setup (Step 1): 30 minutes
- Kubernetes cluster creation (Step 2): 30 minutes
- Azure Arc enablement (Step 3): 30 minutes
- Portal deployment (Step 4): 30 minutes
- Run deployment commands (Step 5): 30-60 minutes
- Verification (Step 6): 10 minutes

**Total: about 3 hours**

---

## 🎉 Part 1 Completed! Next Step

Congratulations! You have finished Part 1. Continue with [Part 2: MQTT and Data Flow Configuration](./part2-en.md)

---

**Last updated**: March 4, 2026
