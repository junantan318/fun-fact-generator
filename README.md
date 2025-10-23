# fun-fact-generator
**Live Demo:** [View the app here](https://production.d12ioa7e1u5w1x.amplifyapp.com)
Fun-Fact Generator is a cloud-based web application built with AWS serverless services—Lambda, API Gateway, Amplify, DynamoDB, and Amazon Bedrock. It generates witty cloud-themed fun facts on demand.

The goal is to practice AWS architecture and service integration end-to-end. This implementation started as a learning project and was extended to handle region-specific Bedrock model/version differences (e.g., Claude model IDs and response formats) by adding small adaptations in the Lambda layer.

## Features
- Serverless backend (API Gateway + Lambda) with DynamoDB persistence
- Frontend hosted on AWS Amplify
- Fun facts transformed by Amazon Bedrock (Claude)

## Tech Stack
AWS: Amplify, API Gateway (HTTP), Lambda (Python), DynamoDB, Bedrock (Claude)  
Frontend: HTML 

<img width="1336" height="606" alt="funfact drawio" src="https://github.com/user-attachments/assets/07c5d0bb-7c7c-4d31-93d1-e39a3be76c20" />

The user utilize AWS amplify to host the frontend side of the application and deployment of it. The user then clicks on the 'generate fun fact' button to trigger an api call through api gateway. Once api
gateway receives the call , it triggers the event hosted by aws lambda. Lambda function fetches the data from dynamo DB. Lambda also fetches from bedrock (claude AI) to transform the fun fact fetched from
dynamo DB. Bedrock returns a witty fun fact and amplify displays it all.

<img width="1858" height="968" alt="image" src="https://github.com/user-attachments/assets/fcadf675-1e20-4eb9-9c11-823593dc66b3" />
an example of the page on standby

<img width="1851" height="959" alt="image" src="https://github.com/user-attachments/assets/a4d91ad0-5f2f-4bcb-a0dd-f46d9b2c701f" />
once the event has been triggered , a random data from dynamo DB will be pulled and bedrock will transform it into a witty fun fact.

## Quick Start
1. **Backend**
   - Create a DynamoDB table (PK: `id`) and seed it with simple facts.
   - Create a Lambda function with env vars above; add Bedrock Invoke permissions.
   - Create an HTTP API in API Gateway with a `POST /funfact` route -> Lambda integration.
2. **Frontend**
   - Set `API_BASE_URL` in your frontend config.
   - Build and deploy via **Amplify Hosting** (connect repo or manual deploy).
3. **Try it**
   - Open the app and click **Generate Fun Fact**.

