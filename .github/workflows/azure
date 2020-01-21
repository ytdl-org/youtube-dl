# This workflow will build and push a node.js application to an Azure Web App on every push to the master branch.
#
# To configure this workflow:
#
# 1. Set up a secret in your repository named AZURE_WEBAPP_PUBLISH_PROFILE with the value of your Azure publish profile.
#
# 2. Change the values for the AZURE_WEBAPP_NAME, AZURE_WEBAPP_PACKAGE_PATH and NODE_VERSION environment variables  (below).
#
# For more information on GitHub Actions for Azure, refer to https://github.com/Azure/Actions
# For more samples to get started with GitHub Action workflows to deploy to Azure, refer to https://github.com/Azure/actions-workflow-samples
on:
  push:
    branches:
      - master

env:
  AZURE_WEBAPP_NAME: your-app-name    # set this to your application's name
  AZURE_WEBAPP_PACKAGE_PATH: '.'      # set this to the path to your web app project, defaults to the repository root
  NODE_VERSION: '10.x'                # set this to the node version to use

jobs:
  build-and-deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@master
    - name: Use Node.js ${{ env.NODE_VERSION }}
      uses: actions/setup-node@v1
      with:
        node-version: ${{ env.NODE_VERSION }}
    - name: npm install, build, and test
      run: |
        # Build and test the project, then
        # deploy to Azure Web App.
        npm install
        npm run build --if-present
        npm run test --if-present
    - name: 'Deploy to Azure WebApp'
      uses: azure/webapps-deploy@v1
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: ${{ env.AZURE_WEBAPP_PACKAGE_PATH }}
