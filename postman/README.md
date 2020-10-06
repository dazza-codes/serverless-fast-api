# Postman

This project contains Postman collections. They can be imported into
[Postman](https://www.postman.com/) and/or run with the
[newman](https://github.com/postmanlabs/newman) command line tool. The postman
test suite uses the behavior-driven-design (BDD) language in the
[Chai Assertion Library](https://www.chaijs.com/). There are some
useful docs for a quick-start to coding postman tests in:

- [test-examples](https://learning.postman.com/docs/postman/scripts/test-examples/)
- [variables](https://learning.postman.com/docs/postman/variables-and-environments)

## Dependencies

Install [nodejs](https://nodejs.org/) and
[yarn](https://classic.yarnpkg.com/en/docs/install).

- https://nodejs.org/en/download/
- https://nodejs.org/en/download/package-manager/
- https://classic.yarnpkg.com/en/docs/install

Then install the project dependencies (the `package.json` specifies several
all the dependencies):

```sh
yarn
```

## Running Postman

To run collections in the postman app, import an
environment and a collection into the app from
the `src/collections` directory.

This project uses newman to run collections, based on
configuration files in `src/config/*.json`.  There
are convenient `yarn` commands to help, e.g.

```text
yarn test-app-dev-api
yarn test-app-dev-newman-env
yarn test-app-dev-cognito-auth
```

See the details of the yarn commands in `package.json`.
The `src` directory contains everything required to run
a collection.

The `src/config/*.json` provides settings for creating
postman environments.  The environment variable `NODE_ENV`
is used by the node-config package to read one of these
config files.  The `src/newman_env.js` module uses this
config to dynamically create a postman environment.

The `src/collections` provide the postman collections to
run.  The config file identifies which collection to run
and the `src/newman_run.js` module gathers the postman
environment and the collection to run it.

```text
$ tree src/
src/
├── cognito_auth.js
├── collections
│   └── app-dev.postman_collection.json
├── config
│   ├── app_dev.json
│   └── default.json
├── newman_env.js
├── newman_run.js
└── package.json
```

### AWS SAM

Install [aws-sam](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
to use it for local testing and serverless deployments.  See details
below, but note there are a few `make` recipes to set some default
values for this project.

Note that the `node_modules` installed into the project root are
not exactly the same as those used for the lambda-layer built by aws-sam.
Use `make sam-build` to build the sam packages, because that make
recipe will copy `package.json` into the `layer/package.json` file
so that aws-sam will build a nodejs layer for the serverless app.
The aws-sam artifacts are built into `.aws-sam`.  See also the
other `make` recipes for `sam-*` in the `Makefile`.

## Postman Collections and Configurations

The Postman collections are in the `src/collections` directory.
The `src/config` directory contains various parameters required
to create a postman-environment for a collection and to load
a collection for a newman run.

## Postman with AWS API-Gateway

For API endpoints deployed to AWS API-Gateway (API-GW), the postman tests
require AWS-credentials to get JSON-Web-Tokens [JWT](https://jwt.io/) for authentication.
First, get an invitation to register with the Cognito user pool and
complete the signup process or get the credentials for a service account.

### Environment

To get an AWS-Cognito JWT, update the `src/config/{env}.json` values described below.
Confer with another developer and/or the AWS console to update the cognito
configuration values, if they are not set already using service account
credentials.

### Configuration

The project uses the [node config module](https://github.com/lorenwest/node-config)
for configuration. Hence, check out `default.json` for default config options
and other files for available custom environments.

### Running newman test suite

There is a yarn script for this (see `package.json` for details), try:

```shell script
yarn test-app-dev-api
```

### Import test collection into Postman

In Postman, open the "Import" menu and try to import a "collection" file from
`src/collections/{api}.postman_collection.json` into a new collection;
call it say `app-dev-api`. If that worked, the `app-dev-api` collection will appear
in the left navigation panel of Postman.

In Postman, open the "Import" menu and try to import an "environment" file from
`src/collections/{api}.postman_environment.json` into a new environment; call it say
`app-dev-api`. If that worked, the `app-dev-api` environment can be selected
from the Environment dropdown, in the upper right corner of Postman.

The Postman Runner can run all the tests in the collection;
make sure that the `app-dev-api` is selected in the Runner
and the JWT has not expired.

# AWS-SAM

This project contains source code and supporting files for a serverless
application that you can deploy with the AWS Serverless Application Model
(AWS SAM) command line interface (CLI). It includes the following files and
folders:

- `src` - Code for the application's Lambda function.
- `events` - Invocation events that you can use to invoke the function.
- `__tests__` - Unit tests for the application code.
- `template.yml` - A template that defines the application's AWS resources.

Resources for this project are defined in the `template.yml` file in this
project. You can update the template to add AWS resources through the same
deployment process that updates your application code.

If you prefer to use an integrated development environment (IDE) to build and
test your application, you can use the AWS Toolkit. The AWS Toolkit is an
open-source plugin for popular IDEs that uses the AWS SAM CLI to build and
deploy serverless applications on AWS. The AWS Toolkit also adds step-through
debugging for Lambda function code.

To get started, see the following:

- [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
- [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
- [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
- [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

## Deploy the sample application

The AWS SAM CLI is an extension of the AWS CLI that adds functionality for
building and testing Lambda applications. It uses Docker to run your
functions in an Amazon Linux environment that matches Lambda. It can also
emulate your application's build environment and API.

To use the AWS SAM CLI, you need the following tools:

- AWS SAM CLI - [Install the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html).
- Node.js - [Install Node.js 12](https://nodejs.org/en/), including the npm package management tool.
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community).

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build
sam deploy --guided
```

The first command will build the source of your application. The second
command will package and deploy your application to AWS, with a series of
prompts:

- **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
- **AWS Region**: The AWS region you want to deploy your app to.
- **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
- **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
- **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

## Use the AWS SAM CLI to build and test locally

Build your application by using the `sam build` command.

```bash
my-application$ sam build
```

The AWS SAM CLI installs dependencies that are defined in `package.json`,
creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is
a JSON document that represents the input that the function receives from the
event source. Test events are included in the `events` folder in this
project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
my-application$ sam local invoke ScheduledEventLogger --event events/event-cloudwatch-event.json
```

## Add a resource to your application

The application template uses AWS SAM to define application resources. AWS
SAM is an extension of AWS CloudFormation with a simpler syntax for
configuring common serverless application resources, such as functions,
triggers, and APIs. For resources that aren't included in the
[AWS SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md),
you can use the standard
[AWS CloudFormation resource types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html).

Update `template.yml` to add a dead-letter queue to your application. In the
**Resources** section, add a resource named **MyQueue** with the type
**AWS::SQS::Queue**. Then add a property to the **AWS::Serverless::Function**
resource named **DeadLetterQueue** that targets the queue's Amazon Resource
Name (ARN), and a policy that grants the function permission to access the
queue.

```yaml
Resources:
  MyQueue:
    Type: AWS::SQS::Queue
  ScheduledEventLogger:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/scheduled-event-logger.scheduledEventLogger
      Runtime: nodejs12.x
      DeadLetterQueue:
        Type: SQS
        TargetArn: !GetAtt MyQueue.Arn
      Policies:
        - SQSSendMessagePolicy:
            QueueName: !GetAtt MyQueue.QueueName
```

The dead-letter queue is a location for Lambda to send events that could not
be processed. It's only used if you invoke your function asynchronously, but
it's useful here to show how you can modify your application's resources and
function configuration.

Deploy the updated application.

```bash
my-application$ sam deploy
```

Open the
[**Applications**](https://console.aws.amazon.com/lambda/home#/applications)
page of the Lambda console, and choose your application. When the deployment
completes, view the application resources on the **Overview** tab to see the
new resource. Then, choose the function to see the updated configuration that
specifies the dead-letter queue.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, the AWS SAM CLI has a command called `sam logs`.
`sam logs` lets you fetch logs that are generated by your Lambda function
from the command line. In addition to printing the logs on the terminal, this
command has several nifty features to help you quickly find the bug.

**NOTE:** This command works for all Lambda functions, not just the ones you deploy using AWS SAM.

```bash
my-application$ sam logs -n ScheduledEventLogger --stack-name sam-app --tail
```

**NOTE:** This uses the logical name of the function within the stack. This is
the correct name to use when searching logs inside an AWS Lambda function
within a CloudFormation stack, even if the deployed function name varies due
to CloudFormation's unique resource name generation.

You can find more information and examples about filtering Lambda function
logs in the
[AWS SAM CLI documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Unit tests

Tests are defined in the `__tests__` folder in this project. Use `npm` to
install the [Jest test framework](https://jestjs.io/) and run unit tests.

```bash
my-application$ npm install
my-application$ npm run test
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming
you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name app-dev-postman
```

## Resources

For an introduction to the AWS SAM specification, the AWS SAM CLI, and
serverless application concepts, see the
[AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html).

Next, you can use the AWS Serverless Application Repository to deploy
ready-to-use apps that go beyond Hello World samples and learn how authors
developed their applications. For more information, see the
[AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/) and the
[AWS Serverless Application Repository Developer Guide](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/what-is-serverlessrepo.html).
